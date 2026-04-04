import pandas as pd
import yfinance as yf
from flask import Flask, render_template_string, request, redirect
import re

app = Flask(__name__)

# Diese Liste bleibt im Arbeitsspeicher des Servers (stabil solange App läuft)
# Wir speichern hier direkt die fertigen Ergebnisse, nicht nur die Ticker!
stored_results = []

def get_stock_data(ticker):
    """Holt Live-Daten für EINEN Ticker (schnell)."""
    try:
        t = ticker.strip().upper()
        # Automatik für DE-Werte (2-4 Zeichen ohne Punkt)
        search_t = t if ("." in t or len(t) > 4) else f"{t}.DE"
        
        stock = yf.Ticker(search_t)
        df = stock.history(period="60d") # Schnell-Abfrage
        
        if df.empty or len(df) < 38: return None
        
        current_price = df['Close'].iloc[-1]
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1+rs))
        current_rsi = round(rsi.iloc[-1], 2)
        
        # Farblogik
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

# --- HTML ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal 2026</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 10px; margin: 0; }
        .container { max-width: 450px; margin: auto; }
        .input-area { background: #161616; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; }
        textarea { width: 100%; height: 50px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 8px; box-sizing: border-box; font-size: 16px; }
        .gold-btn { background: linear-gradient(to bottom, #ffd700, #b8860b); color: #000; padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 8px; width: 100%; }
        .card { background: #161616; padding: 12px; margin-bottom: 6px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; border-left: 4px solid #ffd700; border: 1px solid #222; }
        .rsi-badge { padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 0.85em; color: white; }
        .status-over { color: #00ff88; font-size: 0.8em; font-weight: bold; }
        .status-under { color: #ff4d4d; font-size: 0.8em; font-weight: bold; }
        .clear-link { display: block; text-align: center; color: #555; text-decoration: none; font-size: 0.75em; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center; color:#ffd700; letter-spacing: 1px;">BASIC TERMINAL 🚀</h2>
        <div class="input-area">
            <form action="/add" method="POST">
                <textarea name="ticker" placeholder="Ticker eingeben (z.B. VW, META, SAP)..." required></textarea>
                <button type="submit" class="gold-btn">ANALYSIEREN & STAPELN</button>
            </form>
        </div>
        
        {% for s in stocks %}
        <div class="card">
            <div>
                <span style="font-size: 1.1em; font-weight: bold;">{{ s.ticker }}</span><br>
                <span style="font-size: 0.85em; color: #999;">{{ s.price }}€ | SMA: {{ s.sma38 }}</span>
            </div>
            <div style="text-align: right;">
                <span class="rsi-badge" style="background: {{ s.rsi_color }}">RSI: {{ s.rsi }}</span><br>
                <span class="{{ 'status-over' if s.status == 'OVER' else 'status-under' }}">{{ s.status }} SMA38</span>
            </div>
        </div>
        {% endfor %}

        <a href="/clear" class="clear-link">Liste komplett leeren</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, stocks=stored_results)

@app.route('/add', methods=['POST'])
def add():
    global stored_results
    raw_input = request.form.get('ticker', '').upper()
    
    # Trenne die Eingabe (bei Leerzeichen, Komma oder Zeilenumbruch)
    new_tickers = re.split(r'[,\s\n]+', raw_input)
    
    for t in new_tickers:
        t = t.strip()
        if t:
            # Check ob der Ticker schon in der Liste ist (Duplikate vermeiden)
            if not any(item['ticker'] == t for item in stored_results):
                res = get_stock_data(t)
                if res:
                    # NEUEN WERT GANZ NACH OBEN
                    stored_results.insert(0, res)
    
    return redirect('/')

@app.route('/clear')
def clear():
    global stored_results
    stored_results = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
