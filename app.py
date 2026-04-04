import yfinance as yf
from flask import Flask, render_template_string, request, redirect
import pandas as pd
from PIL import Image
import pytesseract
import re
import io

app = Flask(__name__)
# Speicher für die aktuelle Session (RAM)
stored_results = []

# ERWEITERTE WKN-DATENBANK (Otto-Normal-Dolmetscher)
WKN_DB = {
    # Deutsche Standards
    "716460": "SAP.DE", "519000": "BMW.DE", "710000": "MBG.DE",
    "766403": "VOW3.DE", "840400": "ALV.DE", "581005": "DTE.DE",
    "RHM888": "RHM.DE", "BASF11": "BAS.DE", "BAY001": "BAYN.DE",
    "A0D9PT": "MTX.DE", "ENAG99": "EOAN.DE", "CBK100": "CBK.DE",
    # US Tech
    "A1EWWW": "META", "A142N1": "AMZN", "A1CX3T": "TSLA",
    "847905": "MSFT", "A0YEDG": "AAPL", "918422": "NVDA",
    "A14Y6H": "GOOGL", "865985": "NFLX",
    # Union Investment (Beispiele zur Erkennung)
    "849100": "UR02.DE", # UniRak
    "975020": "UN01.DE"  # UniGlobal
}

def get_smart_data(input_val):
    """Zentrale Recheneinheit: Holt Daten & berechnet Smart-Score."""
    t = input_val.strip().upper()
    # 1. WKN zu Ticker übersetzen
    search_t = WKN_DB.get(t, t)
    
    # 2. Automatik für Ticker ohne Börsenplatz
    if "." not in search_t and len(search_t) <= 4:
        us_tech = ["META", "AAPL", "MSFT", "TSLA", "NVDA", "AMZN", "GOOGL", "NFLX"]
        search_t = search_t if search_t in us_tech else f"{search_t}.DE"

    try:
        stock = yf.Ticker(search_t)
        # 60 Tage reichen für SMA38 + RSI14
        df = stock.history(period="60d")
        if df.empty or len(df) < 38: return None
        
        curr = df['Close'].iloc[-1]
        sma = df['Close'].rolling(window=38).mean().iloc[-1]
        
        # RSI 14 Berechnung
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean().iloc[-1]
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean().iloc[-1]
        rsi = round(100 - (100 / (1 + (gain/loss))), 2)
        
        # SMART-SCORE LOGIK (0-10)
        score = 0
        if rsi < 30: score += 6 # Massiv überverkauft
        elif rsi < 40: score += 4
        elif rsi > 70: score -= 2 # Heißgelaufen
        
        # Trend-Punkte (Abstand zu SMA38)
        diff = (curr / sma) - 1
        if -0.05 < diff < 0: score += 4 # Perfekte Rebound-Zone
        elif 0 < diff < 0.05: score += 2 # Trendbestätigung
        
        return {
            'ticker': search_t.replace(".DE", ""), 
            'price': f"{curr:.2f}",
            'rsi': rsi, 
            'score': max(0, min(10, score)), 
            'status': "OVER" if curr > sma else "UNDER"
        }
    except: return None

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VISUAL Terminal 2026</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
    <style>
        body { font-family: sans-serif; background: #0a0a0a; color: #eee; padding: 10px; text-align: center; }
        .container { max-width: 450px; margin: auto; }
        .upload-area { 
            background: #161616; border: 3px dashed #ffd700; padding: 25px; 
            border-radius: 20px; margin-bottom: 20px; cursor: pointer;
            transition: 0.3s;
        }
        .upload-area:active { transform: scale(0.95); background: #222; }
        .card { 
            background: #161616; padding: 15px; margin-bottom: 8px; border-radius: 12px; 
            display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #333; 
        }
        .gold-card { border-left: 5px solid #ffd700 !important; background: linear-gradient(90deg, #161616, #2a2400); }
        .score-box { background: #222; padding: 8px; border-radius: 10px; min-width: 45px; border: 1px solid #ffd700; }
        .btn-clear { color: #444; text-decoration: none; font-size: 0.8em; margin-top: 20px; display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h2 style="color:#ffd700; margin-bottom:5px;">VISUAL TERMINAL 🚀</h2>
        <p style="font-size:0.7em; color:#888; margin-bottom:20px;">WKN-CHECK & BILD-ANALYSE</p>
        
        <div class="upload-area" onclick="document.getElementById('file-input').click()">
            <div style="font-size: 40px;">📸</div>
            <strong>SCREENSHOT HOCHLADEN</strong>
            <form action="/upload" method="POST" enctype="multipart/form-data" id="upload-form">
                <input type="file" name="file" id="file-input" style="display:none" onchange="document.getElementById('upload-form').submit()">
            </form>
        </div>

        <form action="/manual" method="POST" style="margin-bottom:20px;">
            <input type="text" name="ticker" placeholder="WKN oder Kürzel..." style="width:65%; padding:12px; border-radius:10px; border:1px solid #333; background:#111; color:white; font-size:16px;">
            <button type="submit" style="padding:12px 20px; border-radius:10px; background:#ffd700; color:black; border:none; font-weight:bold;">+</button>
        </form>

        <div id="results">
            {% for s in stocks %}
            <div class="card {{ 'gold-card' if s.score >= 7 else '' }}">
                <div style="text-align: left;">
                    <strong style="font-size:1.2em; color:white;">{{ s.ticker }}</strong><br>
                    <small style="color:#999;">{{ s.price }}€ | RSI: {{ s.rsi }}</small><br>
                    <small style="color:{{ '#00ff88' if s.status == 'OVER' else '#ff4d4d' }}; font-weight:bold;">{{ s.status }} SMA38</small>
                </div>
                <div class="score-box">
                    <div style="font-size: 0.6em; color: #888;">SCORE</div>
                    <div style="font-size: 1.4em; font-weight: bold; color: #ffd700;">{{ s.score }}</div>
                </div>
            </div>
            {% endfor %}
        </div>
        
        <a href="/clear" class="btn-clear">TERMINAL LEEREN</a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, stocks=stored_results)

@app.route('/manual', methods=['POST'])
def manual():
    global stored_results
    val = request.form.get('ticker', '').upper().strip()
    if val:
        res = get_smart_data(val)
        if res and not any(x['ticker'] == res['ticker'] for x in stored_results):
            stored_results.insert(0, res)
    return redirect('/')

@app.route('/upload', methods=['POST'])
def upload():
    global stored_results
    if 'file' not in request.files: return redirect('/')
    file = request.files['file']
    if file:
        try:
            img = Image.open(io.BytesIO(file.read()))
            # Text aus Screenshot lesen
            text = pytesseract.image_to_string(img)
            # Suche nach 6-stelligen WKNs (Großbuchstaben + Zahlen)
            found = re.findall(r'\b[A-Z0-9]{6}\b', text)
            
            for f in found:
                res = get_smart_data(f)
                if res and not any(x['ticker'] == res['ticker'] for x in stored_results):
                    stored_results.insert(0, res)
        except: pass
    return redirect('/')

@app.route('/clear')
def clear():
    global stored_results
    stored_results = []
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
