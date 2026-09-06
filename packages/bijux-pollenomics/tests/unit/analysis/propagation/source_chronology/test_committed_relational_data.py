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
    observations = _surface(manifest, "observations")
    result = derive_neotoma_source_chronology_nodes(
        observations=observations,
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
        "SE": (162_683, 125_271, 102_317, 5_626, 0, 22_911),
        "DK": (9_247, 7_930, 3_407, 91, 152, 13_410),
        "NO": (143_065, 91_858, 81_569, 3_692, 0, 20_995),
        "FI": (46_241, 34_001, 28_610, 1_891, 0, 13_135),
    }
    assert {
        country: (
            row.selected_sample_count,
            len(
                {node.site_id for node in result.nodes if node.country_code == country}
            ),
        )
        for country, row in countries.items()
    } == {
        "SE": (4_704, 75),
        "DK": (91, 1),
        "NO": (3_396, 51),
        "FI": (1_797, 28),
    }
    assert result.reconciliation.selected_sample_count == 9_988
    assert result.reconciliation.eligible_observation_count == 215_903
    assert len({node.site_id for node in result.nodes}) == 155
    assert {
        country: dict(row.node_counts_by_level) for country, row in countries.items()
    } == {
        "SE": {
            "source_ecological_code": 11_818,
            "source_sample_presence": 4_704,
            "source_taxon": 102_182,
        },
        "DK": {
            "source_ecological_code": 271,
            "source_sample_presence": 91,
            "source_taxon": 3_407,
        },
        "NO": {
            "source_ecological_code": 8_779,
            "source_sample_presence": 3_396,
            "source_taxon": 81_552,
        },
        "FI": {
            "source_ecological_code": 4_297,
            "source_sample_presence": 1_797,
            "source_taxon": 28_610,
        },
    }
    assert {
        country: (
            row.selected_default_chronology_count,
            row.selected_nondefault_chronology_count,
            row.selected_named_chronology_count,
            dict(row.chronology_selection_posture_counts),
        )
        for country, row in countries.items()
    } == {
        "SE": (
            2_476,
            2_228,
            4_704,
            {"selected_source_default": 2_476, "selected_unique_nondefault": 2_228},
        ),
        "DK": (0, 91, 91, {"selected_unique_nondefault": 91}),
        "NO": (
            966,
            2_430,
            3_396,
            {"selected_source_default": 966, "selected_unique_nondefault": 2_430},
        ),
        "FI": (
            127,
            1_670,
            1_797,
            {"selected_source_default": 127, "selected_unique_nondefault": 1_670},
        ),
    }
    observation_by_id = {str(row["observation_id"]): row for row in observations}
    merged_no_taxa = [
        node
        for node in result.nodes
        if node.country_code == "NO"
        and node.node_level == "source_taxon"
        and len(node.observation_ids) > 1
    ]
    assert len(merged_no_taxa) == 17
    assert sum(len(node.observation_ids) - 1 for node in merged_no_taxa) == 17
    assert {
        (node.source_taxon_id, node.source_reported_name, node.source_variable_ids)
        for node in merged_no_taxa
    } == {(27884, "cf. Larix", ("neotoma:variable:27884",))}
    assert all(node.source_ecological_group is None for node in merged_no_taxa)
    assert all(
        {
            observation_by_id[observation_id]["source_ecological_group"]
            for observation_id in node.observation_ids
        }
        == {"TRSH", "UNID"}
        for node in merged_no_taxa
    )
    codes = Counter(
        node.source_ecological_group
        for node in result.nodes
        if node.node_level == "source_ecological_code"
    )
    assert {code: codes[code] for code in ("TRSH", "UPHE", "AQVP")} == {
        "TRSH": 9_978,
        "UPHE": 9_928,
        "AQVP": 4_991,
    }
    code_observation_denominators: Counter[str | None] = Counter()
    for node in result.nodes:
        if node.node_level == "source_ecological_code":
            code_observation_denominators[node.source_ecological_group] += len(
                node.observation_ids
            )
    assert {
        code: code_observation_denominators[code] for code in ("TRSH", "UPHE", "AQVP")
    } == {
        "TRSH": 114_225,
        "UPHE": 91_739,
        "AQVP": 9_666,
    }
    assert result.reconciliation.propagation_eligible_event_count == 0
    assert all(node.propagation_eligible is False for node in result.nodes)
    assert dict(result.reconciliation.refusal_reason_counts) == {
        "ambiguous_comparable_alternative_chronology": 9_865,
        "missing_comparable_source_chronology": 18_174,
        "non_comparable_source_default_chronology": 15_118,
        "non_pollen_observation": 102_176,
        "ungoverned_country": 9_700,
    }
