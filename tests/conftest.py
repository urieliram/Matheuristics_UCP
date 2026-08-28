"""Shared fixtures: build an isolated sandbox so a run never touches the repo working tree.

main.py writes stat.csv, solHard3_*.csv and logfile*.log into the *current* directory, and on a
re-run it recovers a previously saved solution instead of recomputing it (see the path.exists check
in main.py). Both make in-place runs non-reproducible, so every test runs in a fresh directory.
"""
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
MODULES = ["main.py", "uc_Co.py", "reading.py", "solution.py", "util.py", "routines.py", "Extract.py"]


def _write_config(dest: Path, overrides: dict) -> None:
    """Copy config.con, replacing the given keys."""
    lines = (REPO / "config.con").read_text().splitlines()
    out = []
    for line in lines:
        key = line.split(",", 1)[0]
        out.append(f"{key},{overrides[key]}" if key in overrides else line)
    dest.write_text("\n".join(out) + "\n")


@pytest.fixture
def sandbox(tmp_path):
    """A throwaway copy of the code with instances/ linked back to the repo."""
    for name in MODULES:
        shutil.copy(REPO / name, tmp_path / name)
    os.symlink(REPO / "instances", tmp_path / "instances")
    return tmp_path


@pytest.fixture
def run_instance(sandbox):
    """Run `python3 main.py <instance> yalma` inside the sandbox; return (stdout, stat_row)."""
    def _run(instance="uc_057.json", timeout=900, **config):
        _write_config(sandbox / "config.con", config)
        proc = subprocess.run(
            [sys.executable, "main.py", instance, "yalma"],
            cwd=sandbox, capture_output=True, text=True, timeout=timeout,
        )
        stat = sandbox / "stat.csv"
        row = stat.read_text().strip().split(",") if stat.exists() else None
        return proc, row
    return _run
