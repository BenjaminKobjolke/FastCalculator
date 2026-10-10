@echo off
cd %~dp0..

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0increment_version.ps1"

REM %errorlevel% is expanded before cd runs, so the tool's exit code survives the cd.
cd %~dp0 & exit /b %errorlevel%
