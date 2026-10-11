"""Local source lifecycle contracts preserve admission and review boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.landclim.review import (
    render_landclim_spatiotemporal_review_markdown,
)
from bijux_pollenomics.collection.sources.sead.acquisition.governed import (
    validate_governed_sead_admission,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.service import (
    _REQUIRED_ACQUISITION_TABLES,
    build_sead_site_rows_from_acquisition_tables,
)
from bijux_pollenomics.collection.sources.sead.collection import (
    validate_governed_sead_admission as collection_admission,
)
from tests.support.repository import REPOSITORY_ROOT


def test_sead_linked_site_rows_require_exact_admitted_table_set() -> None:
    rows: dict[str, list[dict[str, object]]] = {
        name: [] for name in _REQUIRED_ACQUISITION_TABLES
    }
    sites, summary = build_sead_site_rows_from_acquisition_tables(rows)
    assert sites == []
    assert summary["site_row_count"] == 0
    missing: dict[str, list[dict[str, object]]] = {
        name: [] for name in rows if name != "tbl_sites"
    }
    extra: dict[str, list[dict[str, object]]] = rows | {"unadmitted_table": []}
    for invalid in (missing, extra):
        with pytest.raises(ValueError, match="exact table set"):
            build_sead_site_rows_from_acquisition_tables(invalid)


def test_collection_admission_refers_to_governed_validator() -> None:
    assert collection_admission is validate_governed_sead_admission


def test_landclim_retained_review_markdown_and_caveat_refusal() -> None:
    report_root = Path(REPOSITORY_ROOT) / "data" / "landclim" / "review"
    payload = json.loads(
        (report_root / "spatiotemporal_review.json").read_text(encoding="utf-8")
    )
    assert render_landclim_spatiotemporal_review_markdown(payload) == (
        report_root / "spatiotemporal_review.md"
    ).read_text(encoding="utf-8")
    with pytest.raises(TypeError):
        render_landclim_spatiotemporal_review_markdown(
            dict(payload, interpretation_caveats=None)
        )
