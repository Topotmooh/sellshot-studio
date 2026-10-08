# tunnel_watchdog.ps1 - keeps cloudflared alive AND keeps tunnel_url.txt fresh
$root = "D:\projects\sellshot-studio"
$errLog = "$root\tunnel_err.log"
$urlFile = "$root\tunnel_url.txt"

while ($true) {
    if (Test-Path "$root\stop_flag.txt") {
        Remove-Item "$root\stop_flag.txt" -ErrorAction SilentlyContinue
        Write-Host "STOP FLAG FOUND - exiting." -ForegroundColor Cyan
        break
    }

    Remove-Item $errLog -ErrorAction SilentlyContinue
    Write-Host "Starting tunnel..." -ForegroundColor Yellow

    $p = Start-Process -FilePath "$root\cloudflared.exe" `
        -ArgumentList "tunnel","--url","http://127.0.0.1:8000","--protocol","http2" `
        -RedirectStandardError $errLog -RedirectStandardOutput "$root\tunnel_out.log" `
        -NoNewWindow -PassThru

    # Wait for first URL
    $current = ""
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        if (Test-Path $errLog) {
            $m = Select-String -Path $errLog -Pattern "https://[a-z0-9\-]+\.trycloudflare\.com" | Select-Object -Last 1
            if ($m) { $current = $m.Matches[0].Value; break }
        }
        if ($p.HasExited) { break }
    }

    if ($current) {
        Set-Content -Path $urlFile -Value $current -Encoding ASCII
        Write-Host "TUNNEL READY: $current" -ForegroundColor Green
    }

    # MONITOR: while process alive, watch for NEW URLs (reconnects)
    while (-not $p.HasExited) {
        Start-Sleep -Seconds 3
        if (Test-Path "$root\stop_flag.txt") { break }
        if (Test-Path $errLog) {
            $m = Select-String -Path $errLog -Pattern "https://[a-z0-9\-]+\.trycloudflare\.com" | Select-Object -Last 1
            if ($m) {
                $latest = $m.Matches[0].Value
                if ($latest -ne $current) {
                    $current = $latest
                    Set-Content -Path $urlFile -Value $current -Encoding ASCII
                    Write-Host "URL UPDATED: $current" -ForegroundColor Green
                }
            }
        }
    }

    if (Test-Path "$root\stop_flag.txt") {
        Remove-Item "$root\stop_flag.txt" -ErrorAction SilentlyContinue
        Write-Host "STOP FLAG FOUND - exiting." -ForegroundColor Cyan
        break
    }

    Write-Host "TUNNEL DIED - restarting in 3 sec..." -ForegroundColor Red
    Start-Sleep -Seconds 3
}