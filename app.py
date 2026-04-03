import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir starten mit einer Liste
    tickers = ["AAPL", "ABT", "MSFT"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [user_input.strip().upper()]

    results = []
    try:
        # Wir nutzen 'yfinance' direkt als Download-Manager mit festem Intervall
        # Das 'auto_adjust=True' hilft oft gegen leere Datenfelder
        data = yf.download(
            tickers=tickers, 
            period="5y", 
            group_by='ticker', 
            auto_adjust=True, 
            prepost=False, 
            threads=False, 
            proxy=None
        )

        if data.empty:
            return render_template('index.html', stocks=[{"name": "Yahoo Blockade aktiv", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}])

        for s in tickers:
            # Sicherheitscheck: Ist der Ticker im Ergebnis-Datenrahmen?
            ticker_df = data[s] if len(tickers) > 1 else data
            
            if not ticker_df.empty:
                # Wir nehmen die 'Close' Spalte (oder 'Close' falls vorhanden)
                col = 'Close' if 'Close' in ticker_df.columns else ticker_df.columns[0]
                close_prices = ticker_df[col].dropna()
                
                if len(close_prices) > 60:
                    curr = float(close_prices.iloc[-1])
                    s38 = float(close_prices.rolling(window=38).mean().iloc[-1])
                    s60 = float(close_prices.rolling(window=60).mean().iloc[-1])
                    
                    # 3-Jahre (750 Tage)
                    old_idx = -750 if len(close_prices) > 750 else 0
                    old_price = float(close_prices.iloc[old_idx])
                    
                    results.append({
                        "name": s,
                        "price": round(curr, 2),
                        "dist38": round(((curr / s38) - 1) * 100, 2),
                        "dist60": round(((curr / s60) - 1) * 100, 2),
                        "perf3y": round(((curr / old_price) - 1) * 100, 2)
                    })

    except Exception as e:
        results = [{"name": f"Error: {str(e)[:15]}", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    if not results:
        results = [{"name": "Keine Daten (Timeout)", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
