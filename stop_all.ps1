# stop_all.ps1 - остановка приложения
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force
Write-Host "ВСЁ ОСТАНОВЛЕНО." -ForegroundColor Cyan