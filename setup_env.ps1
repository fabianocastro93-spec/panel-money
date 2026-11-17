# Script de Configuração Rápida em PowerShell
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "   Instalador do Ambiente - Cortes AI (Shorts e Reels)  " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

# 1. Verificar Python
try {
    $pyVer = python --version 2>&1
    if ($pyVer -like "*Python*") {
        Write-Host "[OK] $pyVer detectado." -ForegroundColor Green
    } else {
        throw "Python ausente"
    }
} catch {
    Write-Host "[!] Python não encontrado. Instalando Python 3.11 via Winget..." -ForegroundColor Yellow
    winget install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 2. Verificar Git
try {
    $gitVer = git --version 2>&1
    Write-Host "[OK] $gitVer detectado." -ForegroundColor Green
} catch {
    Write-Host "[!] Instalando Git via Winget..." -ForegroundColor Yellow
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# 3. Criar e Ativar Venv
if (!(Test-Path ".\venv")) {
    Write-Host "[*] Criando ambiente virtual (venv)..." -ForegroundColor Cyan
    python -m venv venv
}

Write-Host "[*] Instalando dependências..." -ForegroundColor Cyan
& ".\venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\venv\Scripts\pip.exe" install -r requirements.txt

Write-Host "========================================================" -ForegroundColor Green
Write-Host "  Tudo pronto! Para executar o sistema:" -ForegroundColor Green
Write-Host "  .\venv\Scripts\python.exe main.py" -ForegroundColor Yellow
Write-Host "========================================================" -ForegroundColor Green
