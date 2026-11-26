"""Malformed source references cannot create chronology selection."""

from copy import deepcopy
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.propagation.source_chronology.indexing import (
    select_source_chronology,
)
from bijux_pollenomics.collection.sources.neotoma.relational.identifiers import (
    source_reference_matches,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows
from tests.unit.collection.sources.neotoma.relational.test_parent_refusals import (
    snapshot,
)


@pytest.mark.parametrize("bad", [{"nested": 1}, [1]])
def test_nonscalar_chronology_ids_are_never_matching_references(bad: object) -> None:
    assert not source_reference_matches(bad, deepcopy(bad))
    assert source_reference_matches(7001, "7001")


@pytest.mark.parametrize("bad", [{"nested": 1}, [1]])
def test_invalid_model_default_age_and_control_are_retained_without_linking(
    bad: object,
) -> None:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    model = nested(rows(unit["chronologies"])[0], "chronology")
    control = rows(model["chroncontrols"])[0]
    sample = rows(nested(unit, "dataset")["samples"])[0]
    age = rows(sample["ages"])[0]
    unit["defaultchronology"] = deepcopy(bad)
    model["chronologyid"] = deepcopy(bad)
    control["chroncontrolid"] = deepcopy(bad)
    age["chronologyid"] = deepcopy(bad)
    sample["ages"] = [age]
    p = snapshot([source])
    affected_model = next(
        x for x in p["chronologies"] if x["source_chronology_id"] == bad
    )
    affected_control = next(
        x for x in p["chronology_controls"] if x["source_chronology_control_id"] == bad
    )
    claim = p["age_claims"][0]
    assert affected_model["selected_by_collection_unit_reference"] is False
    assert ":unidentified:" in affected_model["chronology_id"]
    assert ":control:unidentified:" in affected_control["chronology_control_id"]
    assert claim["chronology_id"] is None and claim["is_default_chronology"] is None
    assert claim["comparability_status"] == "comparable"
    assert claim["source_payload"]["chronologyid"] == bad
    assert claim["chronology_reference_status"] == "invalid_source_reference"
    assert (
        select_source_chronology([claim]).selection_posture
        == "refused_invalid_source_chronology_reference"
    )
    reasons = {o["reason"] for o in p["orphans"]}
    assert {
        "invalid_default_chronology_reference",
        "invalid_source_identifier",
        "invalid_chronology_reference",
    } <= reasons


def test_invalid_default_cannot_select_valid_unique_alternative() -> None:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    unit["defaultchronology"] = {"nested": 1}
    sample = rows(nested(unit, "dataset")["samples"])[0]
    sample["ages"] = [rows(sample["ages"])[0]]
    p = snapshot([source])
    claim = p["age_claims"][0]
    assert claim["comparability_status"] == "comparable"
    assert claim["chronology_reference_status"] == "invalid_source_reference"
    assert (
        select_source_chronology([claim]).selection_posture
        == "refused_invalid_source_chronology_reference"
    )


def test_selector_fails_closed_for_unknown_status_and_mixed_claims() -> None:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    sample = rows(nested(unit, "dataset")["samples"])[0]
    sample["ages"] = [rows(sample["ages"])[0]]
    valid = snapshot([source])["age_claims"][0]
    assert select_source_chronology([valid]).claim is not None
    invalid = deepcopy(valid)
    invalid["chronology_claim_id"] += ":invalid"
    invalid["chronology_reference_status"] = {"unexpected": True}
    selected = select_source_chronology([valid, invalid])
    assert selected.claim is None
    assert selected.refusal_reason == "invalid_source_chronology_reference"


def test_direct_chronology_admission_refuses_invalid_reference_without_reinterpreting_age() -> (
    None
):
    from bijux_pollenomics.analysis.propagation.source_chronology.admission import (
        canonical_claim_interval,
        source_chronology_refusal_reason,
    )

    source = download_row()
    unit = nested(source, "site", "collectionunit")
    unit["defaultchronology"] = {"nested": 1}
    claim = snapshot([source])["age_claims"][0]
    assert canonical_claim_interval(claim) is not None
    assert source_chronology_refusal_reason({}, None, None, claim) == (
        "invalid_source_chronology_reference",
        None,
    )


def test_invalid_model_and_age_materialize_with_native_evidence(tmp_path: Path) -> None:
    from bijux_pollenomics.collection.sources.neotoma.materialization import (
        materialize_neotoma_relational_snapshot,
    )
    from bijux_pollenomics.evidence.sources.neotoma import (
        validate_neotoma_relational_materialization,
    )

    source = download_row()
    unit = nested(source, "site", "collectionunit")
    unit["defaultchronology"] = {"bad": 1}
    model = nested(rows(unit["chronologies"])[0], "chronology")
    model["chronologyid"] = {"bad": 1}
    rows(model["chroncontrols"])[0]["chroncontrolid"] = [1]
    sample = rows(nested(unit, "dataset")["samples"])[0]
    rows(sample["ages"])[0]["chronologyid"] = {"bad": 1}
    payload = snapshot([source])
    output = tmp_path / "snapshot"
    materialize_neotoma_relational_snapshot(output, payload, rows_per_part=1)
    validate_neotoma_relational_materialization(output)


def test_legacy_age_payload_with_invalid_reference_is_not_selected() -> None:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    sample = rows(nested(unit, "dataset")["samples"])[0]
    sample["ages"] = [rows(sample["ages"])[0]]
    claim = snapshot([source])["age_claims"][0]
    assert select_source_chronology([claim]).claim is not None
    legacy = deepcopy(claim)
    legacy["source_payload"]["chronologyid"] = {"bad": 1}
    assert (
        select_source_chronology([legacy]).refusal_reason
        == "invalid_source_chronology_reference"
    )
    legacy["chronology_reference_status"] = "not_recorded"
    assert (
        select_source_chronology([legacy]).refusal_reason
        == "invalid_source_chronology_reference"
    )
