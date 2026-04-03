import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. Die Liste der Ticker festlegen
    tickers = ["AAPL", "ABT", "MSFT"] # Deine Standard-Werte
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers.insert(0, user_input.upper())

    results = []
    try:
        # 2. DER CLOU: Ein einziger Download für ALLE Ticker gleichzeitig
        # Das ist viel unverdächtiger für Yahoo
        data = yf.download(tickers, period="4y", group_by='ticker', progress=False)

        for s in tickers:
            # Daten für den einzelnen Ticker aus dem großen Block ziehen
            if len(tickers) > 1:
                ticker_data = data[s]
            else:
                ticker_data = data # Falls nur ein Ticker abgefragt wird

            if not ticker_data.empty and 'Close' in ticker_data:
                close_prices = ticker_data['Close'].dropna()
                
                if len(close_prices) > 60:
                    current_price = close_prices.iloc[-1]
                    sma38 = close_prices.rolling(window=38).mean().iloc[-1]
                    sma60 = close_prices.rolling(window=60).mean().iloc[-1]
                    
                    # 3-Jahres Performance
                    p3y_start = close_prices.iloc[-750] if len(close_prices) > 750 else close_prices.iloc[0]
                    perf3y = ((current_price / p3y_start) - 1) * 100
                    
                    results.append({
                        "name": s,
                        "price": round(float(current_price), 2),
                        "dist38": round(float(((current_price/sma38)-1)*100), 2),
                        "dist60": round(float(((current_price/sma60)-1)*100), 2),
                        "perf3y": round(float(perf3y), 2)
                    })
    except Exception as e:
        print(f"Fehler beim Batch-Download: {e}")

    # Falls gar nichts geladen wurde, zeigen wir eine Info
    if not results:
        results = [{"name": "Warte auf Eingabe...", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
