"""Refuse changed scientific inputs, physical aliases and incomplete native custody."""

from pathlib import Path
import json
import os
import shutil

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.finite_covariance_capture import (
    CAPTURE_ROOT,
    validated_finite_covariance_capture,
)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy the admitted finite packet and scientific inputs into independently owned files."""
    maintained = Path(__file__).resolve().parents[5]
    root = tmp_path / "repository"
    shutil.copytree(maintained / CAPTURE_ROOT, root / CAPTURE_ROOT)
    record = json.loads((root / CAPTURE_ROOT / "capture/capture.json").read_text())
    names = [
        *record["source_context"]["protected_science_sha256"],
        "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json",
    ]
    for name in names:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(maintained / name, target)
    return root


def test_admitted_native_source_population(repository: Path) -> None:
    capture = validated_finite_covariance_capture(repository)
    assert len(capture.raw_sha256) == 138
    assert len(capture.report_source_members) == 129
    assert len(capture.input_sha256) == 153
    assert len(capture.source_context["protected_science_sha256"]) == 68


@pytest.mark.parametrize(
    "name",
    [
        "capture/oracle/C0000.csv",
        "capture/receipt.json",
        "capture/capture.json",
        "execution-evidence/plan.json",
        "execution-evidence/terminal.json",
        "execution-evidence/independent-terminal-review.json",
        "source-archives/GenSA_1.1.15.tar.gz",
    ],
)
def test_modified_admitted_member_refuses(repository: Path, name: str) -> None:
    target = repository / CAPTURE_ROOT / name
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError):
        validated_finite_covariance_capture(repository)


@pytest.mark.parametrize(
    "name", ["fixed_site_covariance.py", "joint_fixed_site_covariance.py"]
)
def test_changed_covariance_source_refuses(repository: Path, name: str) -> None:
    target = (
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction"
        / name
    )
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="protected source"):
        validated_finite_covariance_capture(repository)


def test_undeclared_physical_member_refuses(repository: Path) -> None:
    (repository / CAPTURE_ROOT / "capture/undeclared.csv").write_text("0,0\n")
    with pytest.raises(ValueError, match="extra/missing"):
        validated_finite_covariance_capture(repository)


@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_member_file_alias_refuses(repository: Path, alias: str) -> None:
    target = repository / CAPTURE_ROOT / "capture/oracle/C0000.csv"
    backing = repository / "backing.csv"
    target.rename(backing)
    if alias == "symlink":
        target.symlink_to(backing)
    else:
        os.link(backing, target)
    with pytest.raises(ValueError):
        validated_finite_covariance_capture(repository)
