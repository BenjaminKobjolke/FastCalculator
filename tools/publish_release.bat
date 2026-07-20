@echo off
REM Update --previous-version before each release (see docs\CREATE_NEW_RELEASE.md).
REM Needs a local tools\publish_settings.ini (copy from publish_settings_example.ini).
set "EXE=%~dp0..\dist\FastCalculator.exe"
if exist "%~dp0compile_settings.bat" call "%~dp0compile_settings.bat"
if defined OUTPUT_PATH set "EXE=%OUTPUT_PATH%\FastCalculator.exe"

if not exist "%EXE%" (
    echo ERROR: %EXE% not found. Run tools\build.bat first.
    exit /b 1
)

cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool "%EXE%" "%~dp0publish_settings.ini" --previous-version 0.1.1 --verbose
cd /d "%~dp0"
