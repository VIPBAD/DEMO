# server.py
from flask import Flask, request, jsonify, render_template
import requests
import os
from functools import lru_cache
from dotenv import load_dotenv
import logging

# Load .env in dev (optional)
load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set. Set it as environment variable.")

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__, static_folder='static', template_folder='templates')
logging.basicConfig(level=logging.INFO)

@lru_cache(maxsize=1024)
def fetch_profile_file_path(user_id: str):
    """Return Telegram file_path for user's largest profile photo or None."""
    resp = requests.get(f"{API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1}, timeout=8)
    resp.raise_for_status()
    js = resp.json()
    if not js.get("ok") or js["result"]["total_count"] == 0:
        return None

    photos = js["result"]["photos"]
    file_id = photos[0][-1]["file_id"]  # largest size
    gf = requests.get(f"{API}/getFile", params={"file_id": file_id}, timeout=8)
    gf.raise_for_status()
    gjs = gf.json()
    if not gjs.get("ok"):
        return None
    return gjs["result"]["file_path"]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_profile_photo')
def get_profile_photo():
    user_id = request.args.get('user_id', type=str)
    if not user_id:
        return jsonify({"error": "missing user_id"}), 400
    try:
        file_path = fetch_profile_file_path(user_id)
        if not file_path:
            return jsonify({"photo_url": None})
        file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
        return jsonify({"photo_url": file_url})
    except requests.HTTPError as e:
        app.logger.error("Telegram API HTTP error: %s", e)
        return jsonify({"error": "telegram api error"}), 502
    except Exception as e:
        app.logger.exception("Unexpected error")
        return jsonify({"error": "internal server error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
