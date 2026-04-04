import yfinance as yf
from flask import Flask, render_template_string, request, redirect
import requests

app = Flask(__name__)
stored_results = []

def get_ticker_from_any(input_val):
    val = input_val.strip()
    # Wenn es eine 6-stellige WKN ist, suchen wir den Ticker bei Yahoo
    if val.isdigit() and len(val) == 6:
        try:
            # Yahoo Search API nutzen, um den Ticker zur WKN zu finden
            url = f"https://query2.finance.yahoo.com/v1/finance/search?q={val}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers).json()
            if response['quotes']:
                return response['quotes'][0]['symbol']
        except: pass
    
    # Standard-Logik für Ticker
    t = val.upper()
    if len(t) <= 4 and t not in ["META", "AAPL", "MSFT", "NVDA", "TSLA"]:
        return f"{t}.DE"
    return t

def get_signal(rsi):
    if rsi < 35: return "KAUFEN", "#00ff88"
    if rsi > 65: return "VERKAUFEN", "#ff4d4d"
    return "HALTEN", "#ffd700"

def get_market_data(input_val):
    search_t = get_ticker_from_any(input_val)
    try:
        stock = yf.Ticker(search_t)
        df = stock.history(period="65d")
        if df.empty: return None
        
        curr = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((curr / prev_close) - 1) * 100
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2) if loss > 0 else 50
        
        status = "OVER" if curr > sma else "UNDER"
        signal, sig_color = get_signal(rsi)
        
        try:
            kgv = stock.info.get('trailingPE', 'n/a')
            if isinstance(kgv, (int, float)): kgv = round(kgv, 1)
        except: kgv = "n/a"
        
        return {
            'ticker': search_t, 'price': f"{curr:.2f}", 'change': f"{change_pct:+.2f}%",
            'sma38': f"{sma:.2f}", 'kgv': kgv, 'rsi': rsi, 'status': status,
            'signal': signal, 'sig_color': sig_color
        }
    except: return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PRO Terminal V2</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 15px; text-align: center; }
        .container { max-width: 500px; margin: auto; }
        .input-area { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
        input { width: 85%; padding: 15px; background: #222; border: 1px solid #444; color: #fff; border-radius: 10px; margin-bottom: 10px; font-size: 16px; }
        .gold-btn { background: #ffd700; color: #000; padding: 15px; border: none; border-radius: 10px; width: 90%; font-weight: bold; cursor: pointer; }
        .card { background: #161616; padding: 15px; margin-bottom: 10px; border-radius: 12px; border-left: 4px solid #ffd700; display: flex; justify-content: space-between; align-items: center; text-align: left; }
        .sig-badge { padding: 5px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8em; margin-top: 5px; display: inline-block; }
    </style>
    <script>
        function copyData() {
            let cards = document.querySelectorAll('.card');
            let txt = "TERMINAL EXPORT:\\n";
            cards.forEach(c => { txt += c.innerText.replace(/\\n/g, " ") + "\\n"; });
            navigator.clipboard.writeText(txt); alert("Export für KI kopiert!");
        }
    </script>
</head>
<body>
    <div class="container">
        <h2 onclick="copyData()" style="color:#ffd700; cursor:pointer;">PRO TERMINAL 🚀</h2>
        <form class="input-area" action="/stack" method="POST">
            <input type="text" name="symbol" placeholder="WKN (703000) oder Ticker (META)..." required autofocus>
            <button type="submit" class="gold-btn">STAPELN & ANALYSIEREN</button>
        </form>
        {% for s in stocks %}
        <div class="card">
            <div>
                <strong>{{ s.ticker }}</strong> <small style="color:#888;">KGV: {{ s.kgv }}</small><br>
                <span style="font-weight:bold;">{{ s.price }}€ <small style="{{ 'color:#00ff88' if '+' in s.change else 'color:#ff4d4d' }}">({{ s.change }})</small></span><br>
                <div class="sig-badge" style="background:{{ s.sig_color }}; color:#000;">{{ s.signal }}</div>
            </div>
            <div style="text-align: right;">
                <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}; font-weight:bold;">{{ s.status }} SMA38</small><br>
                <small style="color:#777;">RSI: {{ s.rsi }}</small>
            </div>
        </div>
        {% endfor %}
        <br><a href="/clear" style="color:#444; text-decoration:none; font-size:0.8em;">Leeren</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE, stocks=stored_results)

@app.route('/stack', methods=['POST'])
def stack():
    global stored_results
    val = request.form.get('symbol', '')
    if val:
        res = get_market_data(val)
        if res: stored_results.insert(0, res)
    return redirect('/')

@app.route('/clear')
def clear():
    global stored_results
    stored_results = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
