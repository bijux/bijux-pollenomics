"""Exact chronology-node denominators for the committed Neotoma snapshot."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
from typing import Any

from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
    derive_neotoma_source_chronology_nodes,
)

ROOT = Path(__file__).resolve().parents[7]
RELATIONAL = ROOT / "data/neotoma/relational"


def _surface(manifest: dict[str, Any], name: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for part in manifest["surfaces"][name]["parts"]:
        payload = json.loads((RELATIONAL / part["path"]).read_text(encoding="utf-8"))
        rows.extend(payload["rows"])
    return rows


def test_committed_snapshot_reconciles_country_nodes_and_refusals() -> None:
    manifest = json.loads((RELATIONAL / "manifest.json").read_text(encoding="utf-8"))
    result = derive_neotoma_source_chronology_nodes(
        observations=_surface(manifest, "observations"),
        samples=_surface(manifest, "samples"),
        sites=_surface(manifest, "sites"),
        variables=_surface(manifest, "variables"),
        chronologies=_surface(manifest, "age_claims"),
        context=SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id=manifest["source_snapshot_id"],
            build_id=manifest["build_id"],
        ),
    )
    countries = {
        row.country_code: row for row in result.reconciliation.country_reconciliations
    }

    assert {
        country: (
            row.input_observation_count,
            row.pollen_observation_count,
            row.eligible_observation_count,
            row.usable_canonical_age_claim_count,
            row.canonical_coverage_younger_bp,
            row.canonical_coverage_older_bp,
        )
        for country, row in countries.items()
    } == {
        "SE": (162_683, 125_271, 49_416, 5_626, 0, 22_911),
        "DK": (9_247, 7_930, 0, 91, 152, 13_410),
        "NO": (143_065, 91_858, 23_447, 3_692, 0, 20_995),
        "FI": (46_241, 34_001, 1_735, 1_891, 0, 13_135),
    }
    assert {
        country: dict(row.node_counts_by_level) for country, row in countries.items()
    } == {
        "SE": {
            "source_ecological_code": 6_164,
            "source_sample_presence": 2_476,
            "source_taxon": 49_415,
        },
        "DK": {},
        "NO": {
            "source_ecological_code": 2_307,
            "source_sample_presence": 966,
            "source_taxon": 23_447,
        },
        "FI": {
            "source_ecological_code": 307,
            "source_sample_presence": 127,
            "source_taxon": 1_735,
        },
    }
    assert {
        country: row.source_taxon_identity_enrichment_count
        for country, row in countries.items()
    } == {"SE": 0, "DK": 0, "NO": 17, "FI": 0}
    assert result.reconciliation.source_taxon_identity_enrichment_count == 17
    codes = Counter(
        node.source_ecological_group
        for node in result.nodes
        if node.node_level == "source_ecological_code"
    )
    assert {code: codes[code] for code in ("TRSH", "UPHE", "AQVP")} == {
        "TRSH": 3_559,
        "UPHE": 3_511,
        "AQVP": 1_467,
    }
    assert result.reconciliation.propagation_eligible_event_count == 0
    assert all(node.propagation_eligible is False for node in result.nodes)
