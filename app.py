import os
from flask import Flask, render_template, request
import yfinance as yf

app = Flask(__name__)

def get_data(symbol):
    try:
        t = yf.Ticker(symbol.strip().upper())
        # 4 Jahre für 3J-Performance + SMA Puffer
        hist = t.history(period="4y")
        if hist.empty or len(hist) < 60:
            return None
            
        cur = hist['Close'].iloc[-1]
        s38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        s60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        # Performance 3 Jahre
        p3y_val = hist['Close'].iloc[-750] if len(hist) > 750 else hist['Close'].iloc[0]
        
        return {
            "name": symbol.upper(),
            "price": round(cur, 2),
            "dist38": round(((cur/s38)-1)*100, 2),
            "dist60": round(((cur/s60)-1)*100, 2),
            "perf3y": round(((cur/p3y_val)-1)*100, 2)
        }
    except:
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    # Startwerte
    tickers = ["ABT", "BRK-B"]
    if request.method == 'POST':
        user_input = request.form.get('ticker')
        if user_input:
            tickers.insert(0, user_input.upper())

    results = []
    for s in tickers:
        data = get_data(s)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
