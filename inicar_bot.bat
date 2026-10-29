@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ERRO: Python do ambiente virtual nao encontrado.
    echo Confere se a pasta .venv existe.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" bot.py

echo.
echo O bot foi encerrado. Verifica as mensagens acima.
pause