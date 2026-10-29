"""Run repository formatter and lint settings on authored controller sources."""

from pathlib import Path
import subprocess
import sys

SOURCE = Path(__file__).absolute().parent
ROOT = SOURCE.parents[2]
RUFF = (
    "/Users/bijan/.cache/uv/archive-v0/2XF0xMG3jR4vPhZZ/ruff-0.15.8.data/scripts/ruff"
)
files = [str(path) for path in sorted(SOURCE.glob("*.py"))]
common = [
    "--config",
    str(ROOT / "configs/ruff.toml"),
    "--cache-dir",
    str(SOURCE / "preflight/ruff-cache"),
]
action = sys.argv[1]
if action == "format":
    argv = [RUFF, "format", *common, *files]
elif action == "lint-fix":
    argv = [RUFF, "check", "--fix", *common, *files]
elif action == "format-check":
    argv = [RUFF, "format", "--check", *common, *files]
elif action == "lint":
    argv = [RUFF, "check", *common, *files]
else:
    raise ValueError("Unknown authored source check")
raise SystemExit(subprocess.run(argv, cwd=ROOT, check=False).returncode)
