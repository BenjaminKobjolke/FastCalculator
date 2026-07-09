@echo off
REM Initial project setup: create the virtual env and install all dependencies.
where uv >nul 2>nul
if errorlevel 1 (
    echo uv is not installed. Install it from https://docs.astral.sh/uv/ first.
    exit /b 1
)
uv sync --all-extras
if errorlevel 1 exit /b 1
call tools\run_tests.bat
