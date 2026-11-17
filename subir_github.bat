@echo off
chcp 65001 >nul
title Enviar Projeto para o GitHub - Cortes AI Studio
echo ========================================================
echo   Enviando Cortes AI Studio para o seu GitHub
echo   Repositorio: https://github.com/fabianocastro93-spec/panel-money
echo ========================================================
echo.
cd /d "%~dp0"

echo [*] Verificando conexao com a branch main...
git branch -M main

echo [*] Enviando codigo para o GitHub...
echo (Se for o primeiro acesso, seu navegador vai abrir para autorizar com 1 clique)
echo.
git push -u origin main

if %errorlevel% neq 0 (
    echo.
    echo [!] Se pediu login e nao abriu, autentique com 1 comando:
    echo     gh auth login
    echo     git push -u origin main
    echo.
) else (
    echo.
    echo ========================================================
    echo   SUCESSO! Projeto enviado com sucesso para o GitHub:
    echo   https://github.com/fabianocastro93-spec/panel-money
    echo ========================================================
)

pause
