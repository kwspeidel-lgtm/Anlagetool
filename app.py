import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    # Standard-Werte für den ersten Start
    tickers = ["AAPL", "ABT", "MSFT"]

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [user_input.strip().upper()]

    try:
        # Wir laden die Daten. threads=False ist lebenswichtig für Render!
        data = yf.download(tickers, period="5y", group_by='ticker', progress=False, threads=False)
        
        if not data.empty:
            for s in tickers:
                try:
                    # Holen des richtigen Datenblocks
                    df = data[s] if len(tickers) > 1 else data
                    if df.empty or 'Close' not in df.columns:
                        continue
                        
                    close = df['Close'].dropna()
                    if len(close) > 60:
                        curr = float(close.iloc[-1])
                        s38 = float(close.rolling(window=38).mean().iloc[-1])
                        s60 = float(close.rolling(window=60).mean().iloc[-1])
                        
                        # 3-Jahres Check
                        p3y_price = float(close.iloc[-750]) if len(close) > 750 else float(close.iloc[0])
                        
                        stocks_data.append({
                            "name": s,
                            "price": round(curr, 2),
                            "dist38": round(((curr/s38)-1)*100, 2),
                            "dist60": round(((curr/s60)-1)*100, 2),
                            "perf3y": round(((curr/p3y_price)-1)*100, 2)
                        })
                except:
                    continue
    except Exception as e:
        print(f"Fehler: {e}")

    # Falls die Liste leer ist, zeigen wir eine Dummy-Zeile statt abzustürzen
    if not stocks_data:
        stocks_data = [{"name": "Keine Daten gefunden", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}]

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    # Render nutzt Port 10000 oder den zugewiesenen Port
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
