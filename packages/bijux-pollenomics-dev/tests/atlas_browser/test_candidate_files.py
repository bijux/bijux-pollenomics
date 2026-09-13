"""Filesystem admission and independent package startup orders."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.candidate_files import regular_bytes
from bijux_pollenomics_dev.ci.atlas_browser.contracts import AtlasBrowserContractError


def test_regular_bytes_preserves_exact_data_and_compatibility_alias(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics_dev.ci import atlas_browser
    from bijux_pollenomics_dev.ci.atlas_browser.artifact_candidate import (
        regular_bytes as compatibility_reader,
    )

    member = tmp_path / "candidate.bin"
    payload = bytes(range(256)) + b"\r\n\x00"
    member.write_bytes(payload)
    assert regular_bytes(member) == payload
    assert compatibility_reader is regular_bytes
    assert atlas_browser.audit_static_atlas is not None


@pytest.mark.parametrize("kind", ["missing", "directory", "leaf_link", "ancestor_link"])
def test_nonregular_and_linked_members_refuse(tmp_path: Path, kind: str) -> None:
    real = tmp_path / "real"
    real.mkdir()
    member = real / "member"
    member.write_bytes(b"retained")
    if kind == "missing":
        selected = tmp_path / "missing"
    elif kind == "directory":
        selected = real
    elif kind == "leaf_link":
        selected = tmp_path / "link"
        selected.symlink_to(member)
    else:
        alias = tmp_path / "alias"
        alias.symlink_to(real, target_is_directory=True)
        selected = alias / "member"
    with pytest.raises(AtlasBrowserContractError):
        regular_bytes(selected)
    assert member.read_bytes() == b"retained"


@pytest.mark.parametrize(
    "first",
    [
        "bijux_pollenomics_dev.ci.lra_reference.certification",
        "bijux_pollenomics_dev.ci.atlas_media",
        "bijux_pollenomics_dev.ci.atlas_browser",
    ],
)
def test_fresh_process_import_order(first: str, tmp_path: Path) -> None:
    script = (
        "import importlib; importlib.import_module(" + repr(first) + ");"
        "from bijux_pollenomics_dev.ci.lra_reference.certification import certify;"
        "from bijux_pollenomics_dev.ci.atlas_media.contracts import AtlasMediaError;"
        "from bijux_pollenomics_dev.ci.atlas_browser import audit_static_atlas;"
        "from bijux_pollenomics_dev.ci.atlas_browser.artifact_candidate import regular_bytes as old;"
        "from bijux_pollenomics_dev.ci.atlas_browser.candidate_files import regular_bytes;"
        "assert old is regular_bytes"
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_fifo_refuses_without_waiting_for_writer(tmp_path: Path) -> None:
    member = tmp_path / "pipe"
    os.mkfifo(member)
    with pytest.raises(AtlasBrowserContractError, match="nonregular"):
        regular_bytes(member)
