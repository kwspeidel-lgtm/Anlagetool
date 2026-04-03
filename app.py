from flask import Flask, render_template
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

def calculate_rsi(series, period=14):
    """Berechnet den Relative Strength Index ohne externe Library."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_stock_analysis(isin):
    """Ruft Daten ab und berechnet technische Faktoren (38D, 3Y, RSI)."""
    try:
        ticker = yf.Ticker(isin)
        # 3 Jahre Daten für den Langfrist-Check abrufen
        df = ticker.history(period="3y")
        
        if df.empty or len(df) < 60:
            return None

        # Aktueller Preis
        current_price = df['Close'].iloc[-1]
        
        # --- Technische Indikatoren ---
        # RSI (14 Tage)
        df['RSI'] = calculate_rsi(df['Close'])
        rsi_val = df['RSI'].iloc[-1]
        
        # Gleitender Durchschnitt (38 Tage)
        sma38 = df['Close'].rolling(window=38).mean().iloc[-1]
        sma38_diff = ((current_price / sma38) - 1) * 100
        
        # --- Zeitvergleiche ---
        # 1 Jahr Performance
        one_year_ago = datetime.now() - timedelta(days=365)
        price_1y = df['Close'].asof(one_year_ago)
        perf_1y = ((current_price / price_1y) - 1) * 100
        
        # 3 Jahre Performance (Start des Dataframes)
        perf_3y = ((current_price / df['Close'].iloc[0]) - 1) * 100
        
        # --- Stammdaten & Kennzahlen ---
        info = ticker.info
        name = info.get('longName', 'N/A')
        kgv = info.get('forwardPE', 'N/A')
        div = (info.get('dividendYield', 0) or 0) * 100

        return {
            "name": name,
            "isin": isin,
            "price": round(current_price, 2),
            "rsi": round(rsi_val, 1) if not np.isnan(rsi_val) else "N/A",
            "sma38_diff": round(sma38_diff, 2),
            "perf_1y": round(perf_1y, 1),
            "perf_3y": round(perf_3y, 1),
            "kgv": kgv,
            "div": round(div, 2)
        }
    except Exception as e:
        print(f"Fehler bei ISIN {isin}: {e}")
        return None

@app.route('/')
def index():
    # Deine Ziel-ISINs für den Strategie-Check
    target_isins = ["US0028241000", "US0846707026"]
    
    results = []
    for isin in target_isins:
        data = get_stock_analysis(isin)
        if data:
            results.append(data)
            
    return render_template('index.html', stocks=results)

if __name__ == '__main__':
    # Port 5000 für lokale Tests, Render nutzt Umgebungsvariablen
    app.run(host='0.0.0.0', port=5000, debug=False)
