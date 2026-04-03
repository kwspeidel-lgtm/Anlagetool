import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def get_stock_data(query):
    try:
        symbol = query.strip().upper()
        # Den Ticker erstellen
        t = yf.Ticker(symbol)
        
        # WICHTIG: Wir erzwingen den Download mit period="5y"
        # yfinance braucht manchmal einen Moment oder mehrere Versuche
        hist = t.history(period="5y")
        
        if hist.empty or len(hist) < 100:
            return None
            
        # Letzte Zeile (heute)
        last_row = hist.iloc[-1]
        current_price = last_row['Close']
        
        # SMA Berechnung (38 und 60 Tage)
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # 3-Jahres Performance (ca. 750 Handelstage zurück)
        # Wir nehmen den Kurs von vor genau 3 Jahren
        price_3y_ago = hist['Close'].iloc[-750] if len(hist) > 750 else hist['Close'].iloc[0]
        perf3y = ((current_price / price_3y_ago) - 1) * 100
        
        return {
            "name": symbol,
            "price": round(current_price, 2),
            "dist38": round(((current_price / sma38) - 1) * 100, 2),
            "dist60": round(((current_price / sma60) - 1) * 100, 2),
            "perf3y": round(perf3y, 2)
        }
    except Exception as e:
        print(f"Fehler bei {query}: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    results = []
    # Teste es mal mit diesen drei Standard-Tickern
    tickers = ["AAPL", "MSFT", "TSLA"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Deine Eingabe kommt nach vorne
            tickers.insert(0, user_input.upper())

    for symbol in tickers:
        data = get_stock_data(symbol)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
