@echo off
setlocal EnableExtensions

set "ROOT=C:\jobradar-engineer"
cd /d "%ROOT%" || exit /b 1

if exist "%ROOT%\.venv\Scripts\activate.bat" (
    call "%ROOT%\.venv\Scripts\activate.bat"
)

streamlit run dashboard.py
