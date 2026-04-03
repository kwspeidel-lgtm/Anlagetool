import os
from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def get_stock_analysis(isin):
    try:
        ticker = yf.Ticker(isin)
        # 3 Jahre Daten für den Langfrist-Check
        df = ticker.history(period="3y")
        if df.empty or len(df) < 20: return None
        
        current_price = df['Close'].iloc[-1]
        
        # Manuelle RSI-Berechnung (Stabil ohne Extra-Library)
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        
        # SMA 38 Tage Trend
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # Fundamentaldaten
        info = ticker.info
        
        return {
            "name": info.get('longName', 'N/A'),
            "isin": isin,
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else "N/A",
            "sma38_diff": round(((current_price / sma38) - 1) * 100, 2),
            "perf_3y": round(((current_price / df['Close'].iloc[0]) - 1) * 100, 1),
            "kgv": info.get('forwardPE', 'N/A'),
            "div": round((info.get('dividendYield', 0) or 0) * 100, 2)
        }
    except Exception as e:
        print(f"Fehler bei {isin}: {e}")
        return None

@app.route('/')
def index():
    # Deine Werte aus dem Strategie-Check
    target_isins = ["US0028241000", "US0846707026"]
    results = [get_stock_analysis(isin) for isin in target_isins]
    # Nur erfolgreiche Abrufe anzeigen
    valid_results = [r for r in results if r is not None]
    return render_template('index.html', stocks=valid_results)

if __name__ == '__main__':
    # WICHTIG: Render braucht den dynamischen Port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
