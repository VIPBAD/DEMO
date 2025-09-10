import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"
app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory cache for profile photos
PROFILE_CACHE: dict[str, tuple[Optional[str], datetime]] = {}
CACHE_TTL = timedelta(minutes=30)

def generate_secret_key(bot_token: str) -> bytes:
    """Generate secret key using HMAC-SHA256 with 'WebAppData' as key."""
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()

def verify_telegram_data(init_data: str) -> dict:
    """Verify Telegram init data signature."""
    if not init_data or not init_data.strip():
        raise HTTPException(status_code=400, detail="Init data is missing or empty")

    # Split into key-value pairs
    pairs = [p.split("=", 1) for p in init_data.split("&") if "=" in p]
    data = {k: v for k, v in pairs if k != "hash"}
    hash_value = next((v for k, v in pairs if k == "hash"), None)

    if not hash_value:
        raise HTTPException(status_code=400, detail="Hash value missing")

    # Create data check string
    check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items())).encode("utf-8")
    secret_key = generate_secret_key(BOT_TOKEN)
    computed_hash = hmac.new(secret_key, check_string, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise HTTPException(status_code=403, detail="Invalid signature")

    return data

async def fetch_profile_photo(user_id: str) -> Optional[str]:
    """Fetch the largest profile photo file path from Telegram API."""
    cache_entry = PROFILE_CACHE.get(user_id)
    if cache_entry and datetime.utcnow() < cache_entry[1]:
        return cache_entry[0]

    PROFILE_CACHE.pop(user_id, None)  # Evict if stale

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        response.raise_for_status()
        data = response.json()

        if not data.get("ok") or data["result"]["total_count"] == 0:
            PROFILE_CACHE[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

        file_id = data["result"]["photos"][0][-1]["file_id"]
        file_response = await client.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id})
        file_response.raise_for_status()
        file_data = file_response.json()

        if not file_data.get("ok"):
            PROFILE_CACHE[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

        file_path = file_data["result"]["file_path"]
        PROFILE_CACHE[user_id] = (file_path, datetime.utcnow() + CACHE_TTL)
        return file_path

@app.post("/verify")
async def verify_init_data_endpoint(payload: dict):
    """Endpoint to verify Telegram init data and return user info."""
    init_data = payload.get("initData")
    if not init_data:
        return JSONResponse({"ok": False, "error": "Init data missing"}, status_code=400)

    try:
        verified_data = verify_telegram_data(init_data)
    except HTTPException as e:
        print(f"Verification failed: {e.detail}")
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    result = {"ok": True, "data": verified_data}

    # Parse user from verified data
    if "user" in verified_data:
        try:
            user_str = verified_data["user"]
            user = json.loads(user_str)
            user_id = str(user.get("id"))
            result["user"] = {
                "id": user.get("id"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "username": user.get("username"),
                "photo_url": user.get("photo_url")  # May be present or not
            }

            # Fetch profile photo if not in init data
            if not result["user"]["photo_url"]:
                photo_path = await fetch_profile_photo(user_id)
                if photo_path:
                    result["user"]["photo_url"] = f"{TELEGRAM_FILE_API}/{photo_path}"
        except Exception as e:
            result["user_parse_error"] = str(e)

    return JSONResponse(result)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    # Serve the index.html directly
    with open("index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)
