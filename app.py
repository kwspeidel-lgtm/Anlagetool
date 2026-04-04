import os
from flask import Flask, render_template, request
import yfinance as yf
import requests

app = Flask(__name__)

# Der Gschmäckle-Session-Trick für Yahoo
def get_session():
    s = requests.Session()
    s.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return s

@app.route('/', methods=['GET', 'POST'])
def index():
    stocks_data = []
    symbol = "AAPL" # Test-Aktie

    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            symbol = user_input.strip().upper()

    try:
        # Wir fragen nur den Kurs ab
        session = get_session()
        ticker_obj = yf.Ticker(symbol, session=session)
        df = ticker_obj.history(period="1d")
        
        if not df.empty:
            last_price = float(df['Close'].iloc[-1])
            stocks_data.append({
                "name": symbol,
                "price": round(last_price, 2)
            })
    except Exception as e:
        print(f"Fehler: {e}")

    if not stocks_data:
        # Fehlermeldung, falls Yahoo die IP von Render doch blockt
        stocks_data = [{"name": "Yahoo blockiert IP", "price": 0}]

    return render_template('index.html', stocks=stocks_data)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
