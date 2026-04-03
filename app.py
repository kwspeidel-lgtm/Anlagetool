import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # 1. Standard-Liste (wird immer angezeigt, wenn nichts gesucht wird)
    tickers = ["ABT", "AAPL", "MSFT"]
    
    # 2. Wenn du einen Einzelwert eingibst
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Wir machen aus deinem Einzelwert eine Liste, damit yf.download stabil bleibt
            tickers = [user_input.strip().upper()]

    results = []
    try:
        # 3. Der Batch-Download (Wichtig: threads=False für Render-Stabilität)
        data = yf.download(tickers, period="5y", group_by='ticker', progress=False, threads=False)

        if data.empty:
            return render_template('index.html', stocks=[{"name": "Keine Daten gefunden", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}])

        for s in tickers:
            # Logik für die Daten-Extraktion (Unterscheidung Batch vs. Einzelwert)
            if len(tickers) > 1:
                ticker_df = data[s]
            else:
                ticker_df = data

            if not ticker_df.empty and 'Close' in ticker_df:
                # Entferne leere Zeilen (Wochenenden/Feiertage)
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
        print(f"Fehler: {e}")
        results = [{"name": f"Fehler: {str(e)[:15]}", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
