@echo off
REM Build ASKABR-L.exe from Command Prompt (calls packaging\build_windows.cmd)
setlocal
cd /d "%~dp0\.."
call packaging\build_windows.cmd %*
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo Build failed with exit code %ERR%.
  pause
  exit /b %ERR%
)
if /i "%~1"=="--no-pause" exit /b 0
pause
exit /b 0
