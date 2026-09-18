# SellShot Studio

AI-бот для генерации фонов и обработки фото товаров.

## Возможности

- Студийная цветокоррекция и тени (Aidentika-style)
- AI-генерация фонов (Yandex ART, Sber Kandinsky)
- Удаление фона (rembg)
- Лимиты и водяные знаки для free-пользователей

## Быстрый старт

### Требования

- Python 3.12
- Docker (опционально)

### Локальный запуск

1. Установи зависимости:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows
pip install -r requirements.txt