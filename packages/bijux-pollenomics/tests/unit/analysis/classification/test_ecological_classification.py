from __future__ import annotations

import copy
from typing import Any, cast

from bijux_pollenomics.evidence.classification import (
    build_neotoma_classification_accounting,
)


def _observation(
    observation_id: str,
    *,
    variable_id: str,
    taxon_id: int,
    name: str,
    site_id: str = "neotoma:site:1",
    country_code: str = "SE",
    taxon_group: str = "Vascular plants",
    ecological_group: str = "UPHE",
    element: str = "pollen",
    element_type: str | None = "pollen",
    unit: str = "NISP",
    unit_family: str = "count",
) -> dict[str, Any]:
    return {
        "observation_id": observation_id,
        "variable_id": variable_id,
        "site_id": site_id,
        "country_code": country_code,
        "source_taxon_id": taxon_id,
        "source_reported_name": name,
        "source_taxon_group": taxon_group,
        "source_ecological_group": ecological_group,
        "source_element": element,
        "source_element_type": element_type,
        "source_unit": unit,
        "unit_family": unit_family,
    }


def _snapshot(
    observations: list[dict[str, Any]],
    *,
    sites: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    variables_by_id: dict[str, dict[str, Any]] = {}
    for observation in observations:
        variable_id = str(observation["variable_id"])
        variables_by_id.setdefault(
            variable_id,
            {
                "variable_id": variable_id,
                "source_taxon_id": observation["source_taxon_id"],
                "source_reported_name": observation["source_reported_name"],
            },
        )
    return {
        "schema_version": "neotoma-relational-snapshot.v1",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:fixture",
        "build_id": "fixture-build",
        "sites": sites
        or [
            {
                "site_id": "neotoma:site:1",
                "source_geopolitical": ["Sweden", "Skåne"],
            }
        ],
        "variables": list(variables_by_id.values()),
        "observations": observations,
    }


def _concepts_by_name(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    concepts = payload["concepts"]
    assert isinstance(concepts, list)
    return {str(row["source_reported_name"]): row for row in concepts}


def _build(snapshot: dict[str, Any]) -> dict[str, Any]:
    return cast(dict[str, Any], build_neotoma_classification_accounting(snapshot))


def test_biological_labels_never_infer_crop_or_indicator_mappings() -> None:
    labels = (
        (1947, "Poaceae (Cerealia-type)"),
        (220, "Plantago lanceolata"),
        (268, "Rumex"),
        (49802, "Triticum aestivum"),
        (3437, "Alisma plantago-aquatica"),
        (284, "Scrophulariaceae"),
    )
    observations = [
        _observation(
            f"neotoma:observation:{index}",
            variable_id=f"neotoma:variable:{taxon_id}",
            taxon_id=taxon_id,
            name=name,
        )
        for index, (taxon_id, name) in enumerate(labels)
    ]

    payload = _build(_snapshot(observations))

    for concept in _concepts_by_name(payload).values():
        assert concept["mapping_status"] == "unmapped"
        assert concept["accepted_taxon_concept_id"] is None
        assert concept["primary_group_id"] is None
        assert concept["primary_subgroup_id"] is None
        assert concept["role_ids"] == []


def test_source_label_qualifiers_survive_without_resolution_promotion() -> None:
    labels = (
        "Poaceae (Cerealia-type) undiff.",
        "cf. Avena sativa",
        "Avena/Triticum-type",
        "Hordeum group",
        "Rumex acetosella sensu lato",
        "Rumex subg. Acetosa",
    )
    observations = [
        _observation(
            f"observation:{index}",
            variable_id=f"neotoma:variable:{index}",
            taxon_id=index,
            name=name,
        )
        for index, name in enumerate(labels, start=1)
    ]

    payload = _build(_snapshot(observations))
    concepts = _concepts_by_name(payload)

    assert concepts[labels[0]]["source_label_qualifier_markers"] == [
        "type",
        "undifferentiated",
    ]
    assert concepts[labels[1]]["source_label_qualifier_markers"] == ["cf"]
    assert concepts[labels[2]]["source_label_qualifier_markers"] == [
        "type",
        "combined_taxa",
    ]
    assert concepts[labels[3]]["source_label_qualifier_markers"] == ["group"]
    assert concepts[labels[4]]["source_label_qualifier_markers"] == ["sensu_lato"]
    assert concepts[labels[5]]["source_label_qualifier_markers"] == ["subgenus"]
    assert all(row["mapping_status"] == "unmapped" for row in concepts.values())


def test_element_and_unit_variants_are_distinct_source_concepts() -> None:
    observations = [
        _observation(
            "observation:pollen",
            variable_id="neotoma:variable:210",
            taxon_id=210,
            name="Picea",
        ),
        _observation(
            "observation:stomate",
            variable_id="neotoma:variable:210",
            taxon_id=210,
            name="Picea",
            element="stomate",
            element_type="stomate",
        ),
        _observation(
            "observation:concentration-count",
            variable_id="neotoma:variable:63",
            taxon_id=63,
            name="Pollen concentration",
            taxon_group="Laboratory analyses",
            ecological_group="LABO",
            element="concentration",
        ),
        _observation(
            "observation:concentration-volume",
            variable_id="neotoma:variable:63",
            taxon_id=63,
            name="Pollen concentration",
            taxon_group="Laboratory analyses",
            ecological_group="LABO",
            element="concentration",
            unit="grains/cm3",
            unit_family="concentration_per_volume",
        ),
    ]

    payload = _build(_snapshot(observations))
    concepts = payload["concepts"]
    assert isinstance(concepts, list)

    assert len(concepts) == 4
    assert len({row["classification_concept_id"] for row in concepts}) == 4
    assert {
        row["source_element"] for row in concepts if row["source_taxon_id"] == 210
    } == {
        "pollen",
        "stomate",
    }
    assert {
        row["source_evidence_universe"]
        for row in concepts
        if row["source_taxon_id"] == 210
    } == {"source_pollen", "other_or_unresolved_source_element"}
    assert {row["source_unit"] for row in concepts if row["source_taxon_id"] == 63} == {
        "NISP",
        "grains/cm3",
    }
    assert all(
        row["aggregation_posture"] == "exact_source_unit_only" for row in concepts
    )
    assert not any(row["cross_unit_aggregation_allowed"] for row in concepts)
    unit_rows = payload["partitions"]["source_unit"]
    assert sum(row["observation_count"] for row in unit_rows) == 4


def test_only_explicit_lab_and_admin_source_semantics_are_not_applicable() -> None:
    observations = [
        _observation(
            "observation:lab",
            variable_id="neotoma:variable:63",
            taxon_id=63,
            name="Pollen concentration",
            taxon_group="Laboratory analyses",
            ecological_group="LABO",
            element="concentration",
            element_type="concentration",
            unit="grains/cm3",
            unit_family="concentration_per_volume",
        ),
        _observation(
            "observation:admin",
            variable_id="neotoma:variable:9000",
            taxon_id=9000,
            name="Recorded value",
            taxon_group="Administrative variables",
            ecological_group="ADMN",
            element="administrative",
            element_type=None,
        ),
        _observation(
            "observation:name-only",
            variable_id="neotoma:variable:9001",
            taxon_id=9001,
            name="Laboratory crop indicator",
        ),
    ]

    payload = _build(_snapshot(observations))
    concepts = _concepts_by_name(payload)

    assert concepts["Pollen concentration"]["mapping_status"] == "not_applicable"
    assert (
        concepts["Pollen concentration"]["mapping_reason_code"]
        == "source_declares_laboratory_analysis"
    )
    assert concepts["Recorded value"]["mapping_status"] == "not_applicable"
    assert (
        concepts["Recorded value"]["source_element_type_partition"]
        == "not_provided_by_source"
    )
    assert concepts["Laboratory crop indicator"]["mapping_status"] == "unmapped"


def test_duplicate_observation_ids_do_not_inflate_accounting() -> None:
    observation = _observation(
        "observation:duplicate",
        variable_id="neotoma:variable:220",
        taxon_id=220,
        name="Plantago lanceolata",
    )

    payload = _build(_snapshot([observation, copy.deepcopy(observation)]))

    assert payload["reconciliation"]["input_observation_row_count"] == 2
    assert payload["reconciliation"]["unique_observation_count"] == 1
    assert payload["reconciliation"]["duplicate_observation_row_count"] == 1
    assert payload["reconciliation"]["concept_observation_count_sum"] == 1
    blockers = payload["review"]["integrity_blockers"]
    assert blockers == [
        {
            "reason_code": "duplicate_observation_id",
            "subject_id": "observation:duplicate",
            "detail": "1",
        }
    ]


def test_source_and_governed_country_partitions_remain_separate() -> None:
    observations = [
        _observation(
            "observation:country-conflict",
            variable_id="neotoma:variable:220",
            taxon_id=220,
            name="Plantago lanceolata",
            country_code="NO",
        ),
        _observation(
            "observation:unassigned-source",
            variable_id="neotoma:variable:268",
            taxon_id=268,
            name="Rumex",
            site_id="neotoma:site:2",
            country_code="SE",
        ),
    ]
    sites = [
        {
            "site_id": "neotoma:site:1",
            "source_geopolitical": ["Sweden", "Norrbotten"],
        },
        {"site_id": "neotoma:site:2", "source_geopolitical": []},
    ]

    payload = _build(_snapshot(observations, sites=sites))
    partitions = payload["partitions"]

    assert [row["country_code"] for row in partitions["source_country"]] == [
        "SE",
        "DK",
        "NO",
        "FI",
        "UNASSIGNED",
    ]
    assert [row["country_code"] for row in partitions["governed_country"]] == [
        "SE",
        "DK",
        "NO",
        "FI",
        "UNASSIGNED",
    ]
    relation = {
        (row["source_country_code"], row["governed_country_code"]): row[
            "observation_count"
        ]
        for row in partitions["country_relation"]
    }
    assert relation[("SE", "NO")] == 1
    assert relation[("UNASSIGNED", "SE")] == 1
    assert len(payload["review"]["country_release_blockers"]) == 10


def test_status_and_observation_totals_reconcile() -> None:
    observations = [
        _observation(
            "observation:biological",
            variable_id="neotoma:variable:220",
            taxon_id=220,
            name="Plantago lanceolata",
        ),
        _observation(
            "observation:lab",
            variable_id="neotoma:variable:63",
            taxon_id=63,
            name="Pollen concentration",
            taxon_group="Laboratory analyses",
            ecological_group="LABO",
            element="concentration",
            element_type="concentration",
        ),
    ]

    payload = _build(_snapshot(observations))
    reconciliation = payload["reconciliation"]
    statuses = {
        row["value"]: (row["concept_count"], row["observation_count"])
        for row in payload["partitions"]["mapping_status"]
    }

    assert statuses["unmapped"] == (1, 1)
    assert statuses["not_applicable"] == (1, 1)
    assert statuses["accepted"] == (0, 0)
    assert reconciliation["observation_membership_count"] == 2
    assert reconciliation["concept_observation_count_sum"] == 2
    assert reconciliation["mapping_status_concept_count_sum"] == 2
    assert reconciliation["mapping_status_observation_count_sum"] == 2


def test_ids_and_output_order_are_deterministic() -> None:
    observations = [
        _observation(
            "observation:2",
            variable_id="neotoma:variable:268",
            taxon_id=268,
            name="Rumex",
        ),
        _observation(
            "observation:1",
            variable_id="neotoma:variable:220",
            taxon_id=220,
            name="Plantago lanceolata",
        ),
    ]
    forward = _snapshot(observations)
    reverse = copy.deepcopy(forward)
    reverse["observations"] = list(reversed(reverse["observations"]))
    reverse["variables"] = list(reversed(reverse["variables"]))
    reverse["sites"] = list(reversed(reverse["sites"]))

    assert _build(forward) == _build(reverse)


def test_release_is_refused_without_citations_and_named_human_review() -> None:
    observation = _observation(
        "observation:species-label",
        variable_id="neotoma:variable:49802",
        taxon_id=49802,
        name="Triticum aestivum",
    )

    payload = _build(_snapshot([observation]))
    concept = payload["concepts"][0]

    assert payload["release_status"] == "refused"
    assert payload["release_reason_codes"] == [
        "accepted_mapping_not_available",
        "mapping_evidence_not_available",
        "human_review_not_available",
    ]
    assert concept["evidence_reference_ids"] == []
    assert concept["reviewer_id"] is None
    assert concept["decision_date"] is None
    assert concept["release_eligible"] is False
    assert payload["reconciliation"]["accepted_concept_count"] == 0
    assert payload["reconciliation"]["release_eligible_concept_count"] == 0
