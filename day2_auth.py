import os
import requests
import logging
from dotenv import load_dotenv
from typing import Optional, Dict, Any

load_dotenv()  # Загружает переменные из .env

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


def get_private_repo_info(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Получает информацию о приватном репозитории GitHub с аутентификацией.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # Получаем токен из переменных окружения
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.error("GITHUB_TOKEN не найден в .env файле!")
        return None
    
    # FDE-паттерн: Bearer Token в заголовке Authorization
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FDE-Training-Script",
        "Authorization": f"Bearer {token}"  # ← вот где магия
    }
    
    try:
        logger.info("Запрос к приватному репозиторию: %s/%s", owner, repo)
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        logger.info("✅ Успех! Репозиторий: %s, Приватный: %s", 
                    data.get("name"), data.get("private"))
        return data
        
    except requests.exceptions.HTTPError as e:
        if response.status_code == 401:
            logger.error("❌ Ошибка аутентификации (401). Проверь токен.")
        elif response.status_code == 404:
            logger.error("❌ Репозиторий не найден или нет доступа (404).")
        else:
            logger.error("HTTP ошибка: %s", e)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Сетевая ошибка: %s", e)
        return None


if __name__ == "__main__":
    print("--- Доступ к приватному репозиторию ---")
    repo_info = get_private_repo_info("Topotmooh", "sellshot-studio")
    
    if repo_info:
        print(f"\n✅ Название: {repo_info.get('name')}")
        print(f"✅ Приватный: {repo_info.get('private')}")
        print(f"✅ Описание: {repo_info.get('description')}")
        print(f"✅ Звёзд: {repo_info.get('stargazers_count')}")
        print(f"✅ Форков: {repo_info.get('forks_count')}")
    else:
        print("\n❌ Не удалось получить данные. Проверь токен и имя репозитория.")