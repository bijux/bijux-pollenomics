"""The Nordic SEAD map input preserves admitted source UUID and join identity."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.sead_public_custody import reconcile

ROOT = Path(__file__).resolve().parents[4]
RAW = ROOT / "data/sead/raw/acquisitions/sead-full-evidence-39bfff6a-ce80714e"


@pytest.fixture(scope="module")
def source_graph() -> tuple[list[dict[str, Any]], ...]:
    sites = json.loads((RAW / "payloads/tbl_sites.json").read_text())["rows"]
    decisions = json.loads((RAW / "country-decisions.json").read_text())["decisions"]
    joins = json.loads((RAW / "reconciliation/joins.json").read_text())["edges"]
    features = json.loads(
        (ROOT / "data/sead/normalized/nordic_environmental_sites.geojson").read_text()
    )["features"]
    traceability = json.loads(
        (ROOT / "docs/report/regions/nordic/nordic_point_traceability.json").read_text()
    )
    records = next(
        layer["records"]
        for layer in traceability["layers"]
        if layer["layer_key"] == "sead-sites"
    )
    return sites, decisions, joins, features, records


def test_current_public_sites_reconcile_from_all_source_uuids(
    source_graph: tuple[list[dict[str, Any]], ...],
) -> None:
    report = reconcile(*source_graph)
    governed = json.loads(
        (
            ROOT / "docs/report/source-relations/sead/public-custody/report.json"
        ).read_text()
    )
    assert all(governed[key] == value for key, value in report.items())
    for path, expected in governed["inputs_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    assert report["raw_and_public_site_count"] == 2069
    assert report["excluded_status_counts"] == {"review": 103, "unassigned": 23}
    assert report["join_edge_count"] == 86
    assert report["join_null_reference_count"] == 37634
    assert all(edge["orphan_child_count"] == 0 for edge in report["join_edges"])


def test_public_uuid_drift_refuses(
    source_graph: tuple[list[dict[str, Any]], ...],
) -> None:
    sites, decisions, joins, features, records = source_graph
    changed = deepcopy(features)
    popup = changed[0]["properties"]["popup_rows"]
    next(row for row in popup if row["label"] == "Site UUID")["value"] = "wrong"
    with pytest.raises(ValueError, match="binding diverges"):
        reconcile(sites, decisions, joins, changed, records)


def test_orphan_source_join_refuses(
    source_graph: tuple[list[dict[str, Any]], ...],
) -> None:
    sites, decisions, joins, features, records = source_graph
    changed = deepcopy(joins)
    changed[0]["orphan_child_ids"].append("unmatched")
    with pytest.raises(ValueError, match="Unreconciled source relation"):
        reconcile(sites, decisions, changed, features, records)


def test_excluded_country_decision_cannot_leak_to_public(
    source_graph: tuple[list[dict[str, Any]], ...],
) -> None:
    sites, decisions, joins, features, records = source_graph
    changed = deepcopy(features)
    excluded = next(
        row for row in decisions if row["decision"]["decision_status"] != "assigned"
    )
    changed[0]["properties"]["record_id"] = str(excluded["site_id"])
    with pytest.raises(ValueError, match="site sets diverge"):
        reconcile(sites, decisions, joins, changed, records)
