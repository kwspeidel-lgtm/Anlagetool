import yfinance as yf
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
stored_results = []

def get_market_data(input_val):
    t = input_val.strip().upper()
    search_t = f"{t}.DE" if "." not in t and len(t) <= 6 else t
    try:
        stock = yf.Ticker(search_t)
        df = stock.history(period="60d")
        if df.empty or len(df) < 38: return None
        
        info = stock.info
        kgv = info.get('trailingPE', 'n/a')
        if isinstance(kgv, (int, float)): kgv = round(kgv, 1)
        
        curr = df['Close'].iloc[-1]
        prev_close = df['Close'].iloc[-2]
        change_pct = ((curr / prev_close) - 1) * 100
        
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2)
        
        rsi_color = "#00ff88" if rsi < 40 else "#ff4d4d" if rsi > 60 else "#777"
        change_color = "#00ff88" if change_pct >= 0 else "#ff4d4d"
        
        return {
            'ticker': search_t.replace(".DE", ""),
            'price': f"{curr:.2f}",
            'change': f"{change_pct:+.2f}%",
            'change_color': change_color,
            'sma38': f"{sma:.2f}",
            'kgv': kgv,
            'rsi': rsi,
            'rsi_color': rsi_color,
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
        .input-area { background: #1a1a1a; padding: 25px; border-radius: 15px; border: 1px solid #333; margin-bottom: 25px; }
        input { width: 90%; padding: 15px; background: #222; border: 1px solid #444; color: #fff; border-radius: 10px; margin-bottom: 15px; font-size: 16px; }
        .gold-btn { background: #ffd700; color: #000; padding: 15px; border: none; border-radius: 10px; width: 95%; font-weight: bold; cursor: pointer; }
        .card { background: #161616; padding: 20px; margin-bottom: 12px; border-radius: 12px; border-left: 4px solid #ffd700; display: flex; justify-content: space-between; align-items: center; text-align: left; }
        .rsi-badge { padding: 5px 12px; border-radius: 6px; font-weight: bold; font-size: 0.9em; }
        .status-text { font-weight: bold; font-size: 0.85em; margin-top: 5px; }
        .kgv-tag { color: #888; font-size: 0.8em; margin-left: 10px; }
    </style>
    <script>
        function copyTerminalData() {
            let cards = document.querySelectorAll('.card');
            let textToCopy = "TERMINAL EXPORT:\\n";
            cards.forEach(card => {
                let ticker = card.querySelector('strong').innerText;
                let price = card.querySelector('.p-line').innerText;
                let rsi = card.querySelector('.rsi-badge').innerText;
                textToCopy += ticker + ": " + price + " | " + rsi + "\\n";
            });
            navigator.clipboard.writeText(textToCopy);
            alert("Kopiert für KI!");
        }
    </script>
</head>
<body>
    <div class="container">
        <h2 onclick="copyTerminalData()" style="color:#ffd700; cursor:pointer;">PRO TERMINAL 🚀</h2>
        <div class="input-area">
            <form action="/stack" method="POST">
                <input type="text" name="symbol" placeholder="WKN / Ticker..." required>
                <button type="submit" class="gold-btn">STAPELN</button>
            </form>
        </div>
        {% for s in stocks %}
        <div class="card">
            <div>
                <strong>{{ s.ticker }}</strong><span class="kgv-tag">KGV: {{ s.kgv }}</span><br>
                <div class="p-line" style="color:#fff; font-weight:bold; margin-top:3px;">
                    {{ s.price }}€ <span style="color:{{ s.change_color }}; font-size:0.8em;">({{ s.change }})</span>
                </div>
                <div class="status-text" style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}">{{ s.status }} SMA38</div>
                <small style="color:#555;">SMA: {{ s.sma38 }}</small>
            </div>
            <div style="text-align:right;">
                <div class="rsi-badge" style="background:{{ s.rsi_color }}; color:#000;">RSI: {{ s.rsi }}</div>
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
