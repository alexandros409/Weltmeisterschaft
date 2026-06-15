from flask import Flask, render_template_string
import requests
import os
import datetime

app = Flask(__name__)

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"
WC_LEAGUE_ID = 1

def get_fixtures():
    url = f"https://{API_HOST}/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": WC_LEAGUE_ID, "season": 2026, "next": 10}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        return r.json().get("response", [])
    except:
        return []

def get_team_stats(team_id):
    url = f"https://{API_HOST}/teams/statistics"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": WC_LEAGUE_ID, "season": 2026, "team": team_id}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        return r.json().get("response", {})
    except:
        return {}

def calculate_prediction(home_stats, away_stats):
    def safe_avg(stats, direction):
        try:
            val = stats.get("goals", {}).get(direction, {}).get("average", {}).get("total", "0")
            return float(val) if val else 0.0
        except:
            return 0.0

    home_attack = safe_avg(home_stats, "for")
    home_defense = safe_avg(home_stats, "against")
    away_attack = safe_avg(away_stats, "for")
    away_defense = safe_avg(away_stats, "against")

    home_power = (home_attack + 1) / (home_defense + 0.5) * 1.10
    away_power = (away_attack + 1) / (away_defense + 0.5)

    total = home_power + away_power
    home_prob = (home_power / total) * 85
    away_prob = (away_power / total) * 85
    draw_prob = round(100 - home_prob - away_prob, 1)

    surprise = min(100.0, abs(home_prob - 50) / 50 * 100)

    return round(home_prob, 1), round(away_prob, 1), max(0, draw_prob), round(surprise, 1)

HTML = """
<!DOCTYPE html>
<html lang="el">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>⚽ Weltmeisterschaft 2026</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: Arial, sans-serif;
            background: #0A1128;
            color: #fff;
            min-height: 100vh;
            padding: 20px;
        }
        header {
            text-align: center;
            padding: 30px 0 24px;
        }
        header h1 { font-size: 24px; color: #00f2fe; }
        header p { color: #aaa; font-size: 12px; margin-top: 6px; }
        .grid {
            display: flex;
            flex-direction: column;
            gap: 16px;
            max-width: 600px;
            margin: 0 auto;
        }
        .card {
            background: #101F42;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid rgba(255,255,255,0.08);
        }
        .match-date {
            font-size: 11px;
            color: #aaa;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .teams {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 16px;
        }
        .team { text-align: center; flex: 1; }
        .team img { width: 48px; height: 48px; object-fit: contain; }
        .team-name { font-size: 12px; font-weight: bold; margin-top: 6px; color: #e0e6ed; }
        .vs { font-size: 20px; color: #ffd700; font-weight: bold; padding: 0 10px; }
        .probs { display: flex; gap: 8px; margin-bottom: 12px; }
        .prob-bar {
            flex: 1;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            padding: 10px 6px;
            text-align: center;
        }
        .prob-bar .label { font-size: 10px; color: #aaa; margin-bottom: 4px; }
        .prob-bar .value { font-size: 18px; font-weight: bold; color: #00f2fe; }
        .surprise {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: bold;
        }
        .surprise.high {
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            box-shadow: 0 0 12px rgba(231,76,60,0.4);
        }
        .surprise.low { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        .no-fixtures { text-align: center; padding: 60px 20px; color: #aaa; }
        .no-fixtures h2 { color: #ffd700; margin-bottom: 10px; }
        footer { text-align: center; margin-top: 40px; color: #444; font-size: 11px; }
    </style>
</head>
<body>
<header>
    <h1>⚽ Weltmeisterschaft 2026</h1>
    <p>Live Προγνωστικά • Επόμενοι Αγώνες</p>
</header>
<div class="grid">
{% if fixtures %}
  {% for f in fixtures %}
  <div class="card">
    <div class="match-date">{{ f.date }} • {{ f.venue }}</div>
    <div class="teams">
      <div class="team">
        <img src="{{ f.home_logo }}" alt="{{ f.home }}">
        <div class="team-name">{{ f.home }}</div>
      </div>
      <div class="vs">VS</div>
      <div class="team">
        <img src="{{ f.away_logo }}" alt="{{ f.away }}">
        <div class="team-name">{{ f.away }}</div>
      </div>
    </div>
    <div class="probs">
      <div class="prob-bar">
        <div class="label">{{ f.home }}</div>
        <div class="value">{{ f.home_prob }}%</div>
      </div>
      <div class="prob-bar">
        <div class="label">Ισοπαλία</div>
        <div class="value">{{ f.draw_prob }}%</div>
      </div>
      <div class="prob-bar">
        <div class="label">{{ f.away }}</div>
        <div class="value">{{ f.away_prob }}%</div>
      </div>
    </div>
    <div class="surprise {{ 'high' if f.surprise >= 60 else 'low' }}">
      <span>⚡ Δείκτης Έκπληξης</span>
      <span>{{ f.surprise }}%</span>
    </div>
  </div>
  {% endfor %}
{% else %}
  <div class="no-fixtures">
    <h2>Δεν βρέθηκαν αγώνες</h2>
    <p>Δοκίμασε αργότερα.</p>
  </div>
{% endif %}
</div>
<footer><p>Powered by API-Football • Weltmeisterschaft 2026</p></footer>
</body>
</html>
"""

@app.route('/')
def home():
    fixtures_raw = get_fixtures()
    fixtures = []
    for f in fixtures_raw[:8]:
        home_id = f["teams"]["home"]["id"]
        away_id = f["teams"]["away"]["id"]
        home_stats = get_team_stats(home_id)
        away_stats = get_team_stats(away_id)
        home_prob, away_prob, draw_prob, surprise = calculate_prediction(home_stats, away_stats)
        try:
            dt = datetime.datetime.fromisoformat(f["fixture"]["date"].replace("Z", "+00:00"))
            date_str = dt.strftime("%d/%m %H:%M")
        except:
            date_str = "TBD"
        fixtures.append({
            "home": f["teams"]["home"]["name"],
            "away": f["teams"]["away"]["name"],
            "home_logo": f["teams"]["home"]["logo"],
            "away_logo": f["teams"]["away"]["logo"],
            "date": date_str,
            "venue": f["fixture"]["venue"]["name"] or "TBD",
            "home_prob": home_prob,
            "away_prob": away_prob,
            "draw_prob": draw_prob,
            "surprise": surprise,
        })
    return render_template_string(HTML, fixtures=fixtures)

if __name__ == '__main__':
    app.run(debug=True)
