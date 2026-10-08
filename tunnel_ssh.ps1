# tunnel_ssh.ps1 - автоматический SSH-туннель к VPS
$vps = "root@195.19.219.10"

while ($true) {
    Write-Host "Подключаем туннель к $vps ..." -ForegroundColor Yellow
    ssh -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ExitOnForwardFailure=yes -o StrictHostKeyChecking=no -R 8080:127.0.0.1:8000 -N $vps
    Write-Host "Туннель разорван - переподключение через 5 сек..." -ForegroundColor Red
    Start-Sleep -Seconds 5
}