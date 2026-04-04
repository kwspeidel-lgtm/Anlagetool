import yfinance as yf
from flask import Flask, render_template_string, request, redirect

app = Flask(__name__)
stored_results = []

def get_smart_data(symbol):
    symbol = symbol.strip().upper()
    # Automatik für deutsche Werte, falls kein Punkt vorhanden
    search_t = f"{symbol}.DE" if "." not in symbol and len(symbol) <= 6 else symbol
    try:
        stock = yf.Ticker(search_t)
        df = stock.history(period="60d")
        if df.empty or len(df) < 38: return None
        
        curr = df['Close'].iloc[-1]
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2)
        
        score = 0
        if rsi < 35: score += 6
        if curr < sma: score += 4
        
        return {
            'ticker': search_t.replace(".DE", ""), 'price': f"{curr:.2f}",
            'rsi': rsi, 'score': min(10, score), 'status': "UNDER" if curr < sma else "OVER"
        }
    except: return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal - Multi-Check</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 15px; text-align: center; }
        .container { max-width: 450px; margin: auto; }
        .input-area { background: #161616; padding: 20px; border-radius: 15px; border: 2px solid #ffd700; margin-bottom: 20px; }
        input { width: 80%; padding: 15px; border-radius: 10px; border: none; background: #222; color: #fff; font-size: 16px; margin-bottom: 10px; }
        .gold-btn { background: #ffd700; color: #000; padding: 15px; border: none; border-radius: 10px; width: 100%; font-weight: bold; cursor: pointer; }
        .card { background: #161616; padding: 15px; margin-bottom: 10px; border-radius: 12px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #444; text-align: left; }
        .gold-card { border-left: 5px solid #ffd700 !important; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="color:#ffd700;">BASIC TERMINAL 🚀</h2>
        <div class="input-area">
            <form action="/check" method="POST">
                <input type="text" name="symbols" placeholder="WKNs/Ticker (mit Komma getrennt)...">
                <button type="submit" class="gold-btn">JETZT STAPELN</button>
            </form>
        </div>
        {% for s in stocks %}
        <div class="card {{ 'gold-card' if s.score >= 7 else '' }}">
            <div>
                <strong>{{ s.ticker }}</strong><br>
                <small>{{ s.price }}€ | RSI: {{ s.rsi }}</small>
            </div>
            <div style="text-align:right;">
                <div style="font-size: 1.5em; font-weight: bold; color: #ffd700;">{{ s.score }}</div>
                <small style="color:{{ '#ff4d4d' if s.status == 'UNDER' else '#00ff88' }}">{{ s.status }} SMA38</small>
            </div>
        </div>
        {% endfor %}
        <br><a href="/clear" style="color:#555; text-decoration:none;">Liste leeren</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_TEMPLATE, stocks=stored_results)

@app.route('/check', methods=['POST'])
def check():
    global stored_results
    raw = request.form.get('symbols', '')
    symbols = [s.strip() for s in raw.replace(',', ' ').split()]
    for s in symbols:
        res = get_smart_data(s)
        if res: stored_results.insert(0, res)
    return redirect('/')

@app.route('/clear')
def clear():
    global stored_results
    stored_results = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
