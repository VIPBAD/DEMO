import os
import hmac, hashlib
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
    return hashlib.sha256(token.encode('utf-8')).digest()


def verify_init_data(init_data: str) -> dict:
    """
    init_data is the full string provided by Telegram in the query or tg.initData
    It consists of k=v pairs joined by '\n'. One of the keys is 'hash' - compare with HMAC-SHA256.
    Returns the parsed data (dict) if valid, otherwise raise HTTPException(400).
    """
    if not init_data:
        raise HTTPException(status_code=400, detail="missing init_data")

    # Build map of key->value
    parts = init_data.split('\n')
    data = {}
    hash_value = None
    for p in parts:
        if '=' not in p:
            continue
        k, v = p.split('=', 1)
        if k == 'hash':
            hash_value = v
        else:
            data[k] = v

    if not hash_value:
        raise HTTPException(status_code=400, detail="init_data missing hash")

    # Build data_check_string: sorted keys (lexicographically) joined with '\n' as "key=value"
    items = sorted([f"{k}={v}" for k, v in data.items()])
    data_check_string = '\n'.join(items).encode('utf-8')

    secret_key = _make_secret_key(BOT_TOKEN)
    computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

    # Telegram's hash field is hex as well. Compare in constant time
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
        r = await client.get(f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
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



@app.post("/debug_client")
async def debug_client(payload: dict):
    # lightweight debugging endpoint used by client to log what it saw.
    # We'll just print to server logs and return ok.
    print("DEBUG CLIENT:", payload)
    return {"ok": True}
    
 

@app.post("/verify_init")
async def verify_init(payload: dict):
    """
    Client should POST JSON:
      { "initData": "<initData string from tg.initData>", "initDataUnsafe": <object or null> }
    Returns JSON:
      { "ok": True, "verified": True, "data": {...}, "profile_photo_url": "...", "room_id": "...", "listener_count": 1 }
    """
    init_data = payload.get("initData") or ""
    try:
        parsed = verify_init_data(init_data)
    except HTTPException as e:
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    result = {"ok": True, "verified": True, "data": parsed}

    # Extract user and room_id from initData
    import json
    user_id = None
    room_id = None
    if "start_param" in parsed or "startapp" in parsed:  # Check for startapp parameter
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
            if file_path:
                result["profile_photo_url"] = f"{TELEGRAM_FILE}/{file_path}"
            else:
                result["profile_photo_url"] = None
        except Exception as e:
            result["profile_photo_error"] = str(e)

    # Add room_id and simulate listener count
    if room_id:
        result["room_id"] = room_id
    result["listener_count"] = 1  # Simulate 1 listener; you can replace with real-time data if available

    return JSONResponse(result)
