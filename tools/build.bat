@echo off
REM Build a standalone FastCalculator.exe with PyInstaller.
REM Optional: create tools\compile_settings.bat (from the .example) to set OUTPUT_PATH.
setlocal
cd /d "%~dp0.."
if exist "%~dp0compile_settings.bat" call "%~dp0compile_settings.bat"

REM Ensure pyinstaller (dev group) is installed.
uv sync --all-extras
if errorlevel 1 exit /b 1

REM Release the file lock if an instance is running.
taskkill /IM FastCalculator.exe /F >nul 2>&1

set PYI_ARGS=--name FastCalculator --onefile --windowed --noconfirm --add-data "locales;locales" --add-data "release_notes;release_notes" --add-data "version.txt;." main.py

if defined OUTPUT_PATH (
    uv run pyinstaller %PYI_ARGS% --distpath "%OUTPUT_PATH%"
) else (
    uv run pyinstaller %PYI_ARGS%
)
