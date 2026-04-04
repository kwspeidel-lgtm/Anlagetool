import pandas as pd
import yfinance as yf
from flask import Flask, render_template_string, request, session
import re
import os

app = Flask(__name__)
# Ein geheimer Schlüssel ist für Sessions (Speichern der Liste) notwendig
app.secret_key = os.urandom(24)

def get_single_stock(ticker):
    """Holt Daten nur für einen Ticker - spart Zeit und Ressourcen."""
    try:
        t = ticker.strip().upper()
        # Automatik für DE-Werte
        search_t = t if ("." in t or len(t) > 4) else f"{t}.DE"
        
        stock = yf.Ticker(search_t)
        df = stock.history(period="60d") # Nur 60 Tage laden statt 1 Jahr = schneller!
        
        if df.empty or len(df) < 38: return None
        
        current_price = df['Close'].iloc[-1]
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14 (vereinfacht für Speed)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1+rs))
        current_rsi = round(rsi.iloc[-1], 2)
        
        color = "#00ff88" if current_rsi < 35 else "#ff4d4d" if current_rsi > 65 else "#777"
        
        return {
            'ticker': t,
            'price': round(current_price, 2),
            'sma38': round(sma38, 2),
            'rsi': current_rsi,
            'rsi_color': color,
            'status': "OVER" if current_price > sma38 else "UNDER"
        }
    except:
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal 2026</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 10px; margin: 0; }
        .container { max-width: 450px; margin: auto; }
        .input-area { background: #161616; padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid #333; }
        textarea { width: 100%; height: 50px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 8px; box-sizing: border-box; font-size: 16px; }
        .gold-btn { background: linear-gradient(to bottom, #ffd700, #b8860b); color: #000; padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 8px; }
        .card { background: #161616; padding: 12px; margin-bottom: 6px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #ffd700; }
        .rsi-badge { padding: 3px 7px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
        .clear-btn { background: none; color: #444; border: none; cursor: pointer; text-decoration: underline; font-size: 0.7em; margin-top: 20px; width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center; color:#ffd700;">BASIC TERMINAL 🚀</h2>
        <div class="input-area">
            <form method="POST">
                <textarea name="ticker" placeholder="Ticker eingeben..."></textarea>
                <button type="submit" class="gold-btn">ANALYSIEREN & STAPELN</button>
            </form>
        </div>
        {% for s in stocks %}
        <div class="card">
            <div><strong>{{ s.ticker }}</strong><br><small>{{ s.price }}€ | SMA: {{ s.sma38 }}</small></div>
            <div style="text-align:right;">
                <span class="rsi-badge" style="background:{{ s.rsi_color }}">{{ s.rsi }}</span><br>
                <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}">{{ s.status }}</small>
            </div>
        </div>
        {% endfor %}
        <a href="/clear"><button class="clear-btn">Liste leeren</button></a>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def main():
    if 'watchlist_data' not in session:
        session['watchlist_data'] = []

    if request.method == 'POST':
        raw_input = request.form.get('ticker', '').upper()
        tickers = re.split(r'[,\s\n]+', raw_input)
        
        current_list = session['watchlist_data']
        for t in tickers:
            t = t.strip()
            if t and not any(stock['ticker'] == t for stock in current_list):
                new_data = get_single_stock(t)
                if new_data:
                    current_list.insert(0, new_data) # Neu nach OBEN
        
        session['watchlist_data'] = current_list[:30] # Limit auf 30 für Performance
        session.modified = True

    return render_template_string(HTML_TEMPLATE, stocks=session['watchlist_data'])

@app.route('/clear')
def clear():
    session['watchlist_data'] = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
