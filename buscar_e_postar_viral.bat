@echo off
chcp 65001 >nul
title Cortes AI - Piloto Automatico de Videos Virais GTA 6
echo ========================================================
echo   Cortes AI Studio - Piloto Automatico de Videos Virais
echo   Rastreia YouTube, Recorta em 9:16 e Posta Automaticamente
echo ========================================================
echo.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [!] Ambiente virtual nao encontrado. Executando instalador inicial...
    call setup_env.bat
)

echo [*] Analisando o YouTube em busca dos vídeos mais assistidos de GTA 6...
echo [*] Baixando o melhor vídeo, transcrevendo e criando o corte 9:16...
echo [*] Publicando automaticamente no YouTube Shorts e Instagram Reels...
echo.

.\venv\Scripts\python.exe src\auto_viral_finder.py %*

echo.
echo ========================================================
echo   Ciclo concluido! Verifique a Galeria no painel web:
echo   http://localhost:5000
echo ========================================================
pause
