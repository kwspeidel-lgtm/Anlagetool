from flask import Flask, render_template, request
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime, timedelta

app = Flask(__name__)

def get_strategy_data(isin):
    try:
        ticker = yf.Ticker(isin)
        # 3 Jahre Daten abrufen + Puffer für Indikatoren
        df = ticker.history(period="3y")
        
        if df.empty:
            return None

        # --- Technische Indikatoren ---
        # RSI 14 Tage
        df['RSI'] = ta.rsi(df['Close'], length=14)
        rsi_val = df['RSI'].iloc[-1]
        
        # Gleitende Durchschnitte (SMA)
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        sma60 = df['Close'].rolling(window=60).mean().iloc[-1]
        
        current_price = df['Close'].iloc[-1]
        
        # --- Performance & Fundamentals ---
        perf_1y = ((current_price / df['Close'].asof(datetime.now() - timedelta(days=365))) - 1) * 100
        perf_3y = ((current_price / df['Close'].iloc[0]) - 1) * 100
        
        info = ticker.info
        
        return {
            "name": info.get('longName', 'N/A'),
            "symbol": info.get('symbol', 'N/A'),
            "isin": isin,
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 1) if not pd.isna(rsi_val) else "N/A",
            "sma38_diff": round(((current_price / sma38) - 1) * 100, 2),
            "sma60_diff": round(((current_price / sma60) - 1) * 100, 2),
            "perf_1y": round(perf_1y, 1),
            "perf_3y": round(perf_3y, 1),
            "kgv": info.get('forwardPE', 'N/A'),
            "div": round((info.get('dividendYield', 0) or 0) * 100, 2)
        }
    except Exception as e:
        print(f"Fehler bei {isin}: {e}")
        return None

@app.route('/')
def index():
    # Deine Liste aus dem Strategie-Check
    isins = ["US0028241000", "US0846707026"]
    stock_results = []
    
    for isin in isins:
        data = get_strategy_data(isin)
        if data:
            stock_results.append(data)
            
    return render_template('index.html', stocks=stock_results)

if __name__ == '__main__':
    app.run(debug=True)
