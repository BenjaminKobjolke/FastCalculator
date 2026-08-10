@echo off
REM One-command release launcher. cd into the release-tool repo so `uv run`
REM resolves its venv (release-tool is not on PATH), then point create back at
REM this project. %* passes --internal / --dry-run straight through.
cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool create "%~dp0release_create.ini" --project-root "%~dp0.." %*
cd /d "%~dp0"
