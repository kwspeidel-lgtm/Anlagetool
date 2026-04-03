import os
import yfinance as yf
import pandas as pd
from flask import Flask, render_template_string, request

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Anlagetool - Strategie-Check</title>
    <style>
        body { font-family: sans-serif; background: #0f1215; color: white; padding: 20px; }
        .container { max-width: 800px; margin: auto; background: #1a1e23; padding: 20px; border-radius: 10px; }
        input { width: 70%; padding: 12px; border-radius: 5px; border: none; background: #0b0d0f; color: white; }
        button { padding: 12px 20px; background: #f1c40f; color: black; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border-bottom: 1px solid #333; padding: 12px; text-align: right; }
        th:first-child, td:first-child { text-align: left; }
        .pos { color: #2ecc71; } .neg { color: #e74c3c; }
        textarea { width: 100%; height: 100px; background: #111; color: #888; border: 1px dashed #f1c40f; margin-top: 20px; padding: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Anlagetool - Strategie-Check</h1>
        <form method="POST">
            <input type="text" name="symbols" placeholder="WKNs/Ticker mit Komma (z.B. AAPL, A0RPWH.DE)" value="{{ last_input }}">
            <button type="submit">Daten laden</button>
        </form>
        {% if data %}
        <table>
            <tr><th>Symbol</th><th>Preis</th><th>1D %</th><th>1M %</th><th>1Y %</th></tr>
            {% for item in data %}
            <tr>
                <td><b>{{ item.symbol }}</b></td>
                <td>{{ "%.2f"|format(item.price) }}</td>
                <td class="{{ 'pos' if item.d1 >= 0 else 'neg' }}">{{ "%+.1f"|format(item.d1) }}%</td>
                <td class="{{ 'pos' if item.m1 >= 0 else 'neg' }}">{{ "%+.1f"|format(item.m1) }}%</td>
                <td class="{{ 'pos' if item.y1 >= 0 else 'neg' }}">{{ "%+.1f"|format(item.y1) }}%</td>
            </tr>
            {% endfor %}
        </table>
        <textarea id="kiText">{{ ki_string }}</textarea>
        <button style="width:100%; margin-top:10px; background:#34495e; color:white;" onclick="copyData()">Goldener Button: KI-Transfer kopieren</button>
        {% endif %}
    </div>
    <script>
        function copyData() {
            var t = document.getElementById("kiText");
            t.select(); document.execCommand("copy");
            alert("Daten kopiert! Jetzt ab in den KI-Chat damit.");
        }
    </script>
</body>
</html>
"""

def fetch(s):
    try:
        t = yf.Ticker(s)
        df = t.history(period="1y")
        if df.empty: return None
        cur = df['Close'].iloc[-1]
        d1 = ((cur / df['Close'].iloc[-2]) - 1) * 100 if len(df) > 1 else 0
        m1 = ((cur / df['Close'].iloc[-22]) - 1) * 100 if len(df) > 22 else 0
        y1 = ((cur / df['Close'].iloc[0]) - 1) * 100
        return {"symbol": s, "price": cur, "d1": d1, "m1": m1, "y1": y1}
    except: return None

@app.route("/", methods=["GET", "POST"])
def index():
    results, ki_s, last = [], "", ""
    if request.method == "POST":
        last = request.form.get("symbols", "")
        syms = [s.strip().upper() for s in last.split(",") if s.strip()]
        ki_s = "Strategie-Check für:\n"
        for s in syms:
            d = fetch(s)
            if d:
                results.append(d)
                ki_s += f"- {d['symbol']}: {d['price']:.2f} | 1D: {d['d1']:+.1f}% | 1M: {d['m1']:+.1f}% | 1Y: {d['y1']:+.1f}%\n"
        ki_s += "\nBitte analysiere diese Werte und gib eine Empfehlung."
    return render_template_string(HTML_TEMPLATE, data=results, ki_string=ki_s, last_input=last)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
