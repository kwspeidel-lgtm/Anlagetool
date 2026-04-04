import pandas as pd
import yfinance as yf
from flask import Flask, render_template_string, request, redirect, url_for
import re

app = Flask(__name__)

# Datenbank im RAM
watchlist = []

def get_stock_data(ticker):
    """Holt Live-Daten, RSI und SMA38."""
    try:
        # Falls Ticker manuell ohne Endung kam, .DE für deutsche Werte ergänzen
        search_ticker = ticker if "." in ticker else f"{ticker}.DE"
        stock = yf.Ticker(search_ticker)
        df = stock.history(period="1y")
        
        if df.empty: return None
        
        # SMA38
        df['SMA38'] = df['Close'].rolling(window=38).mean()
        current_price = df['Close'].iloc[-1]
        sma38 = df['SMA38'].iloc[-1]
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1+rs))
        current_rsi = round(rsi.iloc[-1], 2)
        
        # Farblogik für RSI
        rsi_color = "#4CAF50" if current_rsi < 30 else "#F44336" if current_rsi > 70 else "#888"
        
        return {
            'ticker': ticker,
            'price': round(current_price, 2),
            'sma38': round(sma38, 2),
            'rsi': current_rsi,
            'rsi_color': rsi_color,
            'status': "OVER" if current_price > sma38 else "UNDER"
        }
    except:
        return None

# --- HTML INTERFACE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal 2026</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: 'Segoe UI', sans-serif; background: #0f0f0f; color: #e0e0e0; padding: 15px; margin: 0; }
        .container { max-width: 600px; margin: auto; }
        h1 { color: #ffd700; text-align: center; font-size: 1.5em; margin-bottom: 20px; }
        .input-area { background: #1a1a1a; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 20px; }
        textarea { width: 100%; height: 60px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 10px; box-sizing: border-box; font-size: 16px; }
        .gold-btn { background: linear-gradient(45deg, #ffd700, #ff8c00); color: #000; padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 10px; font-size: 1em; }
        .card { background: #1a1a1a; padding: 12px; margin-bottom: 8px; border-radius: 10px; border-left: 4px solid #ffd700; display: flex; justify-content: space-between; align-items: center; border: 1px solid #333; }
        .price-info { font-size: 0.85em; color: #aaa; }
        .status-over { color: #00ff88; font-weight: bold; font-size: 0.8em; }
        .status-under { color: #ff4d4d; font-weight: bold; font-size: 0.8em; }
        .rsi-badge { padding: 4px 8px; border-radius: 6px; font-size: 0.85em; color: white; font-weight: bold; }
        .clear-btn { background: none; color: #666; border: none; cursor: pointer; text-decoration: underline; font-size: 0.75em; width: 100%; margin-top: 15px; }
        .ticker-name { font-size: 1.1em; font-weight: bold; color: #fff; }
    </style>
</head>
<body>
    <div class="container">
        <h1>BASIC TERMINAL 🚀</h1>
        
        <div class="input-area">
            <form action="/add" method="post">
                <textarea name="raw_input" placeholder="Ticker (z.B. BMW) oder Text-Paste..."></textarea>
                <button type="submit" class="gold-btn">ANALYSYIEREN & STAPELN</button>
            </form>
        </div>

        <div id="results">
            {% for stock in stocks %}
            <div class="card">
                <div>
                    <span class="ticker-name">{{ stock.ticker }}</span><br>
                    <span class="price-info">{{ stock.price }}€ | SMA: {{ stock.sma38 }}€</span>
                </div>
                <div style="text-align: right;">
                    <span class="rsi-badge" style="background: {{ stock.rsi_color }}">RSI: {{ stock.rsi }}</span><br>
                    <span class="{{ 'status-over' if stock.status == 'OVER' else 'status-under' }}">
                        {{ stock.status }} SMA38
                    </span>
                </div>
            </div>
            {% endfor %}
        </div>

        <form action="/clear" method="post">
            <button type="submit" class="clear-btn">Terminal leeren</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    stock_results = []
    # Wir zeigen nur die letzten 20 an, um Render nicht zu überlasten
    for t in watchlist[:20]:
        res = get_stock_data(t)
        if res: stock_results.append(res)
    return render_template_string(HTML_TEMPLATE, stocks=stock_results)

@app.route('/add', methods=['POST'])
def add():
    raw_data = request.form.get('raw_input', '').upper()
    
    # 1. Regex für Textblöcke (findet SAP.DE, TSLA, etc.)
    found = re.findall(r'\b[A-ZÖÄÜ]{2,5}(?:\.[A-Z]{2})?\b', raw_data)
    
    # 2. Falls manuell nur ein Wort eingegeben wurde (z.B. "BMW")
    if not found and len(raw_data.strip()) > 1:
        found = [raw_data.strip().split()[0]] # Nur das erste Wort nehmen

    for ticker in found:
        if ticker not in watchlist:
            watchlist.insert(0, ticker) # Immer ganz nach OBEN stapeln
            
    return redirect(url_for('index'))

@app.route('/clear', methods=['POST'])
def clear():
    global watchlist
    watchlist = []
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
