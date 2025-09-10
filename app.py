# server.py
import os, hmac, hashlib, httpx, urllib.parse, json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Tuple
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

BOT_TOKEN = os.getenv("BOT_TOKEN") or "8410391376:AAF2GqNdUnl1Rh8CZIYwiwj3PfPv27-Dcg8"
API = f"https://api.telegram.org/bot{BOT_TOKEN}"
FILE_API = f"https://api.telegram.org/file/bot{BOT_TOKEN}"

app = FastAPI()

# --- InitData verification (spec) ---
def derive_secret(token: str) -> bytes:
    return hmac.new(b"WebAppData", token.encode("utf-8"), hashlib.sha256).digest()  # [8]

def parse_and_sign_string(init_qs: str):
    if not init_qs or "hash=" not in init_qs:
        raise HTTPException(400, "init_data missing or invalid")  # [8]
    pairs, their_hash = [], None
    for part in init_qs.split("&"):
        if "=" not in part:
            continue
        k, v = part.split("=", 1)
        if k == "hash":
            their_hash = v
        else:
            pairs.append(f"{k}={v}")
    if not their_hash:
        raise HTTPException(400, "hash missing")  # [8]
    pairs.sort()
    dcs = "\n".join(pairs).encode("utf-8")  # newline-joined data_check_string  [12]
    return dcs, their_hash

def verify_init_data(init_qs: str, max_age_seconds: int = 3600) -> dict:
    dcs, their_hash = parse_and_sign_string(init_qs)  # [8]
    secret = derive_secret(BOT_TOKEN)  # [8]
    calc = hmac.new(secret, dcs, hashlib.sha256).hexdigest()  # [8]
    if not hmac.compare_digest(calc, their_hash):
        raise HTTPException(403, "init_data verification failed")  # [8]
    parsed = {}
    for kv in dcs.decode("utf-8").split("\n"):
        k, v = kv.split("=", 1)
        parsed[k] = v
    if "auth_date" in parsed and max_age_seconds:
        ts = int(parsed["auth_date"])
        if datetime.now(timezone.utc).timestamp() - ts > max_age_seconds:
            raise HTTPException(401, "init_data expired")  # [12]
    if "user" in parsed:
        try:
            parsed["user"] = json.loads(urllib.parse.unquote(parsed["user"]))
        except Exception:
            pass
    return parsed

# --- Profile photo via Bot API ---
_cache: Dict[str, Tuple[Optional[str], datetime]] = {}
TTL = timedelta(minutes=30)

async def fetch_avatar_path(user_id: str) -> Optional[str]:
    now = datetime.utcnow()
    cached = _cache.get(user_id)
    if cached and cached[1] > now:
        return cached

    async with httpx.AsyncClient(timeout=8) as client:
        r = await client.get(f"{API}/getUserProfilePhotos", params={"user_id": user_id, "limit": 1})
        r.raise_for_status()
        js = r.json()
        if not js.get("ok") or js["result"]["total_count"] == 0:
            _cache[user_id] = (None, now + TTL)
            return None
        file_id = js["result"]["photos"][-1]["file_id"]  # largest size  [6]
        g = await client.get(f"{API}/getFile", params={"file_id": file_id})
        g.raise_for_status()
        gjs = g.json()
        if not gjs.get("ok"):
            _cache[user_id] = (None, now + TTL)
            return None
        fp = gjs["result"]["file_path"]
        _cache[user_id] = (fp, now + TTL)
        return fp  # combine below  [3][17]

@app.post("/verify_init")
async def verify_endpoint(payload: dict):
    init_qs = payload.get("initData")
    try:
        data = verify_init_data(init_qs)  # HMAC verification per spec
    except HTTPException as e:
        return JSONResponse({"ok": False, "error": e.detail}, status_code=e.status_code)

    user = data.get("user") or {}
    resp = {"ok": True, "user": user, "data": data}

    if "id" in user:
        fp = await fetch_avatar_path(str(user["id"]))
        if fp:
            resp["profile_photo_url"] = f"{FILE_API}/{fp}"  # downloadable URL
        else:
            resp["profile_photo_url"] = user.get("photo_url")  # optional fallback
    return JSONResponse(resp)
