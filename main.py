from flask import Flask
import requests
import json
import os

app = Flask(__name__)

API_KEY = os.environ.get("FOOTBALL_DATA_KEY", "")

@app.route('/')
def home():
    url = "https://api.football-data.org/v4/competitions/2000/matches"
    headers = {"X-Auth-Token": API_KEY}
    params = {"status": "SCHEDULED"}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        raw = r.json()
    except Exception as e:
        raw = {"error": str(e)}
    return f"<pre>{json.dumps(raw, indent=2)}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
