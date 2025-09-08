# server.py
from flask import Flask, request, jsonify
import requests
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")  # set in env, never expose in frontend
API = f"https://api.telegram.org/bot{8482046560:AAHDHQAgtnWNp7gQr7c5E6MKLtxnvyytyDI}"

app = Flask(__name__)

@app.route('/get_profile_photo')
def get_profile_photo():
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({"error":"missing user_id"}), 400

    # 1) getUserProfilePhotos
    resp = requests.get(f"{API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
    js = resp.json()
    if not js.get("ok") or not js["result"]["total_count"]:
        return jsonify({"photo_url": None})

    photos = js["result"]["photos"]
    # photos is a list-of-lists (different sizes). choose largest:
    file_id = photos[0][-1]["file_id"]  # last size is biggest

    # 2) getFile to get file_path
    gf = requests.get(f"{API}/getFile", params={"file_id": file_id}).json()
    if not gf.get("ok"):
        return jsonify({"photo_url": None})
    file_path = gf["result"]["file_path"]

    # 3) construct file URL
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    return jsonify({"photo_url": file_url})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
