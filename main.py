from flask import Flask
import requests
import json

app = Flask(__name__)

@app.route('/')
def home():
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    try:
        r = requests.get(url, timeout=5)
        raw = r.json()
    except Exception as e:
        raw = {"error": str(e)}
    return f"<pre>{json.dumps(raw, indent=2)}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
