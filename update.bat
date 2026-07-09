@echo off
REM Update dependencies, then lint, type-check and test.
uv lock --upgrade
if errorlevel 1 exit /b 1
uv sync --all-extras
if errorlevel 1 exit /b 1
uv run ruff check .
if errorlevel 1 exit /b 1
uv run ruff format --check .
if errorlevel 1 exit /b 1
uv run mypy .
if errorlevel 1 exit /b 1
call tools\run_tests.bat
