"""Authenticate the admitted native packet in place and inject bounded read failures."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.lra_validation.native_reference import (
    finite_covariance_capture as capture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import _file


@pytest.fixture
def repository() -> Path:
    """Use the complete normal clone; neither packet nor package source is copied."""
    return Path(__file__).resolve().parents[5]


def test_admitted_native_source_population(repository: Path) -> None:
    result = capture.validated_finite_covariance_capture(repository)
    assert len(result.raw_sha256) == 138
    assert len(result.report_source_members) == 129
    assert len(result.input_sha256) == 153
    assert len(result.source_context["protected_science_sha256"]) == 68
    driver = capture.CAPTURE_ROOT + "/capture/oracle/oracle.R"
    assert not (repository / driver).exists()
    assert (
        hashlib.sha256(result.read_input(driver)).hexdigest()
        == result.raw_sha256["oracle/oracle.R"]
    )
    with pytest.raises(ValueError, match="Unlisted"):
        result.read_input("unlisted.csv")


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
def test_modified_admitted_member_refuses(
    repository: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original_file = _file
    original_resolver = validated_descriptor
    full = capture.CAPTURE_ROOT + "/" + name

    def changed_file(root: Path, relative: str) -> bytes:
        body = original_file(root, relative)
        return body + b" " if relative == full else body

    class ChangedReader:
        def __init__(self, reader: Any) -> None:
            self.reader = reader

        def read_source(self, relative: str) -> bytes:
            body: bytes = self.reader.read_source(relative)
            return body + b" " if relative == name else body

        def fresh(self) -> None:
            self.reader.fresh()

    def changed_reader(*args: Any, **kwargs: Any) -> ChangedReader:
        return ChangedReader(original_resolver(*args, **kwargs))

    monkeypatch.setattr(capture, "_file", changed_file)
    monkeypatch.setattr(capture, "validated_descriptor", changed_reader)
    with pytest.raises(ValueError):
        capture.validated_finite_covariance_capture(repository)


@pytest.mark.parametrize(
    "name", ["fixed_site_covariance.py", "joint_fixed_site_covariance.py"]
)
def test_changed_covariance_source_refuses(
    repository: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original: Callable[[Path, str], bytes] = _file
    full = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/"
        + name
    )

    def changed(root: Path, relative: str) -> bytes:
        body = original(root, relative)
        return body + b"\n" if relative == full else body

    monkeypatch.setattr(capture, "_file", changed)
    with pytest.raises(ValueError, match="protected source"):
        capture.validated_finite_covariance_capture(repository)
