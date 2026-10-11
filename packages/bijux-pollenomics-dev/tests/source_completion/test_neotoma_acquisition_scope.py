"""Retained Neotoma inventory scope is distinct from original HTTP custody."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.neotoma_acquisition_scope import (
    build,
    reconcile,
)

REPOSITORY = Path(__file__).resolve().parents[4]
GOVERNED = (
    REPOSITORY / "docs/report/source-relations/neotoma/acquisition-scope/report.json"
)


def test_retained_inventory_scope_replays_governed_receipt() -> None:
    report = build(REPOSITORY)
    assert report == json.loads(GOVERNED.read_bytes())
    scope = report["retained_json_reconciliation"]
    assert scope["queried_row_count"] == 387
    assert scope["retained_row_count"] == 206
    assert scope["requested_dataset_count"] == 209
    assert scope["current_selector_row_count"] == 200
    assert [row["dataset_ids"] for row in scope["retained_only_rows"]] == [
        [720],
        [3941],
        [4082],
        [4181],
        [4298],
        [20058],
    ]
    assert scope["current_only_rows"] == []
    assert report["original_http_receipt_status"] == "unavailable"


def test_retained_inventory_cannot_gain_an_unqueried_object() -> None:
    inventory = {
        "endpoint": "https://api.neotomadb.org/v2.0/data/datasets",
        "datasettype": "pollen",
        "loc": '{"type":"Polygon","coordinates":[[[4.0,54.0],[35.0,54.0],[35.0,72.0],[4.0,72.0],[4.0,54.0]]]}',
        "queried_row_count": 1,
        "retained_row_count": 1,
        "retained_dataset_count": 1,
        "rows": [{"site": {"siteid": 1, "datasets": [{"datasetid": 1}]}}],
        "retained_rows": [{"site": {"siteid": 1, "datasets": [{"datasetid": 1}]}}],
    }
    manifest = {
        "endpoint_template": "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}",
        "requested_dataset_count": 1,
        "downloaded_dataset_count": 1,
        "requested_dataset_ids": [1],
        "downloaded_dataset_ids": [1],
    }
    changed = copy.deepcopy(inventory)
    retained_rows = changed["retained_rows"]
    assert isinstance(retained_rows, list)
    retained_site = retained_rows[0]["site"]
    assert isinstance(retained_site, dict)
    retained_site["sitename"] = "unqueried object"
    with pytest.raises(ValueError, match="ordered lossless subset"):
        reconcile(changed, manifest, [])
