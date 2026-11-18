@echo off
chcp 65001 >nul
title Cortes AI Studio - Painel Web e Piloto Automatico (Combo)
echo =======================================================================
echo     CORTES AI STUDIO - COMBO COMPLETO (PAINEL + REDES SOCIAIS)
echo =======================================================================
echo.
echo   [✓] Painel Web Interativo (Criador, Galeria e Players)
echo   [✓] Rastreamento Viral de GTA 6 integrado (YouTube)
echo   [✓] Postagem Tripla: YouTube Shorts + Instagram Reels + TikTok
echo   [✓] Agendamento Automatico no Windows (3 videos/dia: 11:30, 16:30, 20:30)
echo.
echo =======================================================================
echo.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [!] Ambiente virtual nao encontrado. Executando instalador inicial...
    call setup_env.bat
)

:: Libera a porta 5000 se houver algum processo anterior rodando (garante codigo atualizado)
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 5000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

:: Evita abertura duplicada pelo app.py pois abriremos todas as abas no Google Chrome abaixo
set NO_BROWSER=1

:: Localiza o executavel do Google Chrome
set "CHROME_BIN=C:\Program Files\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_BIN%" set "CHROME_BIN=C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME_BIN%" set "CHROME_BIN=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

echo [*] Abrindo Painel Web e Redes Sociais no GOOGLE CHROME...
echo     -> Painel Cortes AI:  http://localhost:5000
echo     -> Instagram:         https://www.instagram.com/castro93c
echo     -> TikTok:            https://www.tiktok.com/@castro93c
echo     -> YouTube:           https://www.youtube.com
echo.

if exist "%CHROME_BIN%" (
    start "" "%CHROME_BIN%" "http://localhost:5000" "https://www.instagram.com/castro93c" "https://www.tiktok.com/@castro93c" "https://www.youtube.com"
) else (
    start "" "http://localhost:5000"
    start "" "https://www.instagram.com/castro93c"
    start "" "https://www.tiktok.com/@castro93c"
    start "" "https://www.youtube.com"
)

echo [*] Servidor Cortes AI Studio iniciando...
.\venv\Scripts\python.exe app.py
pause
