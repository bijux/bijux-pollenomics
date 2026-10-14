"""Run synthetic replay inputs with genuine repository-owned Python origins."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Any, cast


def generate_fixture_candidate(
    repository: Path, destination: Path, module: str
) -> dict[str, Any]:
    """Keep synthetic data separate while exercising the unmodified origin guard."""
    assert module in {"source_detail_candidate", "nordic_source_candidate"}
    original = next(
        parent
        for parent in Path(__file__).resolve().parents
        if (parent / "packages/bijux-pollenomics-dev/pyproject.toml").is_file()
    )
    roots = []
    for package in (
        "bijux-pollenomics-dev",
        "bijux-pollenomics",
        "bijux-pollenomics-lra",
        "pollenomics",
    ):
        source = original / "packages" / package / "src"
        target = repository / "packages" / package / "src"
        shutil.copytree(
            source,
            target,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"),
        )
        roots.append(target)
    environment = dict(
        os.environ,
        PYTHONPATH=os.pathsep.join(map(str, roots)),
        PYTHONDONTWRITEBYTECODE="1",
    )
    environment.pop("PYTHONHOME", None)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "bijux_pollenomics_dev.ci.atlas_browser." + module,
            "--repository",
            str(repository),
            "--destination",
            str(destination),
        ],
        cwd=repository,
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    receipt = cast(
        dict[str, Any], json.loads((destination / "generation.json").read_bytes())
    )
    inputs = cast(dict[str, str], receipt["inputs_sha256"])
    assert {
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/"
        + name
        for name in (module + ".py", "source_custody.py")
    } <= inputs.keys()
    for relative, expected in inputs.items():
        assert (
            hashlib.sha256((repository / relative).read_bytes()).hexdigest() == expected
        )
    return receipt
