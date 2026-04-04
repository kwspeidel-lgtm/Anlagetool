import yfinance as yf
from flask import Flask, render_template_string, request, redirect
import pandas as pd

app = Flask(__name__)
stored_results = []

def calculate_smart_score(rsi, price, sma38):
    """Die zentrale Logik: Berechnet die Attraktivität (0-10)."""
    score = 0
    # RSI Logik (Günstigkeit)
    if rsi < 30: score += 6  # Massiv überverkauft
    elif rsi < 40: score += 4
    elif rsi > 70: score -= 2 # Heißgelaufen
    
    # Trend Logik (SMA38)
    diff = (price / sma38) - 1
    if -0.05 < diff < 0: score += 4 # Perfekte Rebound-Zone
    elif 0 < diff < 0.05: score += 2 # Trendbestätigung
    
    return max(0, min(10, score))

def get_market_data(input_val):
    """Holt Daten für Ticker oder WKN."""
    t = input_val.strip().upper()
    # Automatik für deutsche Werte (DAX/Nebenwerte)
    search_t = f"{t}.DE" if "." not in t and len(t) <= 6 else t
    
    try:
        stock = yf.Ticker(search_t)
        df = stock.history(period="60d")
        if df.empty or len(df) < 38: return None
        
        curr = df['Close'].iloc[-1]
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2)
        
        score = calculate_smart_score(rsi, curr, sma)
        
        return {
            'ticker': search_t.replace(".DE", ""),
            'price': f"{curr:.2f}",
            'sma38': f"{sma:.2f}",
            'rsi': rsi,
            'score': score,
            'status': "OVER" if curr > sma else "UNDER"
        }
    except: return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal - Smart Score</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 10px; text-align: center; }
        .container { max-width: 450px; margin: auto; }
        .input-area { background: #161616; padding: 20px; border-radius: 15px; border: 2px solid #ffd700; margin-bottom: 20px; }
        input { width: 70%; padding: 12px; border-radius: 8px; border: none; background: #222; color: #fff; font-size: 16px; }
        .gold-btn { background: #ffd700; color: #000; padding: 12px 20px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }
        .card { background: #161616; padding: 15px; margin-bottom: 10px; border-radius: 12px; border-left: 5px solid #444; display: flex; justify-content: space-between; align-items: center; text-align: left; }
        .gold-card { border-left: 5px solid #ffd700 !important; background: linear-gradient(90deg, #161616, #2a2400); }
        .score-box { text-align: center; background: #222; padding: 8px; border-radius: 8px; min-width: 50px; border: 1px solid #ffd700; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="color:#ffd700;">BASIC TERMINAL 🚀</h2>
        <div class="input-area">
            <form action="/check" method="POST">
                <input type="text" name="symbol" placeholder="WKN oder Ticker...">
                <button type="submit" class="gold-btn">+</button>
            </form>
        </div>

        {% for s in stocks %}
        <div class="card {{ 'gold-card' if s.score >= 7 else '' }}">
            <div>
                <strong style="font-size:1.2em;">{{ s.ticker }}</strong><br>
                <small style="color:#aaa;">{{ s.price }}€ | RSI: {{ s.rsi }}</small><br>
                <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}">{{ s.status }} SMA38</small>
            </div>
            <div class="score-box">
                <div style="font-size: 0.7em; color: #888;">SCORE</div>
                <div style="font-size: 1.4em; font-weight: bold; color: #ffd700;">{{ s.score }}</div>
            </div>
        </div>
        {% endfor %}
        
        <br><a href="/clear" style="color:#444; text-decoration:none; font-size:0.8em;">Terminal leeren</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, stocks=stored_results)

@app.route('/check', methods=['POST'])
def check():
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
