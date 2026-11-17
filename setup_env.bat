@echo off
chcp 65001 >nul
echo ========================================================
echo   Instalador do Ambiente - Cortes AI (Shorts e Reels)
echo ========================================================
echo.

:: Verificar se Python está instalado
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python não encontrado. Instalando Python 3.11 via Winget...
    winget install --id Python.Python.3.11 -e --source winget --accept-package-agreements --accept-source-agreements
    if %ERRORLEVEL% NEQ 0 (
        echo [ERRO] Falha ao instalar Python automaticamente.
        echo Por favor, instale o Python manualmente em: https://www.python.org/downloads/
        echo Lembre-se de marcar a opção "Add Python to PATH" durante a instalação.
        pause
        exit /b 1
    )
    echo [OK] Python instalado! Reiniciando variáveis de ambiente...
)

:: Verificar se Git está instalado
git --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Git não encontrado. Deseja instalar via winget?
    winget install --id Git.Git -e --source winget --accept-package-agreements --accept-source-agreements
)

:: Criar ambiente virtual se não existir
if not exist "venv" (
    echo [*] Criando ambiente virtual (venv)...
    python -m venv venv
)

echo [*] Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo [*] Atualizando pip...
python -m pip install --upgrade pip

echo [*] Instalando dependências do requirements.txt...
pip install -r requirements.txt

echo.
echo ========================================================
echo   Ambiente configurado com sucesso!
echo   Para iniciar, execute: venv\Scripts\python main.py
echo ========================================================
echo.
pause
