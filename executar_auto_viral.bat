@echo off
chcp 65001 >nul
cd /d "C:\Users\fabia\OneDrive\Desktop\cortes"
if not exist "config" mkdir config
echo ======================================================== >> config\automation_runner.log
echo [%date% %time%] Iniciando rastreamento e postagem de video viral GTA 6 >> config\automation_runner.log
.\venv\Scripts\python.exe src\auto_viral_finder.py --count 1 >> config\automation_runner.log 2>&1
echo [%date% %time%] Ciclo finalizado com sucesso! >> config\automation_runner.log
