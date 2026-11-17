# Inicializador do Painel Web Cortes AI Studio
Set-Location $PSScriptRoot

Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "  Iniciando Cortes AI Studio (Painel Web no Navegador) " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# Liberar porta 5000 se ja estiver em uso
Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}

Start-Process "http://localhost:5000"
& ".\venv\Scripts\python.exe" app.py
