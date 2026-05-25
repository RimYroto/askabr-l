@echo off
setlocal EnableExtensions
cd /d "%~dp0\.."

echo === ASKABR-L Windows build ===

set "PYEXE="
where py >nul 2>&1 && (
  for /f "usebackq delims=" %%P in (`py -3.14 -c "import sys; print(sys.executable)" 2^>nul`) do set "PYEXE=%%P"
)
if not defined PYEXE (
  for /f "usebackq delims=" %%P in (`python packaging\resolve_python314.py 2^>nul`) do set "PYEXE=%%P"
)
if not defined PYEXE (
  echo ERROR: Python 3.14 not found.
  echo Install from https://www.python.org/downloads/
  echo Enable "Add python.exe to PATH" and the Python launcher, then run: py -3.14 --version
  exit /b 1
)

echo Using: %PYEXE%
"%PYEXE%" packaging\build_windows.py
set "ERR=%ERRORLEVEL%"
if not "%ERR%"=="0" exit /b %ERR%

echo.
echo Build succeeded. Output: dist\ASKABR-L.exe
exit /b 0
