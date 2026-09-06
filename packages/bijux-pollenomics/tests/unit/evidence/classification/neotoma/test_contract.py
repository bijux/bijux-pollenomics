"""Scientific accounting, refusal, and deterministic-output contracts."""

from __future__ import annotations

import hashlib
import json
from typing import Any, cast

import pytest
from bijux_pollenomics.evidence.classification.neotoma import (
    build_neotoma_classification_accounting,
)

from .support import representative_snapshot


def test_accounting_preserves_source_taxonomy_and_separate_mapping_dimensions() -> None:
    payload = build_neotoma_classification_accounting(representative_snapshot())
    concepts = cast(list[dict[str, Any]], payload["concepts"])
    by_name = {row["source_reported_name"]: row for row in concepts}

    cereal = by_name["Poaceae (Cerealia-type) undiff."]
    assert cereal["source_taxon_id"] == 1947
    assert cereal["source_taxon_group"] == "Vascular plants"
    assert cereal["source_label_qualifier_markers"] == [
        "type",
        "undifferentiated",
    ]
    assert cereal["mapping_status"] == "unmapped"
    assert cereal["accepted_taxon_concept_id"] is None
    assert cereal["accepted_taxon_name"] is None
    assert cereal["primary_group_id"] is None
    assert cereal["primary_subgroup_id"] is None
    assert cereal["role_ids"] == []
    assert cereal["cross_unit_aggregation_allowed"] is False

    laboratory = by_name["Pollen concentration"]
    administrative = by_name["Recorded value"]
    assert laboratory["mapping_status"] == "not_applicable"
    assert administrative["mapping_status"] == "not_applicable"
    assert administrative["source_element_type"] is None
    assert all(row["release_eligible"] is False for row in concepts)


def test_accounting_reconciles_denominators_and_orders_every_partition() -> None:
    payload = build_neotoma_classification_accounting(representative_snapshot())
    reconciliation = cast(dict[str, int], payload["reconciliation"])
    memberships = cast(list[dict[str, object]], payload["observation_memberships"])
    partitions = cast(dict[str, list[dict[str, object]]], payload["partitions"])
    review = cast(dict[str, object], payload["review"])

    assert reconciliation == {
        "input_observation_row_count": 4,
        "unique_observation_count": 3,
        "duplicate_observation_row_count": 1,
        "observation_membership_count": 3,
        "concept_count": 3,
        "concept_observation_count_sum": 3,
        "mapping_status_concept_count_sum": 3,
        "mapping_status_observation_count_sum": 3,
        "accepted_concept_count": 0,
        "release_eligible_concept_count": 0,
        "integrity_blocker_count": 3,
    }
    assert [row["observation_id"] for row in memberships] == [
        "obs:1",
        "obs:2",
        "obs:3",
    ]
    assert [row["value"] for row in partitions["mapping_status"]] == [
        "accepted",
        "accepted_qualified",
        "unmapped",
        "contested",
        "not_applicable",
        "refused",
    ]
    assert [row["country_code"] for row in partitions["source_country"]] == [
        "SE",
        "DK",
        "NO",
        "FI",
        "UNASSIGNED",
    ]
    blockers = cast(list[dict[str, object]], review["country_release_blockers"])
    assert len(blockers) == 10
    assert [(row["country_dimension"], row["country_code"]) for row in blockers] == [
        (dimension, country)
        for dimension in ("source_country", "governed_country")
        for country in ("SE", "DK", "NO", "FI", "UNASSIGNED")
    ]


def test_representative_output_serialization_is_stable() -> None:
    payload = build_neotoma_classification_accounting(representative_snapshot())
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()

    assert hashlib.sha256(encoded).hexdigest() == (
        "7dbc93fe7949a0c277b5b395caf0ce21519c00fc6f511ca1c63182e7496d051c"
    )


def test_refusals_remain_exact_and_fail_closed() -> None:
    snapshot = representative_snapshot()
    snapshot["source_family"] = "unknown"
    with pytest.raises(
        ValueError,
        match="^classification accounting requires a Neotoma snapshot$",
    ):
        build_neotoma_classification_accounting(snapshot)

    snapshot = representative_snapshot()
    observations = cast(list[dict[str, object]], snapshot["observations"])
    observations[-1]["source_unit"] = "percentage"
    with pytest.raises(
        ValueError,
        match="^conflicting duplicate observation_id: obs:1$",
    ):
        build_neotoma_classification_accounting(snapshot)
