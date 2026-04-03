import os
from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def get_stock_analysis(isin):
    """
    Holt Daten über yfinance und berechnet RSI, SMA38 
    sowie die 3-Jahres-Performance manuell.
    """
    try:
        ticker = yf.Ticker(isin)
        # 3 Jahre Historie abrufen
        df = ticker.history(period="3y")
        
        if df.empty or len(df) < 40:
            return None
        
        current_price = df['Close'].iloc[-1]
        
        # --- Manuelle RSI-Berechnung (14 Tage) ---
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi_series = 100 - (100 / (1 + rs))
        rsi_val = rsi_series.iloc[-1]
        
        # --- SMA 38 Tage (Trend-Indikator) ---
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        sma38_diff = ((current_price / sma38) - 1) * 100
        
        # --- Performance-Zeiträume ---
        # 1 Jahr zurück (asof sucht den nächsten verfügbaren Kurs)
        one_year_ago = datetime.now() - timedelta(days=365)
        price_1y = df['Close'].asof(one_year_ago)
        perf_1y = ((current_price / price_1y) - 1) * 100
        
        # 3 Jahre (vom ersten Wert im 3y-Dataframe)
        price_3y_start = df['Close'].iloc[0]
        perf_3y = ((current_price / price_3y_start) - 1) * 100
        
        # Fundamentaldaten
        info = ticker.info
        
        return {
            "name": info.get('longName', 'N/A'),
            "isin": isin,
            "symbol": info.get('symbol', 'N/A'),
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else "N/A",
            "sma38_diff": round(sma38_diff, 2),
            "perf_1y": round(perf_1y, 1),
            "perf_3y": round(perf_3y, 1),
            "kgv": info.get('forwardPE', 'N/A'),
            "div": round((info.get('dividendYield', 0) or 0) * 100, 2)
        }
    except Exception as e:
        print(f"Fehler bei ISIN {isin}: {e}")
        return None

@app.route('/')
def index():
    # Deine Ziel-ISINs (Abbott und Berkshire)
    target_isins = ["US0028241000", "US0846707026"]
    
    results = []
    for isin in target_isins:
        data = get_stock_analysis(isin)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == '__main__':
    # Port dynamisch von Render beziehen, sonst 5000
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
