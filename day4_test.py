import logging
import io
import requests
from typing import Literal
from PIL import Image

# Настраиваем логирование: показываем уровень, имя логгера и сообщение
logging.basicConfig(
    level=logging.DEBUG, 
    format="%(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)


def get_external_template(url: str, width: int, height: int) -> Image.Image:
    """
    Скачивает шаблон фона из внешнего источника с обработкой сбоев (Graceful Degradation).

    Args:
        url (str): URL для скачивания изображения.
        width (int): Ширина изображения (используется для fallback).
        height (int): Высота изображения (используется для fallback).

    Returns:
        Image.Image: Загруженное изображение или серый fallback-фон в случае ошибки.
    """
    try:
        logger.debug("Попытка скачать шаблон фона: %s", url)
        
        # 1. Жёсткий таймаут: если сервер молчит 10 секунд, мы не ждём вечно
        response = requests.get(url, timeout=10)
        
        # 2. Проверка статуса: если вернётся 404 или 500, метод выбросит HTTPError
        response.raise_for_status()
        
        # 3. FDE-трюк: читаем из байтов в памяти, а не из response.raw
        # Это защищает от обрыва соединения в момент, когда PIL начинает читать поток
        img = Image.open(io.BytesIO(response.content))
        logger.info("Шаблон фона успешно загружен: %s", url)
        return img
        
    except requests.RequestException as e:
        # 4. Graceful degradation: ловим сетевые ошибки, логируем и отдаём запасной вариант
        logger.warning("Не удалось загрузить шаблон по URL %s. Причина: %s. Использую fallback.", url, e)
        return Image.new("RGB", (width, height), (200, 200, 200))
        
    except Exception as e:
        # 5. Страховочная сетка: если PIL упадёт на битых данных (не картинка, а HTML-страница ошибки)
        logger.error("Критическая ошибка при обработке данных из %s: %s. Использую fallback.", url, e)
        return Image.new("RGB", (width, height), (200, 200, 200))


def _create_background(width: int, height: int, style: Literal["white", "beige", "aidentika"]) -> Image.Image:
    """Выбор фона по стилю с безопасным вызовом внешней функции."""
    if style == "white":
        return Image.new("RGB", (width, height), (255, 255, 255))
    if style == "beige":
        return Image.new("RGB", (width, height), (240, 235, 226))
    if style == "aidentika":
        # Передаем width и height, чтобы fallback мог создать картинку правильного размера
        return get_external_template("https://this-url-does-not-exist.com/aidentika_bg.jpg", width, height)
    
    raise ValueError(f"Неподдерживаемый стиль: {style}")


# === Тестовый запуск ===
if __name__ == "__main__":
    print("Запускаем тест...")
    try:
        # Мы специально используем несуществующий URL, чтобы спровоцировать ошибку
        img = _create_background(800, 800, "aidentika")
        print(f"✅ Успех! Приложение не упало. Размер полученного изображения: {img.size}")
    except Exception as e:
        print(f"❌ Всё сломалось (этого не должно было произойти): {e}")