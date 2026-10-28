"""Reject altered scientific protocols and unsafe retained-review destinations."""

from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.lra_validation.counting_coverage import run_counting_coverage
from bijux_pollenomics_dev.lra_validation.counting_coverage_verification import (
    verify_counting_coverage,
)


def test_altered_counting_protocol_is_refused_before_simulation(tmp_path: Path) -> None:
    repository = Path(__file__).resolve().parents[4]
    packet = repository / "data/synthetic-validation/finite-count-coverage"
    shutil.copytree(packet, tmp_path / "packet")
    protocol = tmp_path / "packet/protocol.json"
    protocol.write_bytes(protocol.read_bytes() + b" ")
    output = tmp_path / "artifacts/counting"
    with pytest.raises(ValueError, match="frozen scientific contract"):
        run_counting_coverage(
            repository=tmp_path,
            protocol=protocol,
            output=output,
            source_candidate="0" * 40,
            plan_sha256="0" * 64,
        )
    assert not output.exists()


def test_review_output_cannot_overwrite_source(tmp_path: Path) -> None:
    output = tmp_path / "source.json"
    output.write_text("preserved")
    with pytest.raises(ValueError, match="absent artifacts file"):
        verify_counting_coverage(
            repository=tmp_path,
            protocol_path=tmp_path / "protocol.json",
            products=tmp_path / "products",
            output=output,
        )
    assert output.read_text() == "preserved"


def test_review_output_cannot_escape_repository(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="owned by the repository"):
        verify_counting_coverage(
            repository=tmp_path,
            protocol_path=tmp_path / "protocol.json",
            products=tmp_path / "products",
            output=tmp_path.parent / "escaped-review.json",
        )
