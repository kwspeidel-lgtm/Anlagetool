import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import requests

app = Flask(__name__)

def get_stock_data(symbol):
    try:
        s = symbol.strip().upper()
        
        # DER TRICK: Wir erstellen eine Session mit Browser-Identität
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        })
        
        ticker = yf.Ticker(s, session=session)
        
        # Wir laden 1 Jahr und 3 Jahre (getrennt für Speed)
        hist = ticker.history(period="1y")
        if hist.empty:
            return {"name": f"{s} (Blockade)", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}
            
        current_price = hist['Close'].iloc[-1]
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # Kurzer Check für 3J Performance
        hist_3y = ticker.history(period="3y")
        p3y_start = hist_3y['Close'].iloc[0] if not hist_3y.empty else current_price
        perf3y = ((current_price / p3y_start) - 1) * 100
        
        return {
            "name": s,
            "price": round(current_price, 2),
            "dist38": round(((current_price/sma38)-1)*100, 2),
            "dist60": round(((current_price/sma60)-1)*100, 2),
            "perf3y": round(perf3y, 2)
        }
    except Exception as e:
        return {"name": f"Fehler: {str(e)[:10]}", "price": 0, "dist38": 0, "dist60": 0, "perf3y": 0}

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir nehmen Apple wieder als Test-Anker
    tickers = ["AAPL"]
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers.insert(0, user_input.upper())

    results = []
    for t in tickers:
        data = get_stock_data(t)
        if data:
            results.append(data)
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
