@echo off
REM Build ASKABR-L.exe from Command Prompt (calls packaging\build_windows.cmd)
setlocal
cd /d "%~dp0\.."
call packaging\build_windows.cmd %*
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" (
  echo.
  echo Build FAILED with exit code %ERR%.
  if exist "dist\build.log" echo See dist\build.log
  pause
  exit /b %ERR%
)
if /i "%~1"=="--no-pause" exit /b 0
echo.
echo Build succeeded: dist\ASKABR-L.exe
pause
exit /b 0
