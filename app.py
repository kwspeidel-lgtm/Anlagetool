import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# Diese Funktion ist jetzt identisch mit der stabilen Ur-Version
def get_stock_data(symbol):
    try:
        # Wir erzwingen das Herunterladen der Daten
        ticker = yf.Ticker(symbol.strip().upper())
        hist = ticker.history(period="5y") # Viel Puffer für SMA und 3J
        
        if hist.empty or len(hist) < 200:
            return None
            
        current_price = hist['Close'].iloc[-1]
        
        # SMAs wie in deiner ersten funktionierenden Version
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # 3-Jahres Performance (ca. 756 Handelstage)
        price_3y_ago = hist['Close'].iloc[-756] if len(hist) > 756 else hist['Close'].iloc[0]
        perf3y = ((current_price / price_3y_ago) - 1) * 100
        
        return {
            "name": symbol.upper(),
            "price": round(current_price, 2),
            "dist38": round(((current_price / sma38) - 1) * 100, 2),
            "dist60": round(((current_price / sma60) - 1) * 100, 2),
            "perf3y": round(perf3y, 2)
        }
    except Exception as e:
        print(f"Fehler bei {symbol}: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir nutzen wieder die feste Liste als Basis (wie in Version 1)
    # So ist die Tabelle nie leer!
    tickers = ["ABT", "AAPL", "MSFT"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Die Suche wird zur festen Liste hinzugefügt
            tickers.insert(0, user_input.upper())

    results = []
    for s in tickers:
        data = get_stock_data(s)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
