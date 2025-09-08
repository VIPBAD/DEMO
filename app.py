# app.py
import os
import hmac
import hashlib
import urllib.parse
from typing import Optional
from datetime import datetime, timedelta

import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = FastAPI()
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Simple in-memory cache for profile file path: user_id -> (file_path_or_none, expires_at)
_profile_cache: dict[str, tuple[Optional[str], datetime]] = {}
CACHE_TTL = timedelta(minutes=30)


def _make_secret_key(token: str) -> bytes:
    """
    Per Telegram docs:
    secret_key = sha256(bot_token).digest()
    use that as the HMAC key for verifying initData
    """
    return hashlib.sha256(token.encode("utf-8")).digest()


def verify_init_data(init_data: str) -> dict:
    """
    Robust parser + verifier for tg.initData.

    Accepts either:
      - newline separated "key=value\nkey2=value2\n..."
      - URL query string "key=value&key2=value2&..."

    Values may be percent-encoded. Returns parsed dict (without 'hash') if valid,
    otherwise raises HTTPException with appropriate status/code.
    """
    if not init_data:
        raise HTTPException(status_code=400, detail="missing init_data")

    raw = init_data.strip()

    # parse into list of (key, value) pairs, decoding percent-encoding if present
    pairs = []
    # If it looks like a query string (contains & but not newlines) treat as URL-encoded
    if "&" in raw and "\n" not in raw:
        for part in raw.split("&"):
            if not part:
                continue
            if "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = urllib.parse.unquote_plus(k)
            v = urllib.parse.unquote_plus(v)
            pairs.append((k, v))
    else:
        # newline-separated or mixed form
        for part in raw.splitlines():
            part = part.strip()
            if not part or "=" not in part:
                continue
            k, v = part.split("=", 1)
            k = urllib.parse.unquote_plus(k)
            v = urllib.parse.unquote_plus(v)
            pairs.append((k, v))

    data = {}
    hash_value = None
    for k, v in pairs:
        if k == "hash":
            hash_value = v
        else:
            data[k] = v

    if not hash_value:
        raise HTTPException(status_code=400, detail="init_data missing hash")

    # Build data_check_string: sorted lexicographically by "key=value" strings (exclude hash)
    items = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(items).encode("utf-8")

    secret_key = _make_secret_key(BOT_TOKEN)
    computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise HTTPException(status_code=403, detail="init_data verification failed")

    return data


async def _fetch_user_profile_file_path(user_id: str) -> Optional[str]:
    """
    Uses Telegram getUserProfilePhotos -> getFile to obtain file_path for the user's largest photo.
    Cached for a short TTL to avoid repeated calls.
    """
    entry = _profile_cache.get(user_id)
    if entry:
        file_path, expires_at = entry
        if datetime.utcnow() < expires_at:
            return file_path
        _profile_cache.pop(user_id, None)

    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(
            f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1}
        )
        r.raise_for_status()
        js = r.json()
        if not js.get("ok") or js["result"]["total_count"] == 0:
            _profile_cache[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

        photos = js["result"]["photos"]
        # photos[0] is list of sizes; take the last (largest)
        file_id = photos[0][-1]["file_id"]
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
    # basic landing page - the templates/index.html (provided below) will call /verify_init
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/verify_init")
async def verify_init(payload: dict):
    init_data = payload.get("initData") or ""
    try:
        parsed = verify_init_data(init_data)
    except HTTPException as e:
        # log raw string for debugging (avoid in production if it contains PII)
        print("❌ VERIFY FAILED:", init_data)
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    result = {"ok": True, "verified": True, "data": parsed}

    import json

    user_id = None
    room_id = None
    # If startapp or start_param was passed in the URL, Telegram may include it
    if "start_param" in parsed or "startapp" in parsed:
        room_id = parsed.get("start_param") or parsed.get("startapp")
    if "user" in parsed:
        try:
            userobj = json.loads(parsed["user"])
            user_id = str(userobj.get("id"))
            result["user"] = userobj
        except Exception:
            pass

    if not user_id and "id" in parsed:
        user_id = str(parsed.get("id"))

    if user_id:
        try:
            file_path = await _fetch_user_profile_file_path(user_id)
            result["profile_photo_url"] = f"{TELEGRAM_FILE}/{file_path}" if file_path else None
        except Exception as e:
            result["profile_photo_error"] = str(e)

    if room_id:
        result["room_id"] = room_id
    result["listener_count"] = 1  # Simulated

    print(f"✅ VERIFIED user_id={user_id}, room_id={room_id}")
    return JSONResponse(result)


@app.post("/debug_client")
async def debug_client(payload: dict):
    # Lightweight debugging endpoint used by client to log what it saw.
    print("DEBUG CLIENT:", payload)
    return {"ok": True}
