# Build standalone Windows .exe (run from repo root on Windows 10/11 x64)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

Write-Host "Creating build venv..."
python -m venv .venv-build
& .\.venv-build\Scripts\pip install -U pip
& .\.venv-build\Scripts\pip install -e ".[packaging]"
& .\.venv-build\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu

Write-Host "Running PyInstaller..."
& .\.venv-build\Scripts\pyinstaller packaging/askabr_l_gui.spec --noconfirm

Write-Host ""
Write-Host "Done. Output: dist\ASKABR-L.exe"
Write-Host "Expected size: ~400-800 MB (PyTorch CPU + model weights)."
