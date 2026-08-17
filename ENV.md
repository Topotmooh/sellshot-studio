# Переменные окружения

## Telegram

| Переменная | Обязательна | Описание | Пример |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | Токен бота от @BotFather | `123456789:AAH...` |
| `ADMIN_ID` | ❌ | ID администратора | `123456789` |
| `TELEGRAM_PROXY` |  | Прокси для запуска из РФ | `socks5://user:pass@host:port` |

## App

| Переменная | По умолчанию | Описание |
|---|---|---|
| `APP_NAME` | `SellShot Studio` | Название бота |
| `DEBUG` | `false` | Режим отладки |

## Storage

| Переменная | По умолчанию | Описание |
|---|---|---|
| `DB_PATH` | `data/app.db` | Путь к базе данных |
| `TEMP_DIR` | `data/temp` | Временные файлы |
| `RESULTS_DIR` | `data/results` | Готовые карточки |
| `ASSETS_DIR` | `assets` | Статические файлы |
| `BACKGROUNDS_DIR` | `assets/backgrounds` | Фоны для композитинга |

## Limits & Watermark

| Переменная | По умолчанию | Описание |
|---|---|---|
| `FREE_DAILY_LIMIT` | `5` | Лимит фото для free-пользователей |
| `ENABLE_WATERMARK` | `true` | Включить водяной знак |
| `WATERMARK_TEXT` | `SellShot Studio` | Текст водяного знака |

## Processing

| Переменная | По умолчанию | Описание |
|---|---|---|
| `MAX_PHOTO_SIZE_MB` | `20` | Максимальный размер фото |
| `MAX_CONCURRENT_PROCESSING` | `1` | Одновременных обработок |
| `PROCESSING_TIMEOUT_SECONDS` | `120` | Таймаут обработки |
| `OMP_NUM_THREADS` | `2` | Потоков для ONNX Runtime |

## Profiles

| Переменная | По умолчанию | Описание |
|---|---|---|
| `ENABLED_PROFILES` | `universal,classifieds` | Активные профили |
| `DEFAULT_PROFILE` | `universal` | Профиль по умолчанию |

## AI

| Переменная | По умолчанию | Описание |
|---|---|---|
| `AI_PROVIDER` | `local` | Движок: local, yandex, sber, gpu |
| `YANDEX_API_KEY` | `` | Ключ Yandex Cloud |
| `YANDEX_FOLDER_ID` | `` | Folder ID Yandex Cloud |
| `SBER_CLIENT_ID` | `` | Client ID SberDevices |
| `SBER_CLIENT_SECRET` | `` | Client Secret SberDevices |
| `GPU_API_URL` | `` | URL GPU-сервера |
| `GPU_API_TOKEN` | `` | Токен GPU-сервера |

## Logging

| Переменная | По умолчанию | Описание |
|---|---|---|
| `LOG_LEVEL` | `INFO` | Уровень логирования |
| `LOG_FILE` | `logs/bot.log` | Файл логов |