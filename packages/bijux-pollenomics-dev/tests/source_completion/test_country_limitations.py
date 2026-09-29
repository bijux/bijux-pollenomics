"""Generated limitations keep the three country claims and their nulls distinct."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.country_limitations import render, run

ROOT = Path(__file__).resolve().parents[4]
PUBLIC = ROOT / "docs/public/pollenomics-data/sources/country-source-limitations.md"


def _inputs() -> tuple[dict[str, object], dict[str, object], dict[str, str]]:
    paths = (
        "data/source_family_evidence_stage_matrix.json",
        "data/country_dimension_coverage.json",
    )
    payloads = [(ROOT / path).read_bytes() for path in paths]
    stage, coverage = (json.loads(payload) for payload in payloads)
    identity = {
        path: hashlib.sha256(payload).hexdigest()
        for path, payload in zip(paths, payloads, strict=True)
    }
    return stage, coverage, identity


def test_public_document_matches_current_source_ledgers() -> None:
    stage, coverage, identity = _inputs()
    text = render(stage, coverage, identity)
    assert text == PUBLIC.read_text()
    assert text.count("| Sweden |") == 11
    assert text.count("| Denmark |") == 11
    assert text.count("| Norway |") == 11
    assert text.count("| Finland |") == 11
    assert "SEAD | Sweden | `zero_observations`; received records 0; sites 0" in text
    assert "HYDE | Sweden | `blocked`; count unresolved" in text


def test_changed_resolution_refuses_public_claim() -> None:
    stage, coverage, identity = _inputs()
    changed = deepcopy(coverage)
    cells = changed["cells"]
    assert isinstance(cells, list)
    assert isinstance(cells[0], dict)
    cells[0]["resolution"] = "site"
    with pytest.raises(ValueError, match="resolution changed"):
        render(stage, changed, identity)


def test_producer_refuses_non_artifact_destination() -> None:
    stage, coverage, identity = _inputs()
    rendered = render(stage, coverage, identity)
    assert rendered.startswith("---\ntitle: Nordic Source and Country Limitations")
    with pytest.raises(ValueError, match="Absent repository artifact"):
        run(ROOT, ROOT / "docs/public/pollenomics-data/sources/invalid-output")
