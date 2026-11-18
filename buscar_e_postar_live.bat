@echo off
chcp 65001 >nul
title Cortes AI Studio - Sniper de Clipes de Lives (Twitch & YT)
echo =======================================================================
echo     CORTES AI STUDIO - RADAR E SNIPER DE LIVES AO VIVO
echo =======================================================================
echo.
echo   [✓] Rastreamento de Clipes Virais de Streamers (Twitch e YouTube)
echo   [✓] Regra Estrita: Somente vídeos com 10 segundos ou mais
echo   [✓] Conversao 9:16 vertical + Gancho Viral + Marca @castro93c
echo   [✓] Postagem Tripla: YouTube Shorts + Instagram Reels + TikTok
echo.
echo =======================================================================
echo.
cd /d "%~dp0"

if not exist "venv\Scripts\python.exe" (
    echo [!] Ambiente virtual nao encontrado. Executando instalador inicial...
    call setup_env.bat
)

echo [*] Buscando o clipe viral da semana (maior visualizacao, min 10 segundos)...
.\venv\Scripts\python.exe -c "from src.live_clipper import run_live_sniper_best_clip; res = run_live_sniper_best_clip(auto_upload=True); print('Resultado:', res)"

echo.
echo =======================================================================
echo   Processo de Live concluído!
echo =======================================================================
pause
