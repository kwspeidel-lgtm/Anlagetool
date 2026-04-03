import os
from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

def get_stock_data(symbol):
    try:
        # Wir laden 4 Jahre Daten, um sicherzugehen
        ticker = yf.Ticker(symbol.strip().upper())
        hist = ticker.history(period="4y")
        
        if hist.empty or len(hist) < 60:
            return None
            
        current_price = hist['Close'].iloc[-1]
        # SMA Berechnungen
        sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # 3-Jahres Performance (ca. 750 Handelstage)
        price_3y_ago = hist['Close'].iloc[-750] if len(hist) > 750 else hist['Close'].iloc[0]
        perf3y = ((current_price / price_3y_ago) - 1) * 100
        
        return {
            "name": symbol.upper(),
            "price": round(current_price, 2),
            "dist38": round(((current_price / sma38) - 1) * 100, 2),
            "dist60": round(((current_price / sma60) - 1) * 100, 2),
            "perf3y": round(perf3y, 2)
        }
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Wir starten mit Apple, damit man sofort sieht, ob es geht
    display_list = ["AAPL"] 
    
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            display_list.insert(0, user_input.upper())

    results = []
    for s in display_list:
        data = get_stock_data(s)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
