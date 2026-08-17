# SellShot Studio

Telegram-бот для генерации продающих карточек товаров.

## Возможности

- Вырезание товара с фона (BiRefNet/ISNet/u2net)
- Удаление теней до сегментации (OpenCV LAB + inpaint)
- Адаптивная очистка маски (сохранение светлых краёв)
- Студийная цветокоррекция и тени (Aidentika-style)
- AI-генерация фонов (Yandex ART, Sber Kandinsky)
- GPU-религт через IC-Light (премиум)
- Лимиты и водяные знаки для free-пользователей

## Быстрый старт

1. Установи зависимости:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   .venv\Scripts\activate    # Windows
   pip install -r requirements.txt