from flask import Flask, jsonify, render_template_string, send_from_directory
import json
import os

app = Flask(__name__)
# Ορίζουμε ρητά την εφαρμογή ως 'app' στο global scope για να τη βρίσκει αμέσως η Vercel
app = app  

DATA_FILE = 'database.json'

def load_data():
    if not os.path.exists(DATA_FILE):
        mock_data = {
            "teams": {
                "1": {"name": "Real Madrid", "attack": 2.8, "defense": 0.9, "fifa": 2, "form": 85},
                "2": {"name": "Bayern Munich", "attack": 2.5, "defense": 1.1, "fifa": 6, "form": 75}
            },
            "matches": [
                {"match_id": 42, "home_id": "1", "away_id": "2", "weight": 1.5}
            ],
            "news": [
                {"match_id": 42, "team_id": "1", "headline": "Real Madrid captain suffered a severe hamstring injury and is out!", "sentiment": -0.65, "weight": 2.3},
                {"match_id": 42, "team_id": "1", "headline": "Tactics update: Real Madrid thin on defense options", "sentiment": -0.20, "weight": 1.1},
                {"match_id": 42, "team_id": "2", "headline": "Bayern Munich morale is sky high after training camp", "sentiment": 0.40, "weight": 1.3}
            ]
        }
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(mock_data, f, indent=4)
    
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

@app.route('/')
def home():
    data = load_data()
    match = data["matches"][0]
    home_team = data["teams"][match["home_id"]]
    away_team = data["teams"][match["away_id"]]
    
    home_base = (home_team["attack"] / home_team["defense"]) + (100 / home_team["fifa"])
    away_base = (away_team["attack"] / away_team["defense"]) + (100 / away_team["fifa"])
    home_base *= 1.10 
    
    home_form_factor = 1.0 + ((home_team["form"] - 50) / 100)
    away_form_factor = 1.0 + ((away_team["form"] - 50) / 100)
    
    home_power = home_base * home_form_factor
    away_power = away_base * away_form_factor
    
    home_news_impact = sum(n["sentiment"] * n["weight"] for n in data["news"] if n["match_id"] == match["match_id"] and n["team_id"] == match["home_id"])
    away_news_impact = sum(n["sentiment"] * n["weight"] for n in data["news"] if n["match_id"] == match["match_id"] and n["team_id"] == match["away_id"])
    
    home_final = max(0.1, home_power + home_news_impact)
    away_final = max(0.1, away_power + away_news_impact)
    
    total_power = home_final + away_final
    home_prob = (home_final / total_power) * 100
    away_prob = (away_final / total_power) * 100
    
    is_home_favorite = home_base > away_base
    surprise_index = 0.0
    if is_home_favorite:
        base_prob_home = (home_base / (home_base + away_base)) * 100
        if home_prob < base_prob_home:
            surprise_index = ((base_prob_home - home_prob) / base_prob_home) * 100
    else:
        base_prob_away = (away_base / (home_base + away_base)) * 100
        if away_prob < base_prob_away:
            surprise_index = ((base_prob_away - away_prob) / base_prob_away) * 100
            
    surprise_index = min(100.0, max(0.0, surprise_index * match["weight"]))

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Prediction & Surprise Index App</title>
        <meta charset="utf-8">
        <link rel="icon" type="image/svg+xml" href="/static/icon.svg">
        <style>
            body { font-family: Arial, sans-serif; background-color: #0A1128; text-align: center; padding: 50px; color: #ffffff; }
            .card { background: #101F42; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); display: inline-block; max-width: 500px; width: 100%; border: 1px solid rgba(255,255,255,0.1); }
            .icon-container { margin-bottom: 20px; }
            .icon-container img { width: 80px; height: 80px; }
            h1 { color: #00f2fe; margin-top: 0; font-size: 24px; }
            h2 { color: #ffd700; font-size: 22px; }
            hr { border: 0; height: 1px; background: rgba(255,255,255,0.1); margin: 20px 0; }
            .prob { font-size: 20px; font-weight: bold; margin: 15px 0; color: #e0e6ed; }
            .alert-box { background: linear-gradient(135deg, #e74c3c, #c0392b); color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-weight: bold; box-shadow: 0 0 15px rgba(231,76,60,0.5); }
            .normal-box { background: linear-gradient(135deg, #2ecc71, #27ae60); color: white; padding: 15px; border-radius: 10px; margin-top: 20px; font-weight: bold; }
            .surprise-text { color: #00f2fe; font-size: 24px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="card">
            <div class="icon-container">
                <img src="/static/icon.svg" alt="App Icon">
            </div>
            <h1>📊 Τελική Έκδοση Προγνωστικών</h1>
            <h2>{{ home_name }} vs {{ away_name }}</h2>
            <hr>
            <p class="prob">🏠 Πιθανότητα {{ home_name }}: {{ "%.1f"|format(home_prob) }}%</p>
            <p class="prob">🚀 Πιθανότητα {{ away_name }}: {{ "%.1f"|format(away_prob) }}%</p>
            <hr>
            <h3>⚠️ Δείκτης Έκπληξης: <span class="surprise-text">{{ "%.1f"|format(surprise_index) }}%</span></h3>
            
            {% if surprise_index >= 70.0 %}
                <div class="alert-box">
                    🚨 [PUSH NOTIFICATION TRIGGERED]<br>
                    Πιθανή Έκπληξη στο Μουντιάλ! Οι τελευταίες ειδήσεις ανατρέπουν τα δεδομένα!
                </div>
            {% else %}
                <div class="normal-box">
                    ✅ Σταθερή ροή αγώνα. Δεν ανιχνεύτηκε ακραία τάση έκπληξης.
                </div>
            {% endif %}
        </div>
    </body>
    </html>
    """
    return render_template_string(
        html_template, 
        home_name=home_team["name"], away_name=away_team["name"],
        home_prob=home_prob, away_prob=away_prob, surprise_index=surprise_index
    )

if __name__ == '__main__':
    app.run(debug=True)
