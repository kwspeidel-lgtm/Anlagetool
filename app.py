import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

def get_data_safe(tickers):
    # Wir erstellen eine Session, die so aussieht wie ein echter Browser
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
    })
    
    try:
        # Wir laden die Daten MIT der Session
        data = yf.download(tickers, period="5y", group_by='ticker', session=session, progress=False, threads=False)
        return data
    except:
        return pd.DataFrame()

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    active_tickers = ["AAPL", "ABT", "MSFT"]

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            active_tickers = [user_input.strip().upper()]

    data = get_data_safe(active_tickers)
    
    if not data.empty:
        for s in active_tickers:
            try:
                # Unterscheidung: Ein Ticker vs Mehrere
                df = data[s] if len(active_tickers) > 1 else data
                
                # Wir nehmen die 'Close' Spalte, egal ob sie 'Close' oder 'Adj Close' heißt
                col = 'Close' if 'Close' in df.columns else df.columns[0]
                close = df[col].dropna()
                
                if len(close) > 60:
                    curr = float(close.iloc[-1])
                    s38 = float(close.rolling(window=38).mean().iloc[-1])
                    s60 = float(close.rolling(window=60).mean().iloc[-1])
                    
                    # Performance 3 Jahre
                    p3y_idx = -756 if len(close) > 756 else 0
                    p3y_val = float(close.iloc[p3y_idx])
                    
                    stocks_data.append({
                        "name": s,
                        "price": round(curr, 2),
                        "dist38": round(((curr/s38)-1)*100, 2),
                        "dist60": round(((curr/s60)-1)*100, 2),
                        "perf3y": round(((curr/p3y_val)-1)*100, 2)
                    })
            except:
                continue

    if not stocks_data:
        stocks_data = [{"name": "Yahoo liefert aktuell keine Daten", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
