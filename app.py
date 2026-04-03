import yfinance as yf
import pandas as pd
import pandas_ta as ta # Für die RSI Berechnung
from datetime import datetime, timedelta

def expert_strategy_check(isins):
    results = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=3*365 + 100) # Puffer für Indikatoren
    
    for isin in isins:
        ticker = yf.Ticker(isin)
        hist = ticker.history(start=start_date)
        
        if hist.empty: continue
            
        # 1. Technische Indikatoren berechnen
        current_price = hist['Close'].iloc[-1]
        sma_38 = hist['Close'].rolling(window=38).mean().iloc[-1]
        sma_60 = hist['Close'].rolling(window=60).mean().iloc[-1]
        
        # RSI (14 Tage)
        hist['RSI'] = ta.rsi(hist['Close'], length=14)
        rsi_current = hist['RSI'].iloc[-1]
        
        # 2. Performance Zeiträume
        perf_1y = ((current_price / hist['Close'].asof(end_date - timedelta(days=365))) - 1) * 100
        perf_3y = ((current_price / hist['Close'].iloc[0]) - 1) * 100
        
        # 3. Fundamentaldaten & Stammdaten
        info = ticker.info
        
        results.append({
            "Name": info.get('longName', 'N/A')[:20], # Kürzen für Tabelle
            "Preis": round(current_price, 2),
            "RSI": round(rsi_current, 1),
            "Trend 38D": "UP" if current_price > sma_38 else "DOWN",
            "Trend 60D": "UP" if current_price > sma_60 else "DOWN",
            "1J %": round(perf_1y, 1),
            "3J %": round(perf_3y, 1),
            "KGV fwd": info.get('forwardPE', 'N/A'),
            "Div %": round((info.get('dividendYield', 0) or 0) * 100, 2)
        })
    
    return pd.DataFrame(results)

# Ausführung für deine Werte
meine_liste = ["US0028241000", "US0846707026"]
df_final = expert_strategy_check(meine_liste)
print(df_final.to_markdown(index=False))
