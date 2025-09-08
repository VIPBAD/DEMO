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

_profile_cache: dict[str, tuple[Optional[str], datetime]] = {}
CACHE_TTL = timedelta(minutes=30)

def _make_secret_key(token: str) -> bytes:
    return hashlib.sha256(token.encode('utf-8')).digest()

def verify_init_data(init_data: str) -> dict:
    if not init_data or not init_data.strip():
        raise HTTPException(status_code=400, detail="init_data missing or empty")

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

    items = sorted([f"{k}={v}" for k, v in data.items()])
    data_check_string = '\n'.join(items).encode('utf-8')

    secret_key = _make_secret_key(BOT_TOKEN)
    computed_hash = hmac.new(secret_key, data_check_string, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(computed_hash, hash_value):
        raise HTTPException(status_code=403, detail="init_data verification failed")

    return data

async def _fetch_user_profile_file_path(user_id: str) -> Optional[str]:
    entry = _profile_cache.get(user_id)
    if entry and datetime.utcnow() < entry[1]:
        return entry[0]
    _profile_cache.pop(user_id, None)

    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(f"{TELEGRAM_API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        r.raise_for_status()
        js = r.json()
        if not js.get("ok") or js["result"]["total_count"] == 0:
            _profile_cache[user_id] = (None, datetime.utcnow() + CACHE_TTL)
            return None

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
        print(f"❌ VERIFY FAILED: {init_data}")  # Log raw string for debug
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    result = {"ok": True, "verified": True, "data": parsed}

    user_id = None
    room_id = None
    if "start_param" in parsed or "startapp" in parsed:
        room_id = parsed.get("start_param") or parsed.get("startapp")
    if "user" in parsed:
        try:
            userobj = eval(parsed["user"])  # Use eval for simplicity; consider json.loads if stringified
            user_id = str(userobj.get("id"))
            result["user"] = userobj
        except Exception:
            pass

    if user_id:
        try:
            file_path = await _fetch_user_profile_file_path(user_id)
            result["profile_photo_url"] = f"{TELEGRAM_FILE}/{file_path}" if file_path else None
        except Exception as e:
            result["profile_photo_error"] = str(e)

    if room_id:
        result["room_id"] = room_id
    result["listener_count"] = 1

    print(f"✅ VERIFIED user_id={user_id}, room_id={room_id}")
    return JSONResponse(result)

@app.post("/debug_client")
async def debug_client(payload: dict):
    print("DEBUG CLIENT:", payload)
    return {"ok": True}
