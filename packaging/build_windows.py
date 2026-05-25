# -*- coding: utf-8 -*-
"""Сборка ASKABR-L.exe на Windows (Python 3.14)."""

from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_EXE_MB = 50


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _reexec_if_needed() -> Path:
    resolve = _load_module("resolve_python314", ROOT / "packaging" / "resolve_python314.py")
    if sys.version_info[:2] == (3, 14):
        return Path(sys.executable)

    target = resolve.resolve_python314_executable()
    if target is None:
        resolve.main()
        raise SystemExit(1)

    target_path = Path(target).resolve()
    if Path(sys.executable).resolve() == target_path:
        return target_path

    print(f"Re-launching build with Python 3.14: {target_path}")
    os.execv(str(target_path), [str(target_path), *sys.argv])


def _run(cmd: list[str], *, cwd: Path, windows_paths) -> None:
    print("+", " ".join(cmd))
    kwargs = {"cwd": cwd, "check": True}
    if sys.platform == "win32":
        kwargs.update(windows_paths.subprocess_text_kwargs())
    subprocess.run(cmd, **kwargs)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("build_windows.py must be run on Windows 10/11 (64-bit).")

    windows_paths = _load_module("windows_paths", ROOT / "packaging" / "windows_paths.py")
    windows_paths.configure_unicode_env()

    python = _reexec_if_needed()
    preflight = _load_module("preflight", ROOT / "packaging" / "preflight.py")

    print("=== ASKABR-L Windows build (Python 3.14) ===")
    preflight.assert_python_version(build=True)
    preflight.assert_release_models(ROOT)

    paths = windows_paths.prepare_build_paths(ROOT)
    venv_dir = paths["venv"]
    dist_exe = paths["dist"] / "ASKABR-L.exe"

    if venv_dir.exists():
        print(f"Removing previous build venv: {venv_dir}")
        import shutil

        shutil.rmtree(venv_dir)
    venv_dir.mkdir(parents=True, exist_ok=True)

    print(f"Project: {paths['project']}")
    print(f"Build cache (ASCII): {paths['cache']}")

    print("Creating build venv...")
    _run([str(python), "-m", "venv", str(venv_dir)], cwd=paths["project"], windows_paths=windows_paths)

    pip = venv_dir / "Scripts" / "pip.exe"
    pyinstaller = venv_dir / "Scripts" / "pyinstaller.exe"

    _run([str(pip), "install", "-U", "pip", "wheel", "setuptools"], cwd=paths["project"], windows_paths=windows_paths)
    print("Installing PyTorch (CPU) for cp314...")
    _run(
        [
            str(pip),
            "install",
            "torch",
            "torchvision",
            "--index-url",
            "https://download.pytorch.org/whl/cpu",
        ],
        cwd=paths["project"],
        windows_paths=windows_paths,
    )
    print("Installing project and PyInstaller...")
    _run(
        [str(pip), "install", "pyinstaller>=6.10", "pyinstaller-hooks-contrib>=2025.4"],
        cwd=paths["project"],
        windows_paths=windows_paths,
    )
    _run(
        [str(pip), "install", "-e", ".[packaging]", "--no-deps"],
        cwd=paths["project"],
        windows_paths=windows_paths,
    )
    _run(
        [str(pip), "install", "PyYAML", "Pillow", "numpy", "PyQt6", "certifi"],
        cwd=paths["project"],
        windows_paths=windows_paths,
    )

    print("Running PyInstaller...")
    _run(
        [
            str(pyinstaller),
            "packaging/askabr_l_gui.spec",
            "--noconfirm",
            "--clean",
            "--distpath",
            str(paths["pyi_dist"]),
            "--workpath",
            str(paths["pyi_work"]),
        ],
        cwd=paths["project"],
        windows_paths=windows_paths,
    )

    try:
        windows_paths.copy_built_exe(paths["pyi_dist"], dist_exe)
    except FileNotFoundError as exc:
        raise SystemExit(str(exc)) from exc

    size_mb = round(dist_exe.stat().st_size / (1024 * 1024), 1)
    if size_mb < MIN_EXE_MB:
        raise SystemExit(
            f"ASKABR-L.exe is only {size_mb} MB — expected at least {MIN_EXE_MB} MB. "
            "Check the PyInstaller log above."
        )

    print()
    print(f"Done. Output: {dist_exe} ({size_mb} MB)")
    print("Copy docs\\INSTRUKCIYA.txt next to the exe for end users.")


if __name__ == "__main__":
    main()
