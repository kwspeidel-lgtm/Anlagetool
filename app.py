import os
import time
from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd

app = Flask(__name__)

def get_stock_data(symbol):
    symbol = symbol.strip().upper()

    hist = None

    # 🔁 Retry-Logik (Yahoo ist oft instabil)
    for attempt in range(3):
        try:
            hist = yf.download(symbol, period="5y", progress=False)

            print(f"{symbol}: Versuch {attempt+1} → {len(hist)} Datenpunkte")

            if hist is not None and not hist.empty:
                break

        except Exception as e:
            print(f"{symbol}: Fehler bei Versuch {attempt+1}: {e}")

        time.sleep(1)

    # ❌ Wenn keine Daten → abbrechen
    if hist is None or hist.empty or len(hist) < 200:
        print(f"{symbol}: keine brauchbaren Daten")
        return None

    try:
        hist = hist.dropna()

        current_price = hist['Close'].iloc[-1]

        # 📊 SMAs
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]

        # 📈 3-Jahres Performance (~756 Handelstage)
        if len(hist) > 756:
            price_3y_ago = hist['Close'].iloc[-756]
        else:
            price_3y_ago = hist['Close'].iloc[0]

        perf3y = ((current_price / price_3y_ago) - 1) * 100

        return {
            "name": symbol,
            "price": round(current_price, 2),
            "dist38": round(((current_price / sma38) - 1) * 100, 2),
            "dist60": round(((current_price / sma60) - 1) * 100, 2),
            "perf3y": round(perf3y, 2)
        }

    except Exception as e:
        print(f"{symbol}: Fehler in Berechnung: {e}")
        return None


@app.route('/', methods=['GET', 'POST'])
def index():
    tickers = ["ABT", "AAPL", "MSFT"]

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers.insert(0, user_input.strip().upper())

    results = []

    for s in tickers:
        data = get_stock_data(s)
        if data:
            results.append(data)

    return render_template('index.html', stocks=results)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
