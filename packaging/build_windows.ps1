# Build standalone Windows .exe (run from repo root on Windows 10/11 x64)
$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

Write-Host "=== ASKABR-L Windows build ==="

Write-Host "Checking Python and model weights..."
python packaging/preflight.py
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$venv = Join-Path $Root ".venv-build"
if (Test-Path $venv) {
    Write-Host "Removing previous build venv..."
    Remove-Item -Recurse -Force $venv
}

Write-Host "Creating build venv..."
python -m venv $venv
$pip = Join-Path $venv "Scripts\pip.exe"
$pyinstaller = Join-Path $venv "Scripts\pyinstaller.exe"

& $pip install -U pip wheel setuptools

Write-Host "Installing PyTorch (CPU)..."
& $pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

Write-Host "Installing project and PyInstaller..."
& $pip install "pyinstaller>=6.10" "pyinstaller-hooks-contrib>=2025.4"
& $pip install -e ".[packaging]" --no-deps
& $pip install PyYAML Pillow numpy PyQt6 certifi

Write-Host "Running PyInstaller..."
& $pyinstaller packaging/askabr_l_gui.spec --noconfirm --clean
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$exe = Join-Path $Root "dist\ASKABR-L.exe"
if (-not (Test-Path $exe)) {
    throw "Build finished but $exe was not created."
}
$sizeMb = [math]::Round((Get-Item $exe).Length / 1MB, 1)
if ($sizeMb -lt 50) {
    throw "ASKABR-L.exe is only ${sizeMb} MB — expected hundreds of MB. Check PyInstaller log."
}

Write-Host ""
Write-Host "Done. Output: dist\ASKABR-L.exe ($sizeMb MB)"
Write-Host "Copy docs\INSTRUKCIYA.txt next to the exe for end users."
