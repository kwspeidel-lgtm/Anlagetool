import os
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    # Unsere Standard-Liste mit 5 Werten (Du kannst die Ticker hier ändern)
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            # Erlaubt Eingabe von mehreren Tickern mit Komma oder Leerzeichen
            tickers = [t.strip().upper() for t in user_input.replace(',', ' ').split()]

    for symbol in tickers:
        try:
            # Wir laden 5 Jahre für jeden Ticker einzeln
            df = yf.download(symbol, period="5y", progress=False)
            
            if not df.empty and len(df) > 60:
                close = df['Close']
                curr_p = float(close.iloc[-1])
                sma38 = float(close.rolling(window=38).mean().iloc[-1])
                sma60 = float(close.rolling(window=60).mean().iloc[-1])
                
                # Distanzen
                dist38 = ((curr_p / sma38) - 1) * 100
                dist60 = ((curr_p / sma60) - 1) * 100
                
                # 3-Jahre Performance
                start_idx = -756 if len(close) >= 756 else 0
                old_p = float(close.iloc[start_idx])
                perf3y = ((curr_p / old_p) - 1) * 100
                
                stocks_data.append({
                    "name": symbol,
                    "price": round(curr_p, 2),
                    "dist38": round(dist38, 2),
                    "dist60": round(dist60, 2),
                    "perf3y": round(perf3y, 2)
                })
        except Exception as e:
            print(f"Fehler bei {symbol}: {e}")

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
