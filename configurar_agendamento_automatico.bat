@echo off
chcp 65001 >nul
title Cortes AI - Configurar Agendamento Automatico 3x ao Dia
echo ========================================================
echo   Configurando Agendamento Automatico no Windows
echo   3 Videos Virais de GTA 6 por dia (11:30, 16:30, 20:30)
echo ========================================================
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command "$Action = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument '/c \"\"C:\Users\fabia\OneDrive\Desktop\cortes\executar_auto_viral.bat\"\"'; $T1 = New-ScheduledTaskTrigger -Daily -At '11:30'; $T2 = New-ScheduledTaskTrigger -Daily -At '16:30'; $T3 = New-ScheduledTaskTrigger -Daily -At '20:30'; Register-ScheduledTask -TaskName 'CortesAI_GTA6_Viral' -Action $Action -Trigger @($T1, $T2, $T3) -Description 'Publicacao automatica de 3 videos virais de GTA 6 por dia' -Force"

echo.
echo ========================================================
echo   Tarefa Agendada com Sucesso no Windows Task Scheduler!
echo   Nome da Tarefa: CortesAI_GTA6_Viral
echo   Horarios: 11:30, 16:30 e 20:30 todos os dias.
echo ========================================================
pause
