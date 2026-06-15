from flask import Flask, render_template_string
import requests
import datetime

app = Flask(__name__)

# FIFA Rankings Ιούνιος 2026
FIFA_RANKINGS = {
    "Argentina": 1, "France": 2, "England": 3, "Belgium": 4,
    "Brazil": 5, "Portugal": 6, "Netherlands": 7, "Spain": 8,
    "Croatia": 9, "Italy": 10, "Morocco": 11, "Germany": 12,
    "Colombia": 13, "Japan": 14, "Senegal": 15, "United States": 16,
    "Uruguay": 17, "Mexico": 18, "Switzerland": 19, "Denmark": 20,
    "South Korea": 21, "Ecuador": 22, "Australia": 23, "Canada": 24,
    "Poland": 25, "Serbia": 26, "Austria": 27, "Hungary": 28,
    "Tunisia": 29, "Iran": 30, "Algeria": 31, "Czech Republic": 32,
    "Ukraine": 33, "Chile": 34, "Cameroon": 35, "Wales": 36,
    "Slovakia": 37, "Venezuela": 38, "Turkey": 39, "Romania": 40,
    "Egypt": 41, "Peru": 42, "Norway": 43, "Nigeria": 44,
    "Paraguay": 45, "Ivory Coast": 46, "New Zealand": 47,
    "Qatar": 48, "Saudi Arabia": 56, "South Africa": 60,
    "Uzbekistan": 62, "Cape Verde": 70, "Bolivia": 75,
    "Indonesia": 120, "Panama": 80, "Guatemala": 90,
    "Honduras": 85, "Jamaica": 95, "Costa Rica": 65,
    "Iraq": 68, "Thailand": 115, "China": 80,
}

def get_ranking(team_name):
    # Fuzzy match για διαφορετικά ονόματα
    for key, rank in FIFA_RANKINGS.items():
        if key.lower() in team_name.lower() or team_name.lower() in key.lower():
            return rank
    return 60  # default αν δεν βρεθεί

def calculate_prediction(home_name, away_name):
    home_rank = get_ranking(home_name)
    away_rank = get_ranking(away_name)

    # Χαμηλότερο ranking = καλύτερη ομάδα
    home_strength = (100 / home_rank) * 1.10  # home advantage
    away_strength = (100 / away_rank)

    total = home_strength + away_strength
    home_win = round((home_strength / total) * 80, 1)
    away_win = round((away_strength / total) * 80, 1)
    draw = round(100 - home_win - away_win, 1)

    surprise = round(min(100.0, abs(home_rank - away_rank) / max(home_rank, away_rank) * 100), 1)

    return home_win, away_win, draw, surprise

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

            home_name = home.get("team", {}).get("displayName", "?")
            away_name = away.get("team", {}).get("displayName", "?")

            home_prob, away_prob, draw_prob, surprise = calculate_prediction(home_name, away_name)

            matches.append({
                "home": home_name,
                "away": away_name,
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
                "home_rank": get_ranking(home_name),
                "away_rank": get_ranking(away_name),
            })
        return matches
    except:
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
        .team-rank { font-size: 10px; color: #ffd700; margin-top: 2px; }
        .score { font-size: 28px; font-weight: bold; color: #ffd700; padding: 0 12px; }
        .vs { font-size: 18px; color: #ffd700; font-weight: bold; padding: 0 12px; }
        .probs { display: flex; gap: 6px; margin-bottom: 10px; }
        .prob-bar { flex: 1; background: rgba(255,255,255,0.05); border-radius: 8px; padding: 8px 4px; text-align: center; }
        .prob-bar .label { font-size: 9px; color: #aaa; margin-bottom: 3px; }
        .prob-bar .value { font-size: 16px; font-weight: bold; color: #00f2fe; }
        .surprise { display: flex; align-items: center; justify-content: space-between; padding: 8px 12px; border-radius: 8px; font-size: 12px; font-weight: bold; }
        .surprise.high { background: linear-gradient(135deg, #e74c3c, #c0392b); box-shadow: 0 0 10px rgba(231,76,60,0.4); }
        .surprise.low { background: linear-gradient(135deg, #27ae60, #2ecc71); }
        footer { text-align: center; margin-top: 30px; color: #444; font-size: 10px; }
    </style>
</head>
<body>
<header>
    <h1>⚽ Weltmeisterschaft 2026</h1>
    <p>Live Προγνωστικά βάσει FIFA Rankings</p>
</header>
<div class="grid">
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
            <div class="team-rank">FIFA #{{ m.home_rank }}</div>
        </div>
        {% if m.state == "in" or m.state == "post" %}
            <div class="score">{{ m.home_score }} - {{ m.away_score }}</div>
        {% else %}
            <div class="vs">VS</div>
        {% endif %}
        <div class="team">
            <img src="{{ m.away_logo }}" alt="{{ m.away }}">
            <div class="team-name">{{ m.away }}</div>
            <div class="team-rank">FIFA #{{ m.away_rank }}</div>
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
</div>
<footer><p>Powered by ESPN & FIFA Rankings • Weltmeisterschaft 2026</p></footer>
</body>
</html>
"""

@app.route('/')
def home():
    matches = get_matches()
    return render_template_string(HTML, matches=matches)

if __name__ == '__main__':
    app.run(debug=True)
