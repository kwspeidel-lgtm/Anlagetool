import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def get_stock_data(symbol):
    try:
        # Ticker säubern
        s = symbol.strip().upper()
        ticker = yf.Ticker(s)
        
        # WICHTIG: Nur 1 Jahr Historie für SMA (schneller!)
        # Für die 3J-Performance machen wir eine separate, kurze Abfrage
        hist = ticker.history(period="1y")
        hist_3y = ticker.history(period="3y")

        if hist.empty:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        # SMA Berechnung
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # 3-Jahres Performance
        price_3y_ago = hist_3y['Close'].iloc[0] if not hist_3y.empty else current_price
        perf3y = ((current_price / price_3y_ago) - 1) * 100
        
        return {
            "name": s,
            "price": round(current_price, 2),
            "dist38": round(((current_price / sma38) - 1) * 100, 2),
            "dist60": round(((current_price / sma60) - 1) * 100, 2),
            "perf3y": round(perf3y, 2)
        }
    except Exception as e:
        print(f"Fehler: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir starten mit einer leeren Liste oder festen Werten
    stocks = []
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            data = get_stock_data(user_input)
            if data:
                stocks.append(data)
    
    # Standardwerte laden (optional)
    for default in ["ABT", "AAPL"]:
        if not any(s['name'] == default for s in stocks):
            d = get_stock_data(default)
            if d: stocks.append(d)

    return render_template('index.html', stocks=stocks)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
