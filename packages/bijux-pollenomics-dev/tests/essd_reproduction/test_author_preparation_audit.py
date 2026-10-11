"""Replay private LandClim author count sources and challenge receipts."""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.essd_reproduction.author_preparation_audit import build

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = (
    REPOSITORY
    / "docs/report/source-relations/landclim/author-preparation-audit/report.json"
)
pytestmark = pytest.mark.skipif(
    os.environ.get("BIJUX_RUN_AUTHOR_PREPARATION_AUDIT") != "1",
    reason="explicit private author source audit opt-in required",
)


def _source_roots() -> tuple[Path, Path]:
    author = os.environ.get("BIJUX_LANDCLIM_AUTHOR_SOURCE_ROOT")
    audit = os.environ.get("BIJUX_LANDCLIM_AUTHOR_AUDIT_ROOT")
    if not author or not audit:
        raise ValueError("Private author source and audit roots are required")
    return Path(author), Path(audit)


def test_private_author_sources_recount_seventeen_sites(tmp_path: Path) -> None:
    author, audit = _source_roots()
    output = tmp_path / "replay"
    report = build(REPOSITORY, author, audit, output)
    assert report["totals"] == {
        "sites": 17,
        "grid_512_sites": 9,
        "grid_562_sites": 8,
        "raw_count": 501713,
        "prepared_count": 299660,
        "raw_minus_prepared": 202053,
    }
    assert report["category_totals"] == {
        "raw": 501713,
        "retained": 299660,
        "excluded_zz": 200247,
        "excluded_not_ppe": 0,
        "unmapped": 418,
        "outside_window": 1388,
    }
    sites = {row["site"]: row for row in report["sites"]}
    assert len(sites) == 17
    assert sites["LOBBSBOG"]["source_categories"]["excluded_zz"] == 6511
    assert sites["LOBBSBOG"]["source_categories"]["retained"] == 21913
    assert sites["WHH05"]["source_categories"] == report["whh05_source_categories"]
    assert [row["count"] for row in sites["NTWITCHEN"]["unmapped_source_labels"]] == [
        7,
        1,
        9,
        127,
    ]
    assert [row["count"] for row in sites["WHH11"]["unmapped_source_labels"]] == [
        20,
        38,
        11,
        205,
    ]
    assert (
        sites["NTWITCHEN"]["unmapped_source_labels"][0]["native_header"]
        == "Euphorbia t. "
    )
    assert (
        sites["WHH11"]["unmapped_source_labels"][-1]["native_header"]
        == "Ranunculus acris-type`"
    )
    assert (output / "report.json").read_bytes() == GOVERNED.read_bytes()


def test_historical_audit_drift_refuses_before_output(tmp_path: Path) -> None:
    author, audit = _source_roots()
    changed = tmp_path / "changed-audit"
    shutil.copytree(audit, changed)
    path = changed / "job006/report.json"
    path.write_bytes(path.read_bytes() + b" ")
    output = tmp_path / "refused"
    with pytest.raises(ValueError, match="audit custody changed"):
        build(REPOSITORY, author, changed, output)
    assert not output.exists()
