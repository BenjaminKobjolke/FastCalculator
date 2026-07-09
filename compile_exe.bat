@echo off
REM Build a standalone Calculator.exe with PyInstaller.
REM Optional: create compile_settings.bat (from the .example) to set OUTPUT_PATH.
if exist compile_settings.bat call compile_settings.bat

REM Ensure pyinstaller (dev group) is installed.
uv sync --all-extras
if errorlevel 1 exit /b 1

REM Release the file lock if an instance is running.
taskkill /IM Calculator.exe /F >nul 2>&1

if defined OUTPUT_PATH (
    uv run pyinstaller --name Calculator --onefile --windowed --noconfirm main.py --distpath "%OUTPUT_PATH%"
) else (
    uv run pyinstaller --name Calculator --onefile --windowed --noconfirm main.py
)
pause
