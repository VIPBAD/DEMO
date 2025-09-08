# main.py
import os
from typing import Optional
from datetime import datetime, timedelta
import logging

from fastapi import FastAPI, Request, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import httpx
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN not set. Set BOT_TOKEN environment variable.")

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
TELEGRAM_FILE = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = FastAPI()
# In production, replace ["*"] with your domain(s).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

logger = logging.getLogger("uvicorn.error")

# simple in-memory cache: user_id -> (file_path_or_none, expires_at)
_profile_cache: dict[str, tuple[Optional[str], datetime]] = {}
CACHE_TTL = timedelta(minutes=30)


async def _fetch_user_profile_file_path(user_id: str) -> Optional[str]:
    # check cache
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
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/get_profile_photo")
async def get_profile_photo(user_id: str):
    if not user_id:
        raise HTTPException(status_code=400, detail="missing user_id")
    try:
        file_path = await _fetch_user_profile_file_path(user_id)
        if not file_path:
            return JSONResponse({"photo_url": None})
        file_url = f"{TELEGRAM_FILE}/{file_path}"
        return JSONResponse({"photo_url": file_url})
    except httpx.HTTPStatusError as e:
        logger.error("Telegram API HTTP error: %s", e)
        return JSONResponse({"error": "telegram api error"}, status_code=502)
    except Exception as e:
        logger.exception("Unexpected error")
        return JSONResponse({"error": "internal server error"}, status_code=500)


# Debug endpoint: client posts UA + initData so server logs what client saw.
@app.post("/debug_client")
async def debug_client(payload: dict = Body(...)):
    logger.info("DEBUG CLIENT: %s", payload)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
