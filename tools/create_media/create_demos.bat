@echo off
REM Records the FastCalculator demos (GIF/MP4 + stills, one run per language)
REM into tools\create_media\output\demos\<name>\<lang>\
REM using the automated-application-screenshots tool. Keep hands off mouse and
REM keyboard while the demo window is recording.
echo ========================================
echo  FastCalculator - Create Demo Media
echo ========================================
echo.
cd /d "%~dp0"
uv run --project ..\..\..\automated-application-screenshots screenshot-tool --config "%~dp0fastcalculator.json" --demo all
if errorlevel 1 (
    echo.
    echo Demo recording FAILED
    exit /b 1
)
echo.
echo Media written to %~dp0output\demos\
