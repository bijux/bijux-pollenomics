"""Replay the exact private Amsoldingersee source capture when available."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.source_completion.landclim_amsoldingersee_recovery import (
    build,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = (
    REPOSITORY
    / "docs/report/publication-replay/landclim-amsoldingersee-source-review/report.json"
)
pytestmark = pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_AMSOLDINGERSEE_REAL_INTEGRATION") != "1",
    reason="explicit private Amsoldingersee source replay opt-in required",
)


def _source_root() -> Path:
    value = os.environ.get("BIJUX_AMSOLDINGERSEE_SOURCE_ROOT")
    if not value:
        raise ValueError("BIJUX_AMSOLDINGERSEE_SOURCE_ROOT is required")
    return Path(value)


def test_private_capture_replays_governed_refusal(tmp_path: Path) -> None:
    output = tmp_path / "replay"
    report = build(REPOSITORY, _source_root(), output)
    assert report["denominators"] == {
        "selected_publication_rows": 1,
        "candidate_core_count": 3,
        "candidate_with_23_current_sample_ids": 1,
        "candidate_with_exact_e69_bridge": 0,
        "candidate_with_authenticated_author_chronology": 0,
        "reproduction_ready": 0,
    }
    assert (output / "report.json").read_bytes() == GOVERNED.read_bytes()


def test_capture_drift_refuses_before_output(tmp_path: Path) -> None:
    source = tmp_path / "source"
    shutil.copytree(_source_root(), source)
    path = source / "capture/sites.raw"
    path.write_bytes(path.read_bytes() + b" ")
    output = tmp_path / "refused"
    with pytest.raises(ValueError, match="source custody changed"):
        build(REPOSITORY, source, output)
    assert not output.exists()
