@echo off
setlocal EnableExtensions

set "ROOT=C:\jobradar-engineer"
cd /d "%ROOT%" || exit /b 1

if not exist "%ROOT%\logs" mkdir "%ROOT%\logs"

for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%I"
if "%TS%"=="" set "TS=%DATE:/=-%_%TIME::=-%"

set "LOG_FILE=%ROOT%\logs\jobradar_dry_run_%TS%.log"

echo [%DATE% %TIME%] Starting JobRadar dry-run > "%LOG_FILE%"
echo Root: %ROOT% >> "%LOG_FILE%"

if exist "%ROOT%\.venv\Scripts\activate.bat" (
    echo Activating virtual environment >> "%LOG_FILE%"
    call "%ROOT%\.venv\Scripts\activate.bat" >> "%LOG_FILE%" 2>&1
) else (
    echo Virtual environment not found. Using system Python. >> "%LOG_FILE%"
)

python -m src.main --source mock --analyze --dry-run --min-score 50 --analysis-min-score 50 >> "%LOG_FILE%" 2>&1
set "EXIT_CODE=%ERRORLEVEL%"

echo [%DATE% %TIME%] Finished with exit code %EXIT_CODE% >> "%LOG_FILE%"
exit /b %EXIT_CODE%
