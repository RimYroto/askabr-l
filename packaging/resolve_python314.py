# -*- coding: utf-8 -*-
"""Находит интерпретатор Python 3.14 (для сборки Windows .exe)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REQUIRED_MAJOR = 3
REQUIRED_MINOR = 14


def _version_tuple(executable: str) -> tuple[int, int] | None:
    try:
        result = subprocess.run(
            [executable, "-c", "import sys; print(sys.version_info[0], sys.version_info[1])"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    parts = result.stdout.strip().split()
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _executable_for_command(command: list[str]) -> str | None:
    try:
        result = subprocess.run(
            [*command, "-c", "import sys; print(sys.executable)"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    exe = result.stdout.strip()
    if not exe:
        return None
    version = _version_tuple(exe)
    if version == (REQUIRED_MAJOR, REQUIRED_MINOR):
        return exe
    return None


def candidate_commands() -> list[list[str]]:
    if sys.platform == "win32":
        return [
            ["py", "-3.14"],
            ["py", "-3", "-V:3.14"],
            ["python3.14"],
            ["python"],
        ]
    return [
        ["python3.14"],
        ["python3"],
        ["python"],
    ]


def resolve_python314_executable() -> str | None:
    for command in candidate_commands():
        exe = _executable_for_command(command)
        if exe:
            return exe
    return None


def main() -> None:
    exe = resolve_python314_executable()
    if exe is None:
        print(
            "Python 3.14 not found.\n"
            "Install from https://www.python.org/downloads/ (Windows: enable 'py launcher' and PATH).\n"
            "Then verify: py -3.14 --version",
            file=sys.stderr,
        )
        raise SystemExit(1)
    print(exe)


if __name__ == "__main__":
    main()
