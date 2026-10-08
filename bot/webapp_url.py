"""Динамический URL Mini App (читается из tunnel_url.txt)."""
from pathlib import Path


def get_web_app_url() -> str:
    """Возвращает актуальный URL Mini App."""
    p = Path(__file__).resolve().parent.parent / "tunnel_url.txt"
    
    try:
        url = p.read_text(encoding="utf-8").strip()
        if url and url.startswith("http"):
            return url.rstrip("/") + "/app"
    except Exception:
        pass
    
    return "https://app.sell-shot.ru/app"


def get_api_url() -> str:
    """Возвращает базовый URL API (без /app)."""
    p = Path(__file__).resolve().parent.parent / "tunnel_url.txt"
    
    try:
        url = p.read_text(encoding="utf-8").strip()
        if url and url.startswith("http"):
            return url.rstrip("/")
    except Exception:
        pass
    
    return "https://app.sell-shot.ru"