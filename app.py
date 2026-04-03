import os
import time
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

def get_stock_data(symbol):
    try:
        s = symbol.strip().upper()
        
        # Erhöhte Tarnung: Wir nutzen ein Session-Objekt mit komplexeren Headern
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://finance.yahoo.com/'
        })

        # Wir fügen eine winzige Pause ein, um menschliches Verhalten zu imitieren
        time.sleep(0.5)

        # Download der Daten direkt über die Session
        data = yf.download(s, period="4y", session=session, progress=False, group_by='ticker')

        if data.empty:
            return {"name": f"{s} (Yahoo Sperre)", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}

        # Falls Multi-Index (bei yf.download oft der Fall), extrahieren wir die Spalte
        if isinstance(data.columns, pd.MultiIndex):
            close_prices = data[s]['Close']
        else:
            close_prices = data['Close']

        current_price = close_prices.iloc[-1]
        sma38 = close_prices.rolling(window=38).mean().iloc[-1]
        sma60 = close_prices.rolling(window=60).mean().iloc[-1]
        
        # 3-Jahres Performance
        p3y_start = close_prices.iloc[-750] if len(close_prices) > 750 else close_prices.iloc[0]
        perf3y = ((current_price / p3y_start) - 1) * 100

        return {
            "name": s,
            "price": round(float(current_price), 2),
            "dist38": round(float(((current_price/sma38)-1)*100), 2),
            "dist60": round(float(((current_price/sma60)-1)*100), 2),
            "perf3y": round(float(perf3y), 2)
        }
    except Exception as e:
        return {"name": f"Fehler: {str(e)[:15]}", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir nehmen einen defensiven Startwert
    tickers = ["AAPL"]
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [user_input.upper()]

    results = []
    for t in tickers:
        res = get_stock_data(t)
        if res:
            results.append(res)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
