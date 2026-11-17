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

:: Liberar porta 5000 caso tenha ficado algum processo anterior aberto
for /f "tokens=5" %%a in ('netstat -aon ^| findstr :5000 ^| findstr LISTENING') do (
    echo [*] Liberando porta 5000 (encerrando processo anterior %%a)...
    taskkill /F /PID %%a >nul 2>&1
)

echo [*] Abrindo o painel no seu navegador: http://localhost:5000 ...
start "" http://localhost:5000

.\venv\Scripts\python.exe app.py
pause
