import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    # Test-Werte
    tickers = ["AAPL", "ABT", "MSFT"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [user_input.strip().upper()]

    try:
        # Browser-Simulation
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        
        # Wir laden nur 5 Tage Daten – das geht blitzschnell und ist stabil
        data = yf.download(tickers, period="5d", group_by='ticker', session=session, progress=False, threads=False)
        
        if not data.empty:
            for s in tickers:
                # Datenblock für den Ticker
                df = data[s] if len(tickers) > 1 else data
                
                if not df.empty:
                    # Suche nach irgendeiner Preis-Spalte (Close oder Adj Close)
                    price_col = next((c for c in ['Close', 'Adj Close'] if c in df.columns), None)
                    
                    if price_col:
                        # Hol den allerletzten Preis
                        current_price = float(df[price_col].dropna().iloc[-1])
                        
                        stocks_data.append({
                            "name": s,
                            "price": round(current_price, 2),
                            "dist38": 0, # Platzhalter
                            "dist60": 0, # Platzhalter
                            "perf3y": 0  # Platzhalter
                        })
    except Exception as e:
        print(f"Fehler: {e}")

    if not stocks_data:
        stocks_data = [{"name": "Suche...", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
