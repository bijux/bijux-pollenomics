"""Canonical chronology and source-default admission tests."""

from __future__ import annotations

from copy import deepcopy

import pytest
from bijux_pollenomics.analysis.propagation.source_chronology import (
    SOURCE_NODE_CONFIG_DIGEST,
    SourceNodeContext,
)

from .support import BUILD, SNAPSHOT, derive, source_rows


def test_context_requires_the_governed_derivation_config_identity() -> None:
    assert SOURCE_NODE_CONFIG_DIGEST.startswith("sha256:")
    assert len(SOURCE_NODE_CONFIG_DIGEST) == 71
    assert SOURCE_NODE_CONFIG_DIGEST != BUILD
    with pytest.raises(
        ValueError,
        match="config_digest does not identify source chronology node configuration",
    ):
        SourceNodeContext(
            config_digest=BUILD,
            source_snapshot_id=SNAPSHOT,
            build_id=BUILD,
        )
    with pytest.raises(
        ValueError, match="source_snapshot_id must be a canonical SHA-256 identity"
    ):
        SourceNodeContext(
            config_digest=SOURCE_NODE_CONFIG_DIGEST,
            source_snapshot_id="snapshot",
            build_id=BUILD,
        )


def test_zero_bp_is_preserved_and_null_is_refused() -> None:
    zero = derive(source_rows(younger_bp=0, older_bp=0))
    assert {(node.younger_bp, node.older_bp) for node in zero.nodes} == {(0, 0)}

    missing_rows = source_rows(younger_bp=None, older_bp=None)
    missing = derive(missing_rows)
    assert not missing.nodes
    assert [row.reason_code for row in missing.admission_refusals] == [
        "invalid_source_default_chronology_interval"
    ]


def test_interval_keeps_younger_older_bp_order() -> None:
    result = derive(source_rows(younger_bp=115, older_bp=230))
    assert {(node.younger_bp, node.older_bp) for node in result.nodes} == {(115, 230)}


def test_unique_comparable_nondefault_replaces_an_unusable_source_default() -> None:
    rows = source_rows(
        status="context_only",
        younger_bp=None,
        older_bp=None,
        admission_reason="uncalibrated_radiocarbon",
    )
    alternative = deepcopy(rows["chronologies"][0])
    alternative.update(
        {
            "chronology_claim_id": "calibrated-alternative",
            "is_default_chronology": False,
            "comparability_status": "comparable",
            "younger_bp": 152,
            "older_bp": 253,
            "admission_reason": None,
        }
    )
    rows["chronologies"].append(alternative)

    result = derive(rows)

    assert {node.chronology_claim_id for node in result.nodes} == {
        "calibrated-alternative"
    }
    assert {node.chronology_selection_posture for node in result.nodes} == {
        "selected_unique_nondefault"
    }
    assert all(node.is_default_chronology is False for node in result.nodes)
    assert not result.admission_refusals
    country = result.reconciliation.country_reconciliations[0]
    assert country.usable_canonical_age_claim_count == 1
    assert country.selected_nondefault_chronology_count == 1


def test_usable_source_default_takes_precedence_over_comparable_alternatives() -> None:
    rows = source_rows(chronology_id="default-id", chronology_name="Preferred")
    for suffix, age in (("first", 200), ("second", 300)):
        alternative = deepcopy(rows["chronologies"][0])
        alternative.update(
            {
                "chronology_claim_id": f"alternative-{suffix}",
                "chronology_id": f"alternative-id-{suffix}",
                "chronology_name": f"Alternative {suffix}",
                "is_default_chronology": False,
                "younger_bp": age,
                "older_bp": age + 10,
            }
        )
        rows["chronologies"].append(alternative)

    result = derive(rows)

    assert {node.chronology_claim_id for node in result.nodes} == {
        "claim-SE-observation-1"
    }
    assert {node.chronology_id for node in result.nodes} == {"default-id"}
    assert {node.chronology_name for node in result.nodes} == {"Preferred"}
    assert {node.chronology_selection_posture for node in result.nodes} == {
        "selected_source_default"
    }
    assert result.reconciliation.selected_default_chronology_count == 1


def test_multiple_comparable_nondefault_alternatives_fail_closed() -> None:
    rows = source_rows(
        status="context_only",
        younger_bp=None,
        older_bp=None,
        admission_reason="uncalibrated_radiocarbon",
    )
    for suffix in ("first", "second"):
        alternative = deepcopy(rows["chronologies"][0])
        alternative.update(
            {
                "chronology_claim_id": f"alternative-{suffix}",
                "is_default_chronology": False,
                "comparability_status": "comparable",
                "younger_bp": 100,
                "older_bp": 110,
            }
        )
        rows["chronologies"].append(alternative)

    result = derive(rows)

    assert not result.nodes
    assert result.admission_refusals[0].reason_code == (
        "ambiguous_comparable_alternative_chronology"
    )


def test_zero_comparable_nondefault_alternatives_fail_closed() -> None:
    result = derive(
        source_rows(
            default=False,
            status="context_only",
            younger_bp=None,
            older_bp=None,
            admission_reason="uncalibrated_radiocarbon",
        )
    )

    assert not result.nodes
    assert result.admission_refusals[0].reason_code == (
        "missing_comparable_source_chronology"
    )


def test_nodes_are_published_from_oldest_bp_toward_present() -> None:
    older_rows = source_rows(
        country="SE", younger_bp=450, older_bp=500, observation_id="older"
    )
    newer_rows = source_rows(
        country="NO", younger_bp=75, older_bp=100, observation_id="newer"
    )
    combined = {key: [*older_rows[key], *newer_rows[key]] for key in older_rows}

    result = derive(combined)

    assert [node.older_bp for node in result.nodes] == [500, 500, 500, 100, 100, 100]


def test_ambiguous_source_defaults_fail_closed() -> None:
    rows = source_rows()
    duplicate_default = deepcopy(rows["chronologies"][0])
    duplicate_default["chronology_claim_id"] = "another-default"
    rows["chronologies"].append(duplicate_default)

    result = derive(rows)

    assert not result.nodes
    assert result.admission_refusals[0].reason_code == (
        "ambiguous_source_default_chronology"
    )


def test_conflicting_representations_of_one_claim_fail_closed() -> None:
    rows = source_rows()
    conflicting = deepcopy(rows["chronologies"][0])
    conflicting.update(
        {
            "comparability_status": "context_only",
            "younger_bp": None,
            "older_bp": None,
            "admission_reason": "uncalibrated_radiocarbon",
        }
    )
    rows["chronologies"].append(conflicting)

    result = derive(rows)

    assert not result.nodes
    assert result.admission_refusals[0].reason_code == (
        "conflicting_source_chronology_claim"
    )
