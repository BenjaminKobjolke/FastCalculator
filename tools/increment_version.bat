@echo off
cd %~dp0..

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0increment_version.ps1"

cd %~dp0
