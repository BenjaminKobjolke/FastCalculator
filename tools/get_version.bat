@echo off
setlocal enabledelayedexpansion

cd %~dp0..

:: Read version from version.txt using PowerShell script
for /f "usebackq delims=" %%a in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0get_version.ps1"`) do (
    set "VERSION=%%a"
)

if defined VERSION (
    echo !VERSION!
) else (
    echo Could not determine version
)

cd %~dp0
