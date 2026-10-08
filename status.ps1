# status.ps1 - диагностика SellShot Studio
$root = "D:\projects\sellshot-studio"

Write-Host "=== ПРОЦЕССЫ ===" -ForegroundColor Cyan
$py = Get-Process python -ErrorAction SilentlyContinue
if ($py) { $py | Format-Table Id, ProcessName, StartTime -AutoSize } else { Write-Host "python: НЕ ЗАПУЩЕН" -ForegroundColor Red }

Write-Host "=== TUNNEL URL ===" -ForegroundColor Cyan
$url = ""
if (Test-Path "$root\tunnel_url.txt") {
    $url = (Get-Content "$root\tunnel_url.txt").Trim()
    Write-Host $url
} else {
    Write-Host "tunnel_url.txt НЕ НАЙДЕН" -ForegroundColor Red
}

Write-Host "=== API HEALTH (local) ===" -ForegroundColor Cyan
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/health" -TimeoutSec 5
    Write-Host "API OK: $($r.status)" -ForegroundColor Green
} catch {
    Write-Host "API НЕ ОТВЕЧАЕТ на 127.0.0.1:8000" -ForegroundColor Red
}

Write-Host "=== MINI APP (через домен) ===" -ForegroundColor Cyan
if ($url) {
    try {
        $r2 = Invoke-WebRequest -Uri "$url/app" -TimeoutSec 10 -UseBasicParsing
        Write-Host "MINI APP OK (HTTP $($r2.StatusCode)): $url/app" -ForegroundColor Green
    } catch {
        Write-Host "MINI APP НЕ ОТВЕЧАЕТ: $url/app" -ForegroundColor Red
    }
} else {
    Write-Host "НЕТ URL - проверь tunnel_url.txt" -ForegroundColor Red
}

Write-Host "=== DONE ===" -ForegroundColor Cyan