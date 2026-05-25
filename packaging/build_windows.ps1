# Build standalone Windows .exe (PowerShell; Python 3.14)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== ASKABR-L Windows build ==="

$python = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    try {
        $python = (& py -3.14 -c "import sys; print(sys.executable)" 2>$null).Trim()
    } catch {
        $python = $null
    }
}
if (-not $python) {
    $python = (& python packaging/resolve_python314.py 2>$null).Trim()
}
if (-not $python) {
    Write-Error @"
Python 3.14 not found.
Install from https://www.python.org/downloads/
Enable 'Add python.exe to PATH' and the Python launcher, then run: py -3.14 --version
"@
}

Write-Host "Using: $python"
& $python packaging/build_windows.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "Build succeeded. Output: dist\ASKABR-L.exe"
