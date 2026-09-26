import requests
import logging
from typing import Optional, Dict, Any

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

def get_github_repo_info(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Получает информацию о репозитории GitHub.
    
    Args:
        owner: Владелец репозитория (например, 'Topotmooh')
        repo: Название репозитория (например, 'sellshot-studio')
        
    Returns:
        Словарь с данными репозитория или None в случае ошибки.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}"
    
    # Заголовки: GitHub API требует User-Agent, иначе вернёт 403 Forbidden
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "FDE-Training-Script"
    }
    
    try:
        logger.info("Запрос информации о репозитории: %s/%s", owner, repo)
        
        # FDE-стандарт: всегда указываем timeout!
        response = requests.get(url, headers=headers, timeout=10)
        
        # Если статус не 2xx (например, 404 или 500), выбрасываем исключение
        response.raise_for_status()
        
        # Парсим JSON
        data = response.json()
        
        logger.info("Успешно получены данные. Звёзд: %s, Форков: %s", 
                    data.get("stargazers_count", 0), 
                    data.get("forks_count", 0))
        return data
        
    except requests.exceptions.Timeout:
        logger.error("Таймаут при запросе к GitHub. Сервер не ответил за 10 секунд.")
        return None
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            logger.error("Репозиторий не найден (404). Проверь имя владельца и название.")
        else:
            logger.error("HTTP ошибка: %s (Код: %s)", e, response.status_code)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Сетевая ошибка при запросе к GitHub: %s", e)
        return None
    except ValueError:
        # Случай, когда сервер вернул 200 OK, но это не JSON (например, HTML-страница ошибки провайдера)
        logger.error("Сервер вернул некорректные данные (не JSON).")
        return None


if __name__ == "__main__":
    # Тест 1: Существующий репозиторий
    print("\n--- Тест 1: Существующий репозиторий ---")
    repo_info = get_github_repo_info("microsoft", "vscode") 
    if repo_info:
        print(f"✅ Название: {repo_info.get('name')}")
        print(f"✅ Описание: {repo_info.get('description')}")
        print(f"✅ Язык: {repo_info.get('language')}")
    
    # Тест 2: Несуществующий репозиторий (проверка обработки 404)
    print("\n--- Тест 2: Несуществующий репозиторий ---")
    bad_repo_info = get_github_repo_info("Topotmooh", "this-repo-does-not-exist-12345")
    if bad_repo_info is None:
        print("✅ Ошибка корректно обработана, программа не упала!")