from flask import Flask
import requests
import json
import os

app = Flask(__name__)

API_KEY = os.environ.get("API_FOOTBALL_KEY", "")
API_HOST = "v3.football.api-sports.io"

@app.route('/')
def home():
    url = f"https://{API_HOST}/fixtures"
    headers = {"x-apisports-key": API_KEY}
    params = {"league": 22, "season": 2026, "next": 10}
    try:
        r = requests.get(url, headers=headers, params=params, timeout=5)
        raw = r.json()
    except Exception as e:
        raw = {"error": str(e)}
    return f"<pre>{json.dumps(raw, indent=2)}</pre>"

if __name__ == '__main__':
    app.run(debug=True)
