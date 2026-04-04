import os
from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    symbol = "AAPL"

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            symbol = user_input.strip().upper()

    try:
        # Minimal-Abfrage ohne Session-Zwang für den ersten Test
        data = yf.download(symbol, period="1d", progress=False)
        if not data.empty:
            price = float(data['Close'].iloc[-1])
            stocks_data.append({"name": symbol, "price": round(price, 2)})
    except Exception as e:
        print(f"Fehler: {e}")

    # WICHTIG: Wir geben IMMER eine Liste zurück, auch wenn sie leer ist
    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
