import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import numpy as np

app = Flask(__name__)

def calculate_rsi(data, window=14):
    delta = data.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1+rs))

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"] # Deine Stamm-Elf

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers = [t.strip().upper() for t in user_input.replace(',', ' ').split()]

    for symbol in tickers:
        try:
            t = yf.Ticker(symbol)
            df = t.history(period="5y")
            info = t.info
            
            if not df.empty and len(df) > 60:
                close = df['Close']
                curr_p = float(close.iloc[-1])
                
                # Technische Werte
                sma38 = float(close.rolling(window=38).mean().iloc[-1])
                sma60 = float(close.rolling(window=60).mean().iloc[-1])
                rsi_val = float(calculate_rsi(close).iloc[-1])
                
                # Fundamentaldaten (KGV)
                kgv = info.get('trailingPE', 'N/A')
                
                # Performance & Distanz
                dist38 = ((curr_p / sma38) - 1) * 100
                start_idx = -756 if len(close) >= 756 else 0
                perf3y = ((curr_p / float(close.iloc[start_idx])) - 1) * 100
                
                stocks_data.append({
                    "name": symbol,
                    "price": round(curr_p, 2),
                    "dist38": round(dist38, 2),
                    "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else "N/A",
                    "kgv": round(kgv, 1) if isinstance(kgv, (int, float)) else "N/A",
                    "perf3y": round(perf3y, 2)
                })
        except Exception as e:
            print(f"Fehler bei {symbol}: {e}")

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
