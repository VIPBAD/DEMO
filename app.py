# app.py
import os
import hmac
import hashlib
import json
from datetime import datetime, timedelta
from typing import Optional

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi import Request

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# serve static and templates
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# simple in-memory cache for file_path -> ttl
_profile_cache: dict[str, tuple[Optional[str], datetime]] = {}
CACHE_TTL = timedelta(minutes=30)


def _make_secret_key(bot_token: str) -> bytes:
    """
    Telegram Mini Apps verification:
    secret_key = HMAC_SHA256(key=b"WebAppData", msg=bot_token)
    """
    return hmac.new(b"WebAppData", bot_token.encode("utf-8"), hashlib.sha256).digest()


def verify_init_data(init_data: str) -> dict:
    """
    Verify init_data (query-string-like) per Telegram Mini Apps spec.
    Returns dict of key->value (values are the raw string values).
    Raises HTTPException on failure.
    """
    if not init_data or not init_data.strip():
        raise HTTPException(status_code=400, detail="init_data missing or empty")

    # split into k=v pairs (init_data is like: key1=val1&key2=val2&hash=...)
    parts = [p for p in init_data.split("&") if "=" in p]
    data = {}
    hash_value = None

    for p in parts:
        k, v = p.split("=", 1)
        if k == "hash":
            hash_value = v
        else:
            data[k] = v

    if not hash_value:
        raise HTTPException(status_code=400, detail="init_data missing hash")

    # Build data_check_string: sorted keys, format "key=value", joined with '\n'
    items = sorted([f"{k}={v}" for k, v in data.items()])
    data_check_string = "\n".join(items).encode("utf-8")

    secret_key = _make_secret_key(BOT_TOKEN)
    computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise HTTPException(status_code=403, detail="init_data verification failed")

    return data


async def _fetch_user_profile_file_path(user_id: str) -> Optional[str]:
    """
    Returns Telegram file_path for user's largest profile photo or None.
    Caches result for CACHE_TTL.
    """
    entry = _profile_cache.get(user_id)
    if entry and datetime.utcnow() < entry[1]:
        return entry[0]
    # evict stale
    _profile_cache.pop(user_id, None)

    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        r.raise_for_status()
        js = r.json()
        if not js.get("ok") or js["result"]["total_count"] == 0:
            _profile_cache[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

        # pick largest photo size (last in array)
        file_id = js["result"]["photos"][0][-1]["file_id"]

        gf = await client.get(f"{TELEGRAM_API}/getFile", params={"file_id": file_id})
        gf.raise_for_status()
        gjs = gf.json()
        if not gjs.get("ok"):
            _profile_cache[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

        file_path = gjs["result"]["file_path"]
        _profile_cache[user_id] = (file_path, datetime.utcnow() + CACHE_TTL)
        return file_path


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/verify_init")
async def verify_init(payload: dict):
    init_data = payload.get("initData")
    if not init_data:
        return JSONResponse({"ok": False, "error": "init_data missing"}, status_code=400)

    try:
        parsed = verify_init_data(init_data)
    except HTTPException as e:
        # keep a server log for debugging
        print("❌ VERIFY FAILED:", e.detail)
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    result = {"ok": True, "verified": True, "data": parsed}

    # parsed["user"] is a JSON-string per spec, parse it safely
    user_id = None
    if "user" in parsed:
        try:
            user_obj = json.loads(parsed["user"])
            user_id = str(user_obj.get("id")) if user_obj.get("id") is not None else None
            result["user"] = {
                "id": user_obj.get("id"),
                "first_name": user_obj.get("first_name"),
                "last_name": user_obj.get("last_name"),
                "username": user_obj.get("username"),
                "language_code": user_obj.get("language_code"),
                # photo_url may exist depending on privacy and platform
                "photo_url": user_obj.get("photo_url"),
            }
        except Exception as e:
            result["user_parse_error"] = str(e)

    # If we have a user_id, attempt to fetch Bot API profile photo URL
    if user_id:
        try:
            file_path = await _fetch_user_profile_file_path(user_id)
            result["profile_photo_url"] = f"{TELEGRAM_FILE}/{file_path}" if file_path else None
        except Exception as e:
            result["profile_photo_error"] = str(e)

    return JSONResponse(result)
