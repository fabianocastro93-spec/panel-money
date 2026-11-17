@echo off
chcp 65001 >nul
title Cortes AI Studio - Painel Web
echo ========================================================
echo   Iniciando Cortes AI Studio (Painel Web no Navegador)
echo ========================================================
echo.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [!] Ambiente virtual nao encontrado. Executando instalador inicial...
    call setup_env.bat
)

:: Libera a porta 5000 se houver algum processo anterior
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo [*] Abrindo o painel no seu navegador: http://localhost:5000 ...
start "" http://localhost:5000

.\venv\Scripts\python.exe app.py
pause
