@echo off
REM Previous (online) version for backup-folder naming: %1 if given, else read
REM from tools\previous_version.txt (written by release_create.bat). Empty makes
REM the tool fall back to timestamp-named backups.
REM Needs a local tools\publish_settings.ini (copy from publish_settings_example.ini).
set "PREV=%~1"
if not defined PREV if exist "%~dp0previous_version.txt" set /p "PREV="<"%~dp0previous_version.txt"
set "EXE=%~dp0..\dist\FastCalculator.exe"
if exist "%~dp0compile_settings.bat" call "%~dp0compile_settings.bat"
if defined OUTPUT_PATH set "EXE=%OUTPUT_PATH%\FastCalculator.exe"

if not exist "%EXE%" (
    echo ERROR: %EXE% not found. Run tools\build.bat first.
    exit /b 1
)

cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool "%EXE%" "%~dp0publish_settings.ini" --previous-version "%PREV%" --verbose
cd /d "%~dp0"
