"""SellShot Web API: тонкий слой поверх того же ядра, что и Telegram-бот."""
from __future__ import annotations

import asyncio
import re
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse

from config import logger, settings
from core.profiles import get_profile
from services import compositor, segmenter, storage, watermark

app = FastAPI(title="SellShot Web API")

WEB_DIR = Path(__file__).resolve().parent.parent / "web"
_SAFE = re.compile(r"[a-z0-9_]{1,32}")

# Задачи в памяти (MVP; позже — БД/Redis)
_tasks: dict[str, dict] = {}

# Простейший rate-limit по IP: 1 запрос / 2 сек
_ip_last: dict[str, float] = {}


def _check_ip(ip: str) -> None:
    now = time.monotonic()
    if now - _ip_last.get(ip, 0.0) < 2.0:
        raise HTTPException(429, "too many requests")
    _ip_last[ip] = now


def _clean(key: str) -> str:
    return key if _SAFE.fullmatch(key) else ""


@app.get("/", response_class=HTMLResponse)
async def index():
    return (WEB_DIR / "index.html").read_text(encoding="utf-8")


@app.post("/api/generate")
async def generate(
    request: Request,
    photo: UploadFile = File(...),
    profile: str = Form("universal"),
    category: str = Form("other"),
    style: str = Form("studio"),
):
    _check_ip(request.client.host)

    data = await photo.read()
    if len(data) > settings.MAX_PHOTO_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, "file too big")
    if len(data) < 1024:
        raise HTTPException(400, "file too small")

    profile = _clean(profile) or settings.DEFAULT_PROFILE
    category = _clean(category) or "other"
    style = _clean(style) or "studio"

    task_id = uuid.uuid4().hex
    _tasks[task_id] = {"status": "queued", "created": time.time()}

    asyncio.get_running_loop().create_task(
        _run_task(task_id, data, profile, category, style)
    )
    return {"task_id": task_id}


async def _run_task(task_id: str, data: bytes, profile_key: str, category: str, style: str):
    saved = None
    cutout = None
    try:
        _tasks[task_id]["status"] = "processing"

        saved = storage.new_temp_path(suffix=".jpg")
        await asyncio.to_thread(saved.write_bytes, data)

        cutout = storage.new_temp_path(suffix=".png")
        await segmenter.cutout_product(saved, cutout)

        prof = get_profile(profile_key)
        result = storage.new_result_path(suffix=".jpg")
        await compositor.compose_card(
            cutout, result, prof, category, background_style=style
        )

        # MVP: всегда с водяным знаком (как free в боте)
        watermark.watermark_file(result, settings.WATERMARK_TEXT)

        _tasks[task_id].update({"status": "done", "result": str(result)})
    except Exception:
        logger.exception("web task failed")
        _tasks[task_id].update({"status": "error", "error": "internal error"})
    finally:
        for p in (saved, cutout):
            if p is not None:
                storage.safe_unlink(p)


@app.get("/api/task/{task_id}")
async def task_status(task_id: str):
    t = _tasks.get(task_id)
    if t is None:
        raise HTTPException(404, "not found")

    out = {"status": t["status"]}
    if t["status"] == "done":
        out["result_url"] = f"/api/result/{task_id}"
    if t["status"] == "error":
        out["error"] = t.get("error")
    return out


@app.get("/api/result/{task_id}")
async def task_result(task_id: str):
    t = _tasks.get(task_id)
    if t is None or t["status"] != "done":
        raise HTTPException(404, "not found")
    return FileResponse(t["result"], media_type="image/jpeg")


async def _purge_loop():
    """Результаты веб-задач живут не больше часа."""
    while True:
        await asyncio.sleep(600)
        now = time.time()
        for tid in list(_tasks):
            if now - _tasks[tid].get("created", now) > 3600:
                res = _tasks[tid].get("result")
                if res:
                    storage.safe_unlink(Path(res))
                _tasks.pop(tid, None)


@app.on_event("startup")
async def _startup():
    asyncio.create_task(_purge_loop())