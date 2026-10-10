@echo off
REM One-command release launcher. cd into the release-tool repo so `uv run`
REM resolves its venv (release-tool is not on PATH), then point create back at
REM this project. %* passes --internal / --dry-run straight through.
REM Preflight: fail before the version bump and build, not at the publish gate after them.
if not exist "%~dp0publish_settings.ini" (
  echo ERROR: "%~dp0publish_settings.ini" is missing. Copy publish_settings_example.ini and configure it.
  exit /b 1
)
if not exist "D:\GIT\BenjaminKobjolke\release-tool\ftp_profiles.ini" (
  echo ERROR: "D:\GIT\BenjaminKobjolke\release-tool\ftp_profiles.ini" is missing. Copy examples\ftp_profiles.ini and add the FTP profile.
  exit /b 1
)
cd /d D:\GIT\BenjaminKobjolke\release-tool
call uv run python -m release_tool create "%~dp0release_create.ini" --project-root "%~dp0.." %*
REM %errorlevel% is expanded before cd runs, so the tool's exit code survives the cd.
cd /d "%~dp0" & exit /b %errorlevel%
