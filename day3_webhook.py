import os
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="GitHub Webhook Receiver")

# Секрет для проверки подписи webhook (опционально, но рекомендуется)
WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")


@app.post("/webhook")
async def receive_webhook(request: Request):
    """
    Принимает webhook от GitHub.
    """
    # Проверяем, что это действительно GitHub
    event_type = request.headers.get("X-GitHub-Event")
    if not event_type:
        logger.warning("Получен запрос без заголовка X-GitHub-Event")
        raise HTTPException(status_code=400, detail="Missing X-GitHub-Event header")
    
    # Проверяем подпись (если секрет настроен)
    if WEBHOOK_SECRET:
        signature = request.headers.get("X-Hub-Signature-256", "")
        # В production здесь нужно проверить HMAC-SHA256 подпись
        # Для обучения пропускаем эту проверку
        logger.info("Webhook подпись: %s", signature[:20] + "...")
    
    # Получаем payload
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Не удалось распарсить JSON: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Обрабатываем разные типы событий
    if event_type == "ping":
        logger.info(" Ping от GitHub! Webhook настроен корректно.")
        return {"message": "Pong!"}
    
    elif event_type == "star":
        action = payload.get("action")
        sender = payload.get("sender", {}).get("login", "unknown")
        repo = payload.get("repository", {}).get("full_name", "unknown")
        
        if action == "created":
            logger.info("⭐ %s поставил звезду репозиторию %s", sender, repo)
        elif action == "deleted":
            logger.info("💔 %s убрал звезду с репозитория %s", sender, repo)
        
        return {"message": f"Star event processed: {action}"}
    
    elif event_type == "push":
        ref = payload.get("ref", "unknown")
        commits = payload.get("commits", [])
        logger.info("📦 Push в ветку %s: %d коммитов", ref, len(commits))
        return {"message": f"Push processed: {len(commits)} commits"}
    
    else:
        logger.info("Получено событие типа %s", event_type)
        return {"message": f"Event {event_type} received"}


if __name__ == "__main__":
    port = int(os.getenv("WEBHOOK_PORT", "8000"))
    logger.info("🚀 Запуск webhook-сервера на порту %d", port)
    uvicorn.run(app, host="0.0.0.0", port=port)