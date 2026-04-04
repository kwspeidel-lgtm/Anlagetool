import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

# Diese Funktion simuliert einen echten Browser-Besuch (Gschmäckle-Standard)
def get_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Upgrade-Insecure-Requests': '1'
    })
    return session

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    tickers = ["AAPL", "ABT", "MSFT"] # Start-Werte
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [user_input.strip().upper()]

    # Wir nutzen die Session für die gesamte Abfrage
    session = get_session()
    
    try:
        # Gschmäckle-Trick: Nutze yf.download mit der Session
        # Wir laden nur 7 Tage (Puffer für Wochenende), um die Last minimal zu halten
        data = yf.download(
            tickers=tickers,
            period="7d",
            interval="1d",
            session=session,
            proxy=None,
            progress=False,
            threads=False,
            group_by='ticker'
        )
        
        if not data.empty:
            for s in tickers:
                # Datenblock-Weiche
                df = data[s] if len(tickers) > 1 else data
                
                if not df.empty:
                    # Wir nehmen die letzte verfügbare Preis-Spalte
                    price_col = 'Close' if 'Close' in df.columns else df.columns[0]
                    close_prices = df[price_col].dropna()
                    
                    if not close_prices.empty:
                        curr = float(close_prices.iloc[-1])
                        stocks_data.append({
                            "name": s,
                            "price": round(curr, 2),
                            "dist38": 0,
                            "dist60": 0,
                            "perf3y": 0
                        })
    except Exception as e:
        print(f"Gschmäckle-Log: Fehler bei Abfrage: {e}")

    if not stocks_data:
        stocks_data = [{"name": "Yahoo blockiert trotz Gschmäckle-Filter", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
