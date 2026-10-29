"""Install only hash-bound offline transport wheels into the new owned environment."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import confined_output, digest, json_value, require, write_json


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json_value(args.plan)
    output = confined_output(Path(plan["output"]))
    environment = confined_output(output / "environment")
    require(
        environment.is_dir() and (environment / "pyvenv.cfg").is_file(),
        "Owned venv was not created by the preceding stage",
    )
    wheels = output / "wheels"
    manifest = json_value(wheels / "transport-manifest.json")
    requirements = wheels / "requirements.txt"
    require(
        digest(requirements) == manifest["requirements_sha256"],
        "Offline requirements changed",
    )
    require(
        len(manifest["distributions"]) == 147, "Offline installed membership differs"
    )
    for row in manifest["distributions"]:
        path = Path(row["path"])
        require(
            path.parent == wheels
            and path.is_file()
            and not path.is_symlink()
            and digest(path) == row["sha256"]
            and path.stat().st_size == row["bytes"],
            "Offline wheel authority differs",
        )
    argv = [
        str(environment / "bin/python"),
        "-I",
        "-B",
        str(Path(__file__).resolve().parent / "pip_entry.py"),
        "--plan",
        str(args.plan),
    ]
    env = dict(os.environ)
    for key in list(env):
        if key.startswith(("PIP_", "PYTHON")) or key in {
            "VIRTUAL_ENV",
            "UV_CACHE_DIR",
            "UV_PROJECT_ENVIRONMENT",
        }:
            env.pop(key, None)
    env.update(plan["environment"])
    env["PIP_CONFIG_FILE"] = os.devnull
    write_json(
        output / "offline-install-command.json",
        {
            "argv": argv,
            "network_permitted": False,
            "source_build_fallback_permitted": False,
            "isolated_new_environment": str(environment),
        },
    )
    result = subprocess.run(argv, cwd=output, env=env, check=False)
    write_json(
        output / "offline-install-result.json",
        {
            "argv": argv,
            "actual_exit": result.returncode,
            "new_environment": str(environment),
            "scope": "Offline source-check dependencies only; no first-party editable metadata or installed API admission.",
        },
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
