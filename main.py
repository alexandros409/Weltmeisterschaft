from flask import Flask, render_template_string
import requests
import datetime

app = Flask(__name__)

def get_matches():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    try:
        r = requests.get(url, timeout=5)
        data = r.json()
        events = data.get("events", [])
        matches = []
        for e in events:
            comp = e.get("competitions", [{}])[0]
            competitors = comp.get("competitors", [])
            if len(competitors) < 2:
                continue
            home = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
            away = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
            status = e.get("status", {}).get("type", {})
            date_raw = e.get("date", "")
            try:
                dt = datetime.datetime.fromisoformat(date_raw.replace("Z", "+00:00"))
                date_str = dt.strftime("%d/%m %H:%M")
            except:
                date_str = "TBD"
            home_record = home.get("records", [{}])[0] if home.get("records") else {}
            away_record = away.get("records", [{}])[0] if away.get("records") else {}
            def parse_record(rec):
                summary = rec.get("summary", "0-0-0")
                parts = summary.split("-")
                try:
                    w, l, d = int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0
                except:
                    w, l, d = 0, 0, 0
                return w, l, d
            hw, hl, hd = parse_record(home_record)
            aw, al, ad = parse_record(away_record)
            home_power = (hw * 3 + hd + 1) * 1.10
            away_power = (aw * 3 + ad + 1)
            total = home_power + away_power
            home_prob = round((home_power / total) * 85, 1)
            away_prob = round((away_power / total) * 85, 1)
            draw_prob = round(100 - home_prob - away_prob, 1)
            surprise = round(min(100.0, abs(home_prob - away_prob) / 2), 1)
            matches.append({
                "home": home.get("team", {}).get("displayName", "?"),
                "away": away.get("team", {}).get("displayName", "?"),
                "home_logo": home.get("team", {}).get("logo", ""),
                "away_logo": away.get("team", {}).get("logo", ""),
                "home_score": home.get("score", "-"),
                "away_score": away.get("score", "-"),
                "date": date_str,
                "status": status.get("description", ""),
                "state": status.get("state", "pre"),
                "home_prob": home_prob,
                "away_prob": away_prob,
                "draw_prob": draw_prob,
                "surprise": surprise,
            })
        return matches
    except Exception as ex:
        return []

HTML = """
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>⚽ Weltmeisterschaft 2026</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: Arial, sans-serif; background: #0A1128; color: #fff; padding: 16px; }
        header { text-align: center; padding: 24px 0 20px; }
        header h1 { font-size: 22px; color: #00f2fe; }
        header p { color: #aaa; font-size: 12px; margin-top: 4px; }
        .grid { display: flex; flex-direction: column; gap: 14px; max-width: 600px; margin: 0 auto; }
        .card { background: #101F42; border-radius: 14px; padding: 16px; border: 1px solid rgba(255,255,255,0.08); }
        .meta { font-size: 11px; color: #aaa; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; display: flex; justify-content: space-between; }
        .live-badge { color: #e74c3c; font-weight: bold; animation: pulse 1s infinite; }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }
        .teams { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
        .team { text-align: center; flex: 1; }
        .team img { width: 44px; height: 44px; object-fit: contain; }
        .team-name { font-size: 11px; font-weight: bold; margin-top: 5px; color: #e0e6ed; }
        .score { font-size: 28px; font-weight: bold; color: #ffd700; padding: 0 12px; }
        .vs { font-size: 18px; color: #ffd700; font-weight: bold; padding: 0 12px; }
        .probs { display: flex; gap: 6px; margin-bottom: 10px; }
        .prob-bar { flex: 1; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px 4px; text-align: center; }
        .prob-bar .label { font-size: 9px; color: #aaa; margin-bottom: 3px; }
        .prob-bar .value { font-size: 16px; font-weight: bold; color: #00f2fe; }
        .surprise { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        .surprise.high { background: linear-gradient(135deg, #e74c3c, #c0392b); box-shadow: 0 0 10px rgba(231,76,60,0.4); }
        .surprise.low { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .no-matches { text-align: center; padding: 50px 20px; color: #aaa; }
        .no-matches h2 { color: #ffd700; margin-bottom: 8px; }
        footer { text-align: center; margin-top: 30px; color: #444; font-size: 10px; }
    </style>
</head>
<body>
<header>
    <h1>⚽ Weltmeisterschaft 2026</h1>
    <p>Live Προγνωστικά • Σημερινοί Αγώνες</p>
</header>
<div class="grid">
{% if matches %}
  {% for m in matches %}
  <div class="card">
    <div class="meta">
      <span>{{ m.date }}</span>
      {% if m.state == "in" %}
        <span class="live-badge">🔴 LIVE</span>
      {% else %}
        <span>{{ m.status }}</span>
      {% endif %}
    </div>
    <div class="teams">
      <div class="team">
        <img src="{{ m.home_logo }}" alt="{{ m.home }}">
        <div class="team-name">{{ m.home }}</div>
      </div>
      {% if m.state == "in" or m.state == "post" %}
        <div class="score">{{ m.home_score }} - {{ m.away_score }}</div>
      {% else %}
        <div class="vs">VS</div>
      {% endif %}
      <div class="team">
        <img src="{{ m.away_logo }}" alt="{{ m.away }}">
        <div class="team-name">{{ m.away }}</div>
      </div>
    </div>
    <div class="probs">
      <div class="prob-bar">
        <div class="label">{{ m.home }}</div>
        <div class="value">{{ m.home_prob }}%</div>
      </div>
      <div class="prob-bar">
        <div class="label">Ισοπαλία</div>
        <div class="value">{{ m.draw_prob }}%</div>
      </div>
      <div class="prob-bar">
        <div class="label">{{ m.away }}</div>
        <div class="value">{{ m.away_prob }}%</div>
      </div>
    </div>
    <div class="surprise {{ 'high' if m.surprise >= 40 else 'low' }}">
      <span>⚡ Δείκτης Έκπληξης</span>
      <span>{{ m.surprise }}%</span>
    </div>
  </div>
  {% endfor %}
{% else %}
  <div class="no-matches">
    <h2>Δεν βρέθηκαν αγώνες</h2>
    <p>Δοκίμασε αργότερα.</p>
  </div>
{% endif %}
</div>
<footer><p>Powered by ESPN • Weltmeisterschaft 2026</p></footer>
</body>
</html>
"""

@app.route('/')
def home():
    matches = get_matches()
    return render_template_string(HTML, matches=matches)

if __name__ == '__main__':
    app.run(debug=True)
