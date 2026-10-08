"""Тест подключения к Telegram API."""
import requests

try:
    r = requests.get("https://api.telegram.org", timeout=10)
    print(f"✅ OK: статус {r.status_code}")
    print(f"   Ответ: {r.text[:100]}")
except Exception as e:
    print(f"❌ Ошибка: {e}")