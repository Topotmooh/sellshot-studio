# start_all.ps1 - запуск всего SellShot Studio
$root = "D:\projects\sellshot-studio"

Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# Окно 1: сервер (uvicorn)
Start-Process powershell -ArgumentList "-NoExit","-Command","cd $root; .\.venv\Scripts\activate; python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload"
Start-Sleep -Seconds 3

# Окно 2: SSH-туннель к VPS
Start-Process powershell -ArgumentList "-NoExit","-Command","cd $root; powershell -ExecutionPolicy Bypass -File .\tunnel_ssh.ps1"
Start-Sleep -Seconds 2

# Окно 3: Telegram-бот
Start-Process powershell -ArgumentList "-NoExit","-Command","cd $root; .\.venv\Scripts\activate; python main.py"

Write-Host "ВСЁ ЗАПУЩЕНО. Постоянный адрес: https://app.sell-shot.ru" -ForegroundColor Cyan