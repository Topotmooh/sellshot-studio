"""SellShot Studio — FastAPI веб-сервер + Mini App API + PWA."""
from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config import logger, settings
from core.profiles import get_profile
from services.compositor import compose_card
from services.segmenter import cutout_product


# ================= ИНИЦИАЛИЗАЦИЯ =================

app = FastAPI(
    title=settings.APP_NAME,
    description="API для генерации студийных карточек товаров",
    version="1.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Path(settings.RESULTS_DIR).mkdir(parents=True, exist_ok=True)
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)
Path("web").mkdir(exist_ok=True)
Path("web/pwa").mkdir(parents=True, exist_ok=True)

app.mount("/static/results", StaticFiles(directory=settings.RESULTS_DIR), name="results")
app.mount("/pwa", StaticFiles(directory="web/pwa"), name="pwa")


# ================= PWA ROUTES =================

@app.get("/manifest.webmanifest", include_in_schema=False)
async def get_manifest():
    return FileResponse(
        Path("web/pwa/manifest.webmanifest"),
        media_type="application/manifest+json",
    )


@app.get("/sw.js", include_in_schema=False)
async def get_service_worker():
    return FileResponse(
        Path("web/pwa/sw.js"),
        media_type="application/javascript",
        headers={"Cache-Control": "no-cache"},
    )


# ================= МОДЕЛИ =================

class ProcessResult(BaseModel):
    success: bool
    image_url: str | None = None
    description_avito: str | None = None
    description_youla: str | None = None
    description_vk: str | None = None
    description_gde: str | None = None
    description_barahla: str | None = None
    description_kupipanda: str | None = None
    description_vkupiprodai: str | None = None
    description_yandex: str | None = None
    description_meshok: str | None = None
    description_looton: str | None = None
    error: str | None = None


# ================= ГЕНЕРАЦИЯ ОПИСАНИЙ =================

def generate_descriptions(
    category: str,
    product_name: str,
    product_description: str,
    city: str,
    phone: str,
    address: str = "",
    inn: str = ""
) -> dict[str, str]:
    """Генерирует описания для 10 площадок с данными продавца."""
    
    # Базовая информация о товаре
    product_info = f"**{product_name}**\n\n{product_description}"
    
    # Контактная информация (реальные данные из формы)
    contact_info = f"📞 Телефон: {phone}"
    if city:
        contact_info += f"\n🏙️ Город: {city}"
    if address:
        contact_info += f"\n Адрес: {address}"
    if inn:
        contact_info += f"\n🏢 ИНН: {inn}"
    
    # Шаблоны для разных категорий (БЕЗ плейсхолдеров [город] и [телефон])
    category_templates = {
        "clothing": {
            "features": [
                "✅ Материал: уточняйте в ЛС",
                "✅ Размер: уточняйте в ЛС",
                "✅ Состояние: новое/отличное",
                "✅ Сезон: демисезон",
                "✅ Уход: деликатная стирка",
            ],
        },
        "shoes": {
            "features": [
                "✅ Материал: натуральная кожа/экокожа",
                "✅ Размер: уточняйте в ЛС",
                "✅ Состояние: новое/отличное",
                "✅ Подошва: без износа",
                "✅ Сезон: демисезон",
            ],
        },
        "bags": {
            "features": [
                "✅ Материал: премиум экокожа",
                "✅ Размеры: уточняйте в ЛС",
                "✅ Отделения: основное + карманы",
                "✅ Фурнитура: металлическая, надёжная",
                "✅ Состояние: новое/отличное",
            ],
        },
        "electronics": {
            "features": [
                "✅ Состояние: полностью рабочая",
                "✅ Комплектация: полная (зарядка, коробка)",
                "✅ Гарантия: проверена перед продажей",
                "✅ Причина продажи: не используется",
            ],
        },
        "furniture": {
            "features": [
                "✅ Состояние: хорошее, без повреждений",
                "✅ Материал: качественный",
                "✅ Самовывоз или доставка по городу",
                "✅ Причина продажи: переезд/обновление",
            ],
        },
        "kids": {
            "features": [
                "✅ Возраст: уточняйте в ЛС",
                "✅ Состояние: отличное",
                "✅ Безопасность: проверено",
                "✅ Причина продажи: ребёнок вырос",
            ],
        },
        "sports": {
            "features": [
                "✅ Состояние: отличное",
                "✅ Комплектация: полная",
                "✅ Причина продажи: не используется",
            ],
        },
        "auto": {
            "features": [
                "✅ Совместимость: уточняйте по VIN",
                "✅ Состояние: новое/б/у отличное",
                "✅ Гарантия: проверено перед продажей",
            ],
        },
        "home": {
            "features": [
                "✅ Состояние: отличное",
                "✅ Материал: качественный",
                "✅ Причина продажи: не подошло",
            ],
        },
        "beauty": {
            "features": [
                "✅ Срок годности: актуальный",
                "✅ Упаковка: не вскрыта",
                "✅ Оригинал: 100%",
            ],
        },
        "books": {
            "features": [
                "✅ Состояние: отличное",
                "✅ Язык: русский",
                "✅ Причина продажи: прочитано",
            ],
        },
        "hobby": {
            "features": [
                "✅ Состояние: отличное",
                "✅ Комплектация: полная",
                "✅ Причина продажи: хобби изменилось",
            ],
        },
        "universal": {
            "features": [
                "✅ Качество: премиум",
                "✅ Состояние: новое/отличное",
                "✅ Комплектация: полная",
                "✅ Причина продажи: не подошло",
            ],
        },
    }

    tpl = category_templates.get(category, category_templates["universal"])
    features_text = "\n".join(tpl["features"])

    # Описания для 10 площадок (БЕЗ дублирования контактов)
    desc_avito = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"📞 Звоните или пишите в ЛС — отвечу быстро!"
    )

    desc_youla = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"💬 Пишите в чат — отвечу в течение часа!"
    )

    desc_vk = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"🛒 Добавляйте в корзину — отправлю в течение дня!"
    )

    desc_yandex = (
        f" {product_info}\n\n"
        f"{features_text}\n\n"
        f" Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"📱 Пишите через Яндекс — безопасная сделка!"
    )

    desc_gde = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f" Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"📞 Звоните — договоримся!"
    )

    desc_barahla = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f" Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f" Пишите или звоните!"
    )

    desc_kupipanda = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"💬 Пишите в чат — отвечу быстро!"
    )

    desc_vkupiprodai = (
        f"🔥 {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"📞 Связывайтесь — обсудим детали!"
    )

    desc_meshok = (
        f" {product_info}\n\n"
        f"{features_text}\n\n"
        f" Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"⚠️ Участвуйте в аукционе — стартовая цена минимальна!"
    )

    desc_looton = (
        f"✨ {product_info}\n\n"
        f"{features_text}\n\n"
        f"📦 Доставка: по договорённости\n"
        f"💰 Оплата: наличные / перевод\n"
        f"📦 Самовывоз возможен\n\n"
        f"{contact_info}\n\n"
        f"🔒 100% оригинал, проверено экспертами!"
    )

    return {
        "description_avito": desc_avito,
        "description_youla": desc_youla,
        "description_vk": desc_vk,
        "description_yandex": desc_yandex,
        "description_gde": desc_gde,
        "description_barahla": desc_barahla,
        "description_kupipanda": desc_kupipanda,
        "description_vkupiprodai": desc_vkupiprodai,
        "description_meshok": desc_meshok,
        "description_looton": desc_looton,
    }


# ================= СТАТИСТИКА =================

STATS = {
    "cards_made": 1240,
    "hours_saved": 620,
    "moderation_pass": 98,
    "active_users": 87,
}


# ================= РОУТЫ =================

@app.get("/", response_class=HTMLResponse)
async def index():
    minapp_path = Path("web/minapp.html")
    if minapp_path.exists():
        return HTMLResponse(content=minapp_path.read_text(encoding="utf-8"))
    return HTMLResponse(
        content="<h1>SellShot Studio API is running</h1>"
                "<p>Открой /app для Mini App</p>"
    )


@app.get("/app", response_class=HTMLResponse)
async def get_minapp():
    minapp_path = Path("web/minapp.html")
    if not minapp_path.exists():
        raise HTTPException(status_code=404, detail="Mini App не найден")
    return HTMLResponse(content=minapp_path.read_text(encoding="utf-8"))


@app.get("/api/stats")
async def get_stats():
    """Статистика для Mini App."""
    return STATS


@app.post("/api/process_image", response_model=ProcessResult)
async def process_image(
    file: UploadFile = File(...),
    category: str = Form("universal"),
    product_name: str = Form(""),
    product_description: str = Form(""),
    city: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    inn: str = Form("")
):
    """
    Принимает фото → вырезает фон → композитинг →
    генерирует описания для 10 досок объявлений с данными продавца.
    """
    if not file.filename or not file.filename.lower().endswith((".jpg", ".jpeg", ".png")):
        raise HTTPException(status_code=400, detail="Принимаются только JPG/PNG")

    unique_id = uuid.uuid4().hex[:12]
    ext = Path(file.filename).suffix.lower()

    orig_path = Path(settings.TEMP_DIR) / f"{unique_id}_orig{ext}"
    cutout_path = Path(settings.TEMP_DIR) / f"{unique_id}_cutout.png"
    result_path = Path(settings.RESULTS_DIR) / f"{unique_id}_final.jpg"

    try:
        # 1. Сохраняем оригинал
        with open(orig_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 2. Получаем профиль
        profile = get_profile("universal")

        # 3. Пайплайн обработки
        logger.info("🔄 Начало обработки: %s", orig_path.name)

        await cutout_product(orig_path, cutout_path)

        await compose_card(
            cutout_path=cutout_path,
            output_path=result_path,
            profile=profile,
            category=category,
        )

        # 4. Генерируем описания для 10 площадок с данными продавца
        descriptions = generate_descriptions(
            category=category,
            product_name=product_name,
            product_description=product_description,
            city=city,
            phone=phone,
            address=address,
            inn=inn
        )

        # 5. Увеличиваем счётчики
        STATS["cards_made"] += 1
        STATS["hours_saved"] = round(STATS["hours_saved"] + 0.5, 1)

        image_url = f"/static/results/{result_path.name}"
        logger.info("✅ Карточка создана: %s", result_path.name)

        return ProcessResult(
            success=True,
            image_url=image_url,
            **descriptions,
        )

    except Exception as e:
        logger.error("❌ Ошибка обработки: %s", e, exc_info=True)
        return ProcessResult(success=False, error=str(e))

    finally:
        for temp_file in [orig_path, cutout_path]:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass


@app.get("/api/health")
async def health():
    """Проверка работоспособности."""
    return {"status": "ok", "app": settings.APP_NAME}


# ================= ЗАПУСК =================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )