import yfinance as yf
from flask import Flask, render_template_string, request, redirect
import re

app = Flask(__name__)

# GLOBALER SPEICHER - Bleibt im RAM von Render
stored_results = []
error_msg = ""

def get_stock_data(ticker):
    """Holt Daten extrem schnell (nur 38 Tage Historie)."""
    try:
        t = ticker.strip().upper()
        # Automatik für DE-Werte
        search_t = t if ("." in t or len(t) > 4) else f"{t}.DE"
        
        stock = yf.Ticker(search_t)
        # NUR 50 Tage laden - das ist das absolute Minimum für SMA38
        df = stock.history(period="50d") 
        
        if df.empty or len(df) < 38: 
            return None
        
        current_price = df['Close'].iloc[-1]
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14 (Schnellberechnung)
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
    except Exception as e:
        print(f"Fehler bei {ticker}: {e}")
        return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>BASIC Terminal</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 15px; }
        .container { max-width: 450px; margin: auto; }
        .input-area { background: #161616; padding: 15px; border-radius: 12px; border: 1px solid #333; margin-bottom: 15px; }
        textarea { width: 100%; height: 50px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 8px; font-size: 16px; box-sizing: border-box; }
        .gold-btn { background: linear-gradient(to bottom, #ffd700, #b8860b); color: #000; padding: 12px; border: none; border-radius: 8px; width: 100%; font-weight: bold; cursor: pointer; margin-top: 8px; }
        .card { background: #161616; padding: 12px; margin-bottom: 8px; border-radius: 8px; border-left: 4px solid #ffd700; display: flex; justify-content: space-between; align-items: center; }
        .error { color: #ff4d4d; font-size: 0.8em; text-align: center; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="text-align:center; color:#ffd700;">BASIC TERMINAL 🚀</h2>
        
        {% if error %} <div class="error">{{ error }}</div> {% endif %}

        <div class="input-area">
            <form action="/add" method="POST">
                <textarea name="ticker" placeholder="Ticker eingeben (z.B. BMW, SAP, META)..." required></textarea>
                <button type="submit" class="gold-btn">ANALYSIEREN & STAPELN</button>
            </form>
        </div>
        
        {% for s in stocks %}
        <div class="card">
            <div><strong>{{ s.ticker }}</strong><br><small>{{ s.price }}€ | SMA: {{ s.sma38 }}</small></div>
            <div style="text-align: right;">
                <span style="background:{{ s.rsi_color }}; padding:3px 7px; border-radius:4px; font-weight:bold; font-size:0.8em;">RSI: {{ s.rsi }}</span><br>
                <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}; font-weight:bold;">{{ s.status }} SMA38</small>
            </div>
        </div>
        {% endfor %}

        <a href="/clear" style="display:block; text-align:center; color:#444; text-decoration:none; font-size:0.8em; margin-top:20px;">Terminal leeren</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    global error_msg
    current_error = error_msg
    error_msg = "" # Reset nach Anzeige
    return render_template_string(HTML_TEMPLATE, stocks=stored_results, error=current_error)

@app.route('/add', methods=['POST'])
def add():
    global stored_results, error_msg
    raw_input = request.form.get('ticker', '').upper()
    tickers = re.split(r'[,\s\n]+', raw_input)
    
    found_any = False
    for t in tickers:
        t = t.strip()
        if t and not any(item['ticker'] == t for item in stored_results):
            res = get_stock_data(t)
            if res:
                stored_results.insert(0, res)
                found_any = True
            else:
                error_msg = f"Konnte Daten für {t} nicht laden (Ticker prüfen)."
    
    if not found_any and not error_msg:
        error_msg = "Keine neuen Ticker gefunden oder Abfrage zu langsam."
        
    return redirect('/')

@app.route('/clear')
def clear():
    global stored_results
    stored_results = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
