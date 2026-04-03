from flask import Flask, render_template, request
import yfinance as yf
from datetime import datetime, timedelta

app = Flask(__name__)

# Start-Liste (Standardwerte)
current_stocks = ["ABT", "BRK-B"]

def get_stock_info(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="4y")
        if not hist.empty and len(hist) > 60:
            current_price = hist['Close'].iloc[-1]
            sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
            sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
            price_3y_ago = hist['Close'].iloc[-750] if len(hist) > 750 else hist['Close'].iloc[0]
            
            return {
                "name": symbol.upper(),
                "price": round(current_price, 2),
                "dist38": round(((current_price/sma38)-1)*100, 2),
                "dist60": round(((current_price/sma60)-1)*100, 2),
                "perf3y": round(((current_price/price_3y_ago)-1)*100, 2)
            }
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def home():
    display_list = ["ABT", "BRK-B"] # Standardwerte
    
    if request.method == 'POST':
        new_ticker = request.form.get('ticker').strip().upper()
        if new_ticker:
            display_list.insert(0, new_ticker) # Neue Suche ganz oben anzeigen

    results = []
    for s in display_list:
        data = get_stock_info(s)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
