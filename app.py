import os
from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_analysis(isin):
    try:
        ticker = yf.Ticker(isin)
        df = ticker.history(period="3y")
        if df.empty or len(df) < 60:
            return None

        current_price = df['Close'].iloc[-1]
        df['RSI'] = calculate_rsi(df['Close'])
        rsi_val = df['RSI'].iloc[-1]
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        
        one_year_ago = datetime.now() - timedelta(days=365)
        price_1y = df['Close'].asof(one_year_ago)
        
        info = ticker.info
        return {
            "name": info.get('longName', 'N/A'),
            "isin": isin,
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else "N/A",
            "sma38_diff": round(((current_price / sma38) - 1) * 100, 2),
            "perf_1y": round(((current_price / price_1y) - 1) * 100, 1),
            "perf_3y": round(((current_price / df['Close'].iloc[0]) - 1) * 100, 1),
            "kgv": info.get('forwardPE', 'N/A')
        }
    except Exception as e:
        print(f"Error {isin}: {e}")
        return None

@app.route('/')
def index():
    target_isins = ["US0028241000", "US0846707026"]
    results = [get_stock_analysis(isin) for isin in target_isins]
    return render_template('index.html', stocks=[r for r in results if r])

if __name__ == '__main__':
    # WICHTIG: Port muss über Umgebungsvariable von Render kommen
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
