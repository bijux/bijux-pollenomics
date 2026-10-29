"""Run the exact cached pip module inside a fresh pip-free owned environment."""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import runpy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    confined_output,
    digest,
    json_value,
    normalize,
    require,
    validate_payload,
    write_json,
)


def pip_arguments(environment: Path, requirements: Path) -> list[str]:
    return [
        "pip",
        "--isolated",
        "install",
        "--no-index",
        "--no-deps",
        "--ignore-installed",
        "--require-hashes",
        "--no-cache-dir",
        "--no-compile",
        "--disable-pip-version-check",
        "--no-input",
        "--prefix",
        str(environment),
        "--requirement",
        str(requirements),
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = json_value(args.plan)
    output = confined_output(Path(plan["output"]))
    environment = output / "environment"
    require(
        Path(sys.prefix) == environment
        and Path(sys.executable) == environment / "bin/python",
        "Cached pip must execute inside the fresh owned venv",
    )
    rows = [r for r in plan["selected_payloads"] if normalize(r["name"]) == "pip"]
    require(
        len(rows) == 1 and rows[0]["version"] == "26.2",
        "Exact cached pip authority differs",
    )
    source = rows[0]
    require(validate_payload(source) == source, "Bootstrap pip cache payload changed")
    manifest = json_value(output / "wheels/transport-manifest.json")
    requirements = output / "wheels/requirements.txt"
    require(
        digest(requirements) == manifest["requirements_sha256"],
        "Hash-bound wheel requirements changed",
    )
    for record in manifest["distributions"]:
        path = Path(record["path"])
        require(
            path.parent == output / "wheels"
            and path.is_file()
            and not path.is_symlink()
            and digest(path) == record["sha256"],
            "Generated transport wheel changed",
        )
    sys.path.insert(0, source["archive"])
    pip = importlib.import_module("pip")
    origin = pip.__file__
    require(isinstance(origin, str), "Cached pip has no physical source origin")
    assert isinstance(origin, str)
    require(
        Path(origin).resolve().is_relative_to(Path(source["archive"]))
        and pip.__version__ == "26.2",
        "Pip resolved to an unselected package",
    )
    argv = pip_arguments(environment, requirements)
    os.environ["PIP_CONFIG_FILE"] = os.devnull
    write_json(
        output / "offline-pip-module.json",
        {
            "argv": argv,
            "origin": str(pip.__file__),
            "cached_METADATA_sha256": source["metadata_sha256"],
            "cached_WHEEL_sha256": source["wheel_sha256"],
            "bootstrap_environment_prefix": sys.prefix,
            "stdlib_seed_distributions_used": False,
            "network_permitted": False,
        },
    )
    sys.argv = argv
    runpy.run_module("pip", run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
