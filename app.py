from flask import Flask, render_template
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

app = Flask(__name__)

# Liste deiner ISINs
MEINE_WERTE = ["US0028241000", "US0846707026"]

@app.route('/')
def home():
    stock_data = []
    end_date = datetime.now()
    start_date_3y = end_date - timedelta(days=3*365)
    
    for isin in MEINE_WERTE:
        try:
            ticker = yf.Ticker(isin)
            # 3 Jahre Historie abrufen
            hist = ticker.history(start=start_date_3y)
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                
                # Gleitende Durchschnitte (SMA) berechnen
                sma38 = hist['Close'].rolling(window=38).mean().iloc[-1]
                sma60 = hist['Close'].rolling(window=60).mean().iloc[-1]
                
                # Abstände zu den Linien in Prozent
                dist38 = ((current_price / sma38) - 1) * 100
                dist60 = ((current_price / sma60) - 1) * 100
                
                # 3-Jahres Performance
                perf3y = ((current_price / hist['Close'].iloc[0]) - 1) * 100
                
                # Name aus den Info-Daten (oder ISIN als Fallback)
                name = ticker.info.get('longName', isin)
                
                stock_data.append({
                    "name": name,
                    "isin": isin,
                    "price": round(current_price, 2),
                    "dist38": round(dist38, 2),
                    "dist60": round(dist60, 2),
                    "perf3y": round(perf3y, 2)
                })
        except Exception as e:
            print(f"Fehler bei {isin}: {e}")
            
    # Hier wird die index.html aus dem templates-Ordner aufgerufen
    return render_template('index.html', stocks=stock_data)

if __name__ == "__main__":
    # Wichtig für Render: Port muss variabel sein
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
