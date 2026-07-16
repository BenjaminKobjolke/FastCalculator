@echo off
cd %~dp0..

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0decrement_version.ps1"

cd %~dp0
