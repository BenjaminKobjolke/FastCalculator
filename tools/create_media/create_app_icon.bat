@echo off
REM Generate the app icon via the sibling ai-image-creator project, then make a
REM .ico for the packaged .exe. Needs ai-image-creator's .env OpenAI key set.
setlocal
set CALC=D:\GIT\BenjaminKobjolke\calculator
set AIC=D:\GIT\BenjaminKobjolke\ai-image-creator

REM cd so uv resolves ai-image-creator AND the relative reference_images resolve.
cd /d "%AIC%"
call start.bat "%CALC%\tools\create_media\create_app_icon.json"
if errorlevel 1 exit /b 1

REM PNG -> ICO using calculator's own env (PySide6, no extra dependency).
REM ponytail: single-size .ico via Qt; swap for a Pillow multi-size save if the
REM Explorer thumbnail ever looks rough.
uv run --project "%CALC%" python -c "from PySide6.QtGui import QImage; QImage(r'%CALC%\assets\icon.png').save(r'%CALC%\assets\icon.ico')"
