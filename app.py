import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def get_stock_data(symbol):
    try:
        s = symbol.strip().upper()
        # Erstelle das Ticker-Objekt
        ticker = yf.Ticker(s)
        
        # Test: Wir laden erst mal nur 1 Jahr (geht am schnellsten)
        hist = ticker.history(period="1y")
        
        if hist.empty:
            # Replit-Style Diagnose: Wir geben eine Info-Zeile zurück
            return {"name": f"{s} (Yahoo blockt)", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}
            
        current_price = hist['Close'].iloc[-1]
        
        # SMAs berechnen
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # Performance 3 Jahre (separater kurzer Check)
        hist_3y = ticker.history(period="3y")
        p3y_start = hist_3y['Close'].iloc[0] if not hist_3y.empty else current_price
        perf3y = ((current_price / p3y_start) - 1) * 100
        
        return {
            "name": s,
            "price": round(current_price, 2),
            "dist38": round(((current_price/sma38)-1)*100, 2),
            "dist60": round(((current_price/sma60)-1)*100, 2),
            "perf3y": round(perf3y, 2)
        }
    except Exception as e:
        # Zeigt den technischen Fehler direkt in der Tabelle an
        error_msg = str(e)[:20]
        return {"name": f"Fehler: {error_msg}", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir starten mit Apple (AAPL) als Test-Anker
    tickers = ["AAPL"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Wenn du suchst, schieben wir das Ergebnis ganz nach oben
            tickers.insert(0, user_input.upper())

    results = []
    for t in tickers:
        data = get_stock_data(t)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    # Wichtig für Render: Port-Zuweisung
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
