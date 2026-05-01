@echo off
REM claude-codex-dispatch Windows launcher
REM Resolves python interpreter and forwards args to codex_dispatch_role.py

setlocal
set "SCRIPT_DIR=%~dp0.."
set "WRAPPER=%SCRIPT_DIR%\scripts\codex_dispatch_role.py"

if not exist "%WRAPPER%" (
  echo Error: wrapper not found at %WRAPPER% 1>&2
  exit /b 1
)

where py >nul 2>&1
if %errorlevel% equ 0 (
  py -3 "%WRAPPER%" %*
  exit /b %errorlevel%
)

where python >nul 2>&1
if %errorlevel% equ 0 (
  python "%WRAPPER%" %*
  exit /b %errorlevel%
)

echo Error: py or python required but not found in PATH. 1>&2
exit /b 1
