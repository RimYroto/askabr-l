# Build standalone Windows .exe (PowerShell; Python 3.14; Unicode-safe)
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [Console]::OutputEncoding

$Root = Split-Path $PSScriptRoot -Parent
Set-Location -LiteralPath $Root
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Host "=== ASKABR-L Windows build ==="

$launcher = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $launcher = @("py", "-3.14")
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $launcher = @("python")
} else {
    Write-Error @"
Python 3.14 not found.
Install from https://www.python.org/downloads/
Enable 'Add python.exe to PATH' and the Python launcher, then run: py -3.14 --version
"@
}

$buildScript = Join-Path $Root "packaging\build_windows.py"
& @launcher $buildScript
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Build succeeded. Output: dist\ASKABR-L.exe"
