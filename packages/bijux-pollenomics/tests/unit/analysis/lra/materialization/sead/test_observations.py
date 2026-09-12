"""Absolute element counts and pollen-method links never imply pollen approval."""

from __future__ import annotations

from typing import Any, cast

import pytest

from bijux_pollenomics.analysis.lra.materialization.sead.observations import (
    SeadAccounting,
)
from bijux_pollenomics.analysis.lra.materialization.sead.reading import SeadEvidence

from .support import source_row


def accounting() -> SeadAccounting:
    entity = {
        "entity_relation_id": "entity:1",
        "analysis_entity_id": 1,
        "dataset_id": 1,
        "country_code": "SE",
        "physical_sample_id": 2,
        "sample_group_id": 3,
        "site_uuid": "site",
        "chronology_link": {"claim_ids": ["claim:1", "claim:2"]},
    }
    dataset = {
        "dataset": {"dataset_id": 1, "method_id": 14},
        "source_data_type": {
            "data_type_id": 5,
            "data_type_name": "Abundance",
            "definition": "The absolute number of the counted element (e.g. seeds, fossils) present in the sample.",
        },
    }
    return SeadAccounting(
        cast(SeadEvidence, None),
        {"entity:1": source_row(entity)},
        {"dataset:1": source_row(dataset)},
        {"taxon:1": source_row({"native_name": "not a reviewed taxon"})},
        {},
        {
            14: {
                "method_id": 14,
                "method_name": "Palynology",
                "description": "Pollen analysis.",
            }
        },
        {1: {"abundance_element_id": 1, "element_name": "source element"}},
        {},
    )


def observation(value: Any = 0) -> dict[str, Any]:
    return {
        "source_row": {
            "analysis_entity_id": 1,
            "abundance_element_id": 1,
            "abundance": value,
        },
        "source_value_field": "abundance",
        "source_value": value,
        "entity_relation_id": "entity:1",
        "source_table": "tbl_abundances",
        "country_code": "SE",
        "source_semantics": {
            "dataset_semantics_id": "dataset:1",
            "source_unit_id": None,
        },
        "taxon_relation_id": "taxon:1",
    }


@pytest.mark.parametrize("value", (0, 3.0, 9007199254740993))
def test_source_count_and_linked_method_remain_scientifically_refused(
    value: int | float,
) -> None:
    record = accounting().observation(source_row(observation(value)))
    assert record["exact_nonnegative_integer"] == value
    assert record["source_count_compatibility"] == "source_absolute_count_candidate"
    assert record["source_pollen_method_candidate"] is True
    assert record["source_element"]["element_name"] == "source element"
    assert record["lra_admission_status"] == "refused"
    assert record["pollen_grain_count_eligibility"] == "not_admitted"


@pytest.mark.parametrize("value", (None, "0", True, -1, 1.5))
def test_missing_text_boolean_and_noncounts_remain_distinct(value: Any) -> None:
    record = accounting().observation(source_row(observation(value)))
    assert record["source_count_compatibility"] == "refused"
    assert record["source_observation"]["source_value"] == value
    assert type(record["source_observation"]["source_value"]) is type(value)


def test_absent_is_not_null_and_lookup_is_not_observed_method() -> None:
    owner = accounting()
    row = observation(None)
    del row["source_row"]["abundance"]
    assert owner.observation(source_row(row))["source_value_presence"] == "absent"
    owner.datasets.clear()
    record = owner.observation(source_row(observation()))
    assert 14 in owner.methods
    assert record["source_pollen_method_candidate"] is False


@pytest.mark.parametrize("data_type_id", (6, 9, 10, 13, True, 5.0))
def test_presence_mni_partial_or_wrong_typed_source_id_are_not_absolute_counts(
    data_type_id: Any,
) -> None:
    owner = accounting()
    dataset = owner.datasets["dataset:1"].payload()
    dataset["source_data_type"]["data_type_id"] = data_type_id
    owner.datasets["dataset:1"] = source_row(dataset)
    assert (
        owner.observation(source_row(observation()))["source_count_compatibility"]
        == "refused"
    )


@pytest.mark.parametrize("owner_id", (True, 1.0, 2))
def test_foreign_or_wrong_typed_entity_cannot_supply_counts(owner_id: Any) -> None:
    row = observation()
    row["source_row"]["analysis_entity_id"] = owner_id
    record = accounting().observation(source_row(row))
    assert (
        "source_analysis_entity_ownership_mismatch"
        in record["source_count_reason_codes"]
    )


def test_years_unit_is_not_an_element_count() -> None:
    row = observation()
    row["source_semantics"]["source_unit_id"] = 8
    assert (
        "source_unit_not_admitted_as_count"
        in accounting().observation(source_row(row))["source_count_reason_codes"]
    )
