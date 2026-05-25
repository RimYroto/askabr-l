# -*- coding: utf-8 -*-
"""Сборка ASKABR-L.exe на Windows (Python 3.14, onefile)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIN_EXE_MB = 50
SMOKE_TIMEOUT_SEC = 120


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


class _Tee:
    def __init__(self, *streams) -> None:
        self._streams = streams

    def write(self, data: str) -> int:
        for stream in self._streams:
            try:
                stream.write(data)
                stream.flush()
            except ValueError:
                pass
        return len(data)

    def flush(self) -> None:
        for stream in self._streams:
            try:
                stream.flush()
            except ValueError:
                pass


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
    line = "+ " + " ".join(cmd) + "\n"
    print(line, end="")
    kwargs = {"cwd": cwd, "check": True, "stdout": sys.stdout, "stderr": subprocess.STDOUT}
    kwargs.update(windows_paths.subprocess_text_kwargs())
    subprocess.run(cmd, **kwargs)


def _run_smoke(exe: Path, smoke_log: Path) -> None:
    cmd = [str(exe), "--smoke-test"]
    print(f"Running smoke test: {' '.join(cmd)}")
    with smoke_log.open("w", encoding="utf-8") as log:
        log.write("+ " + " ".join(cmd) + "\n")
        log.flush()
        try:
            result = subprocess.run(
                cmd,
                cwd=exe.parent,
                timeout=SMOKE_TIMEOUT_SEC,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except subprocess.TimeoutExpired as exc:
            raise SystemExit(
                f"Smoke test timed out after {SMOKE_TIMEOUT_SEC}s. See {smoke_log}"
            ) from exc
    if result.returncode != 0:
        raise SystemExit(f"Smoke test failed (exit {result.returncode}). See {smoke_log}")
    print("Smoke test passed.")


def _build(paths: dict, windows_paths, python: Path, preflight, *, skip_smoke: bool) -> None:
    build_cwd = paths["build_cwd"]
    dist_exe = paths["dist"] / "ASKABR-L.exe"
    constraints = build_cwd / "packaging" / "constraints-build.txt"

    print("=== ASKABR-L Windows build (Python 3.14, onefile) ===")
    preflight.assert_python_version(build=True)
    preflight.assert_release_models(ROOT)

    print(f"Project: {paths['project']}")
    print(f"Staging (ASCII): {build_cwd}")
    print(f"Build cache: {paths['cache']}")
    print(f"Build log: {paths['dist_build_log']}")

    venv_dir = paths["venv"]
    if venv_dir.exists():
        print(f"Removing previous build venv: {venv_dir}")
        import shutil

        shutil.rmtree(venv_dir)
    venv_dir.mkdir(parents=True, exist_ok=True)

    pip = venv_dir / "Scripts" / "pip.exe"
    pyinstaller = venv_dir / "Scripts" / "pyinstaller.exe"

    _run([str(python), "-m", "venv", str(venv_dir)], cwd=build_cwd, windows_paths=windows_paths)
    _run([str(pip), "install", "-U", "pip", "wheel", "setuptools"], cwd=build_cwd, windows_paths=windows_paths)

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
        cwd=build_cwd,
        windows_paths=windows_paths,
    )

    print("Installing build constraints...")
    _run(
        [str(pip), "install", "-r", str(constraints)],
        cwd=build_cwd,
        windows_paths=windows_paths,
    )

    print("Installing project (non-editable from staging)...")
    _run([str(pip), "install", "."], cwd=build_cwd, windows_paths=windows_paths)

    print("Running PyInstaller...")
    with paths["pyinstaller_log"].open("w", encoding="utf-8") as pyi_log:
        pyi_log.write("PyInstaller output\n")
        pyi_log.flush()
        kwargs = {
            "cwd": build_cwd,
            "check": True,
            "stdout": pyi_log,
            "stderr": subprocess.STDOUT,
        }
        kwargs.update(windows_paths.subprocess_text_kwargs())
        subprocess.run(
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
            **kwargs,
        )

    windows_paths.copy_built_exe(paths["pyi_dist"], dist_exe)

    size_mb = round(dist_exe.stat().st_size / (1024 * 1024), 1)
    if size_mb < MIN_EXE_MB:
        raise SystemExit(
            f"ASKABR-L.exe is only {size_mb} MB — expected at least {MIN_EXE_MB} MB. "
            f"See {paths['dist_build_log']}"
        )

    if not skip_smoke:
        _run_smoke(dist_exe, paths["smoke_log"])

    print()
    print(f"Done. Output: {dist_exe.resolve()} ({size_mb} MB)")
    print(f"Build log: {paths['dist_build_log'].resolve()}")
    if not skip_smoke:
        print(f"Smoke log: {paths['dist_smoke_log'].resolve()}")
    print("Copy docs\\INSTRUKCIYA.txt next to the exe for end users.")


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("build_windows.py must be run on Windows 10/11 (64-bit).")

    parser = argparse.ArgumentParser(description="Build ASKABR-L.exe (Windows onefile).")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Build with console window (ASKABR_BUILD_DEBUG=1) for troubleshooting.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip post-build smoke test.",
    )
    args = parser.parse_args()

    windows_paths = _load_module("windows_paths", ROOT / "packaging" / "windows_paths.py")
    windows_paths.configure_unicode_env()

    python = _reexec_if_needed()
    preflight = _load_module("preflight", ROOT / "packaging" / "preflight.py")

    if args.debug:
        os.environ["ASKABR_BUILD_DEBUG"] = "1"
    else:
        os.environ.pop("ASKABR_BUILD_DEBUG", None)

    paths = windows_paths.prepare_build_paths(ROOT)
    original_stdout = sys.stdout
    exit_code = 1

    try:
        with paths["build_log"].open("w", encoding="utf-8") as log_file:
            sys.stdout = _Tee(original_stdout, log_file)  # type: ignore[assignment]
            try:
                _build(paths, windows_paths, python, preflight, skip_smoke=args.skip_smoke)
                exit_code = 0
            except subprocess.CalledProcessError as exc:
                print(f"\nBUILD FAILED: command exited with code {exc.returncode}")
                print(f"Command: {' '.join(exc.cmd)}")
                raise SystemExit(1) from exc
            except SystemExit as exc:
                if exc.code not in (None, 0):
                    print(f"\nBUILD FAILED (exit {exc.code})")
                raise
    finally:
        sys.stdout = original_stdout
        windows_paths.publish_build_logs(paths)
        if exit_code != 0:
            print(f"\nBuild failed. See log: {paths['dist_build_log']}", file=original_stdout)

    raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
