@echo off
setlocal
cd /d %~dp0
set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m codex_accmgr %*
  exit /b %errorlevel%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python -m codex_accmgr %*
  exit /b %errorlevel%
)

echo Python 3 not found. Please install Python 3.10+ and retry.
exit /b 1
