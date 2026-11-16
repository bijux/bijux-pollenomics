"""Selected access entrypoints import independently of prior package loading."""

import os
from pathlib import Path
import subprocess
import sys

import pytest

import bijux_pollenomics


@pytest.mark.parametrize(
    "entrypoint", ["selection", "linked_evidence.preflight", "selection.preflight"]
)
def test_selected_access_cold_import(entrypoint: str) -> None:
    """Load each entrypoint in a fresh interpreter using the tested source tree."""
    source_root = Path(bijux_pollenomics.__file__).resolve().parents[1]
    environment = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join([str(source_root), *sys.path]),
    }
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            (
                "from importlib import import_module; from pathlib import Path; "
                "import sys; module = import_module(sys.argv[1]); "
                "assert Path(sys.argv[2]) in Path(module.__file__).resolve().parents"
            ),
            "bijux_pollenomics.collection.sources.neotoma.ancillary_store."
            + entrypoint,
            str(source_root),
        ],
        env=environment,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
