"""Run configured cached-native formatting checks inside the admitted source profile."""

from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
SOURCE = Path(__file__).resolve().parent
RUFF = Path(
    "/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff"
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    files = [
        str(p)
        for p in sorted(SOURCE.glob("*.py"))
        if p.name != "run_account_qualification.py"
    ]
    config = str(ROOT / "configs/ruff.toml")
    cache = str(SOURCE / "preflight/ruff-cache")
    check = [str(RUFF), "check", "--config", config, "--cache-dir", cache]
    format_argv = [str(RUFF), "format", "--config", config, "--cache-dir", cache]
    if args.write:
        check.append("--fix")
    else:
        format_argv.append("--check")
    first = subprocess.run([*check, *files], cwd=ROOT, check=False)
    second = subprocess.run([*format_argv, *files], cwd=ROOT, check=False)
    sys.exit(1 if first.returncode or second.returncode else 0)


if __name__ == "__main__":
    main()
