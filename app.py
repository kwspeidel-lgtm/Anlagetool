import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

# Diese Funktion nutzt den stabilen Batch-Download
def get_stock_data(tickers):
    results = []
    try:
        # Ein einziger Download für alle Ticker (Gschmäckle-Logik)
        data = yf.download(tickers, period="5y", group_by='ticker', progress=False, threads=False)
        
        if data.empty:
            return results

        for s in tickers:
            # Weiche: Mehrere Ticker vs. Einzelwert
            if len(tickers) > 1:
                ticker_df = data[s]
            else:
                ticker_df = data
            
            if not ticker_df.empty and 'Close' in ticker_df:
                close_prices = ticker_df['Close'].dropna()
                
                if len(close_prices) > 60:
                    current_price = float(close_prices.iloc[-1])
                    sma38 = float(close_prices.rolling(window=38).mean().iloc[-1])
                    sma60 = float(close_prices.rolling(window=60).mean().iloc[-1])
                    
                    # 3-Jahres Performance (ca. 756 Handelstage)
                    p3y_idx = -756 if len(close_prices) > 756 else 0
                    price_3y_ago = float(close_prices.iloc[p3y_idx])
                    perf3y = ((current_price / price_3y_ago) - 1) * 100
                    
                    results.append({
                        "name": s,
                        "price": round(current_price, 2),
                        "dist38": round(((current_price / sma38) - 1) * 100, 2),
                        "dist60": round(((current_price / sma60) - 1) * 100, 2),
                        "perf3y": round(perf3y, 2)
                    })
    except Exception as e:
        print(f"Fehler beim Abrufen: {e}")
    return results

@app.route('/', methods=['GET', 'POST'])
def index():
    # Start-Liste
    active_tickers = ["AAPL", "ABT", "MSFT"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Bei Suche nur den Einzelwert zeigen
            active_tickers = [user_input.strip().upper()]

    stocks_data = get_stock_data(active_tickers)
    
    # Falls gar nichts gefunden wurde (z.B. Tippfehler)
    if not stocks_data:
        stocks_data = [{"name": "Keine Daten", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]
        
    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    # Wichtig für Render: Port 10000 als Standard
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
