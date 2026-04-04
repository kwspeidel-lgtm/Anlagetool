import yfinance as yf
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
stored_results = []

def get_market_data(input_val):
    t = input_val.strip().upper()
    
    # LOGIK-CHECK: Ist es eine deutsche WKN (6 Zahlen) oder ein deutsches Kürzel?
    if t.isdigit() and len(t) == 6:
        search_t = f"{t}.DE"
    elif len(t) <= 4 and t not in ["META", "AAPL", "MSFT", "NVDA", "TSLA", "GOOG"]:
        # Standardmäßig .DE für kurze Kürzel, außer es sind bekannte US-Größen
        search_t = f"{t}.DE"
    else:
        # Alles andere (US-Ticker oder bereits mit Punkt) direkt lassen
        search_t = t

    try:
        stock = yf.Ticker(search_t)
        # Wenn US-Ticker nicht gefunden, probier es ohne .DE (Fallback)
        df = stock.history(period="65d")
        if df.empty and ".DE" in search_t:
            search_t = search_t.replace(".DE", "")
            stock = yf.Ticker(search_t)
            df = stock.history(period="65d")
            
        if df.empty: return None
        
        # Daten abrufen
        curr = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((curr / prev_close) - 1) * 100
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2) if loss > 0 else 50
        
        # KGV Check
        try:
            kgv = stock.info.get('trailingPE', 'n/a')
            if isinstance(kgv, (int, float)): kgv = round(kgv, 1)
        except: kgv = "n/a"
        
        return {
            'ticker': search_t,
            'price': f"{curr:.2f}",
            'change': f"{change_pct:+.2f}%",
            'change_color': "#00ff88" if change_pct >= 0 else "#ff4d4d",
            'sma38': f"{sma:.2f}",
            'kgv': kgv,
            'rsi': rsi,
            'rsi_color': "#00ff88" if rsi < 40 else "#ff4d4d" if rsi > 60 else "#777",
            'status': "OVER" if curr > sma else "UNDER"
        }
    except: return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PRO Terminal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 15px; text-align: center; }
        .container { max-width: 500px; margin: auto; }
        .input-area { background: #1a1a1a; padding: 20px; border-radius: 15px; border: 1px solid #333; margin-bottom: 20px; }
        input { width: 85%; padding: 15px; background: #222; border: 1px solid #444; color: #fff; border-radius: 10px; margin-bottom: 10px; font-size: 16px; }
        .gold-btn { background: #ffd700; color: #000; padding: 15px; border: none; border-radius: 10px; width: 90%; font-weight: bold; cursor: pointer; }
        .card { background: #161616; padding: 15px; margin-bottom: 10px; border-radius: 12px; border-left: 4px solid #ffd700; display: flex; justify-content: space-between; align-items: center; text-align: left; }
        .rsi-badge { padding: 5px 10px; border-radius: 6px; font-weight: bold; }
    </style>
    <script>
        function copyData() {
            let cards = document.querySelectorAll('.card');
            let txt = "TERMINAL EXPORT:\\n";
            cards.forEach(c => { txt += c.innerText.replace(/\\n/g, " ") + "\\n"; });
            navigator.clipboard.writeText(txt); alert("Kopiert!");
        }
    </script>
</head>
<body>
    <div class="container">
        <h2 onclick="copyData()" style="color:#ffd700; cursor:pointer;">PRO TERMINAL 🚀</h2>
        <form class="input-area" action="/stack" method="POST">
            <input type="text" name="symbol" placeholder="WKN (716460) oder Ticker (META)..." required>
            <button type="submit" class="gold-btn">STAPELN</button>
        </form>
        {% for s in stocks %}
        <div class="card">
            <div>
                <strong>{{ s.ticker }}</strong> <small style="color:#888;">KGV: {{ s.kgv }}</small><br>
                <span style="font-weight:bold;">{{ s.price }} <small style="color:{{ s.change_color }};">({{ s.change }})</small></span><br>
                <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}; font-weight:bold;">{{ s.status }} SMA38</small>
            </div>
            <div class="rsi-badge" style="background:{{ s.rsi_color }}; color:#000;">RSI: {{ s.rsi }}</div>
        </div>
        {% endfor %}
        <br><a href="/clear" style="color:#444; text-decoration:none;">Leeren</a>
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
