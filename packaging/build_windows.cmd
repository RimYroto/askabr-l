@echo off
REM Build ASKABR-L.exe — safe for non-ASCII (Cyrillic) user names and project paths.
chcp 65001 >nul 2>&1
setlocal EnableExtensions
cd /d "%~dp0\.."

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

echo === ASKABR-L Windows build ===

where py >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  py -3.14 packaging\build_windows.py %*
  if errorlevel 1 goto :failed
  goto :success
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
  python packaging\build_windows.py %*
  if errorlevel 1 goto :failed
  goto :success
)

echo ERROR: Python 3.14 not found.
echo Install from https://www.python.org/downloads/
echo Enable "Add python.exe to PATH" and the Python launcher, then run: py -3.14 --version
exit /b 1

:failed
echo.
echo Build FAILED. See dist\build.log for details.
exit /b 1

:success
echo.
echo Build succeeded. Output: dist\ASKABR-L.exe
echo Log: dist\build.log
exit /b 0
