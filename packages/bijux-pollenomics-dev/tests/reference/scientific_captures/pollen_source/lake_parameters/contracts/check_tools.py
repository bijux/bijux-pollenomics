"""Check lakeparameter replay source with the admitted cached formatter."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
import subprocess

SOURCE = Path(__file__).absolute().parent
ROOT = SOURCE.parents[2]
RUFF = Path(
    "/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff"
)
FILES = sorted(
    (
        p
        for p in SOURCE.glob("*.py")
        if p.name not in {"runtime_contracts.py", "common_runner.py"}
    ),
    key=str,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--format", action="store_true")
    args = parser.parse_args()
    cache = SOURCE / "preflight/ruff-cache"
    config = ROOT / "configs/ruff.toml"
    stages = []
    for action in (
        (("check", "--fix"), ("format",))
        if args.format
        else (("check",), ("format", "--check"))
    ):
        argv = [
            str(RUFF),
            *action,
            "--config",
            str(config),
            "--cache-dir",
            str(cache),
            *map(str, FILES),
        ]
        result = subprocess.run(argv, capture_output=True, text=True)
        print(result.stdout + result.stderr)
        stages.append(
            {
                "argv": argv,
                "actual_exit": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        )
        if result.returncode:
            raise SystemExit(result.returncode)
    sources = sorted(SOURCE.glob("*.py"), key=str)
    for path in sources:
        ast.parse(path.read_bytes())
    target = (
        SOURCE
        / "preflight"
        / ("formatted-tools.json" if args.format else "configured-tools.json")
    )
    target.write_text(
        json.dumps(
            {
                "actual_exit": 0,
                "stages": stages,
                "configured_files": len(FILES),
                "AST_files": len(sources),
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
