"""Canonical gate environments cannot fall back to another editable source tree."""

from __future__ import annotations

import json
from pathlib import Path
import shlex
import subprocess
import sys

import pytest

from bijux_pollenomics.provenance.gates import build_product_gate_specification
from tests.support.repository import REPOSITORY_ROOT


@pytest.mark.parametrize("gate", ["science", "data", "map", "provenance", "doc-counts"])
def test_gate_imports_all_distributions_from_same_owned_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, gate: str
) -> None:
    from bijux_pollenomics.provenance.gates import specification

    monkeypatch.setattr(specification, "_head_revision", lambda _root: "a" * 40)
    names = {
        "bijux_pollenomics": "bijux-pollenomics",
        "bijux_pollenomics_dev": "bijux-pollenomics-dev",
        "bijux_pollenomics_lra": "bijux-pollenomics-lra",
        "pollenomics": "pollenomics",
    }
    spec = build_product_gate_specification(REPOSITORY_ROOT, gate)
    environment = dict(spec.environment)
    script = (
        "import importlib.util,json; "
        f"names={list(names)!r}; "
        "print(json.dumps({name:importlib.util.find_spec(name).origin for name in names}))"
    )
    observed = json.loads(
        subprocess.check_output(
            [sys.executable, "-B", "-c", script],
            cwd=tmp_path,
            env=environment,
            text=True,
        )
    )
    assert observed == {
        module: str(
            REPOSITORY_ROOT / "packages" / package / "src" / module / "__init__.py"
        )
        for module, package in names.items()
    }


def test_make_materializer_uses_complete_owned_source_and_admitted_python(
    tmp_path: Path,
) -> None:
    output = subprocess.check_output(
        [
            "make",
            "--no-print-directory",
            "-n",
            "-o",
            "root-check-env",
            "-f",
            "makes/pollenomics-verification.mk",
            "materialize-scientific-evidence",
            f"ROOT_CHECK_VENV={REPOSITORY_ROOT}/artifacts/root/check-venv",
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
    )
    commands = output.replace("\\\n", " ").splitlines()
    words = shlex.split(
        next(line for line in commands if "ci.scientific_evidence" in line)
    )
    executable = str(REPOSITORY_ROOT / "artifacts/root/check-venv/bin/python")
    index = words.index(executable)
    environment = dict(
        build_product_gate_specification(REPOSITORY_ROOT, "science").environment
    )
    declared = dict(word.split("=", 1) for word in words[:index])
    assert declared["PYTHONPATH"] == environment["PYTHONPATH"]
    assert declared["TMPDIR"] == str(
        REPOSITORY_ROOT
        / "artifacts/release-verification/gates/temporary/scientific-evidence/tmp"
    )
    assert declared["PYTHONDONTWRITEBYTECODE"] == "1"
    assert words[index:] == [
        executable,
        "-m",
        "bijux_pollenomics_dev.ci.scientific_evidence",
        "--repository-root",
        str(REPOSITORY_ROOT),
    ]
    environment.update(declared)
    observed = json.loads(
        subprocess.check_output(
            [
                sys.executable,
                "-B",
                "-c",
                "import importlib.util,json;print(json.dumps({n:importlib.util.find_spec(n).origin for n in ('bijux_pollenomics','bijux_pollenomics_dev','bijux_pollenomics_lra','pollenomics')}))",
            ],
            cwd=tmp_path,
            env=environment,
            text=True,
        )
    )
    assert all(
        Path(value).is_relative_to(REPOSITORY_ROOT / "packages")
        for value in observed.values()
    )
