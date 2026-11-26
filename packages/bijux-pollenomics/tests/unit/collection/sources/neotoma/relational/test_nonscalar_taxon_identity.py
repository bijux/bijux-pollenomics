"""Malformed taxon IDs remain source evidence, not inferred taxon identities."""

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows
from tests.unit.analysis.propagation.source_chronology.support import (
    derive,
    source_rows,
)
from tests.unit.collection.sources.neotoma.relational.test_parent_refusals import (
    assert_partition,
    snapshot,
)


def produced_pair(bad: object) -> dict[str, Any]:
    source = download_row()
    sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
    first = deepcopy(rows(sample["datum"])[0])
    second = deepcopy(first)
    first["taxonid"] = deepcopy(bad)
    second["taxonid"] = str(bad)
    sample["datum"] = [first, second]
    return snapshot([source])


def grafted_rows(
    observation: dict[str, Any], variable: dict[str, Any]
) -> dict[str, list[dict[str, object]]]:
    out = source_rows()
    out["observations"][0].update(
        variable_id=observation["variable_id"],
        source_taxon_id=observation["source_taxon_id"],
        source_reported_name=observation["source_reported_name"],
        source_ecological_group=observation["source_ecological_group"],
    )
    out["variables"][0].update(
        variable_id=variable["variable_id"],
        source_taxon_id=variable["source_taxon_id"],
        source_reported_name=variable["source_reported_name"],
        source_units=variable["source_units"],
        source_semantics=variable["source_semantics"],
    )
    return out


@pytest.mark.parametrize("bad", [[99], {"nested": 99}])
def test_invalid_taxon_does_not_collide_or_become_taxon_facet(
    bad: object, tmp_path: Path
) -> None:
    payload = produced_pair(bad)
    bad_observation = next(
        x for x in payload["observations"] if x["source_taxon_id"] == bad
    )
    scalar_observation = next(
        x for x in payload["observations"] if x["source_taxon_id"] == str(bad)
    )
    assert bad_observation["source_payload"]["taxonid"] == bad
    assert (
        bad_observation["source_taxon_identifier_status"] == "invalid_source_identifier"
    )
    assert bad_observation["variable_id"] != scalar_observation["variable_id"]
    assert bad_observation["variable_id"].startswith("neotoma:invalid-variable:")
    assert any(
        x["reason"] == "invalid_taxon_identifier" and x["source_value"] == bad
        for x in payload["orphans"]
    )
    assert_partition(payload)
    output = tmp_path / "snapshot"
    materialize_neotoma_relational_snapshot(output, payload, rows_per_part=1)
    validate_neotoma_relational_materialization(output)
    variable = next(
        x
        for x in payload["variables"]
        if x["variable_id"] == bad_observation["variable_id"]
    )
    derived = derive(grafted_rows(bad_observation, variable))
    assert {n.node_level for n in derived.nodes} == {
        "source_sample_presence",
        "source_ecological_code",
    }
    assert any(
        f.node_level == "source_taxon"
        and f.reason_code == "invalid_source_taxon_identifier"
        for f in derived.facet_refusals
    )


def test_legacy_collided_invalid_observation_is_not_backfilled() -> None:
    out = source_rows(taxon_id="[99]", taxon_name="Poaceae")
    out["observations"][0]["source_taxon_id"] = [99]
    result = derive(out)
    assert {n.node_level for n in result.nodes} == {
        "source_sample_presence",
        "source_ecological_code",
    }
    assert any(
        f.node_level == "source_taxon"
        and f.reason_code == "invalid_source_taxon_identifier"
        for f in result.facet_refusals
    )


def test_missing_observation_still_accepts_matching_scalar_variable() -> None:
    out = source_rows(taxon_id="[99]", taxon_name="Poaceae")
    out["observations"][0]["source_taxon_id"] = None
    result = derive(out)
    assert any(
        n.node_level == "source_taxon" and n.source_taxon_id == "[99]"
        for n in result.nodes
    )


def test_invalid_namespace_cannot_be_impersonated_by_a_valid_scalar_id() -> None:
    source = download_row()
    sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
    invalid = deepcopy(rows(sample["datum"])[0])
    invalid["taxonid"] = [99]
    sample["datum"] = [invalid]
    first = snapshot([source])["observations"][0]["variable_id"]
    suffix = first.split(":", 2)[2]
    scalar = deepcopy(invalid)
    scalar["taxonid"] = suffix
    sample["datum"] = [invalid, scalar]
    result = snapshot([source])
    ids = [row["variable_id"] for row in result["observations"]]
    assert len(set(ids)) == 2


def test_classification_accounting_marks_malformed_taxon_for_review() -> None:
    from bijux_pollenomics.evidence.classification.neotoma import (
        build_neotoma_classification_accounting,
    )

    result = build_neotoma_classification_accounting(produced_pair([99]))
    concepts = cast(list[dict[str, object]], result["concepts"])
    bad = next(row for row in concepts if row["source_taxon_id"] == [99])
    scalar = next(row for row in concepts if row["source_taxon_id"] == "[99]")
    assert bad["mapping_status"] == "unmapped"
    assert bad["mapping_reason_code"] == "invalid_source_taxon_identifier"
    assert scalar["mapping_reason_code"] == "mapping_evidence_and_human_review_required"


def test_invalid_variable_cannot_fill_a_missing_observation_taxon() -> None:
    out = source_rows(taxon_id=7, taxon_name="Poaceae")
    out["observations"][0]["source_taxon_id"] = None
    out["variables"][0]["source_taxon_id"] = {"bad": 7}
    result = derive(out)
    assert {node.node_level for node in result.nodes} == {
        "source_sample_presence",
        "source_ecological_code",
    }
    assert any(
        row.node_level == "source_taxon"
        and row.reason_code == "invalid_source_taxon_identifier"
        for row in result.facet_refusals
    )


@pytest.mark.parametrize("status", ["invalid_source_identifier", "unknown", None])
def test_invalid_or_unknown_status_never_admits_taxon_facet(status: object) -> None:
    out = source_rows(taxon_id=7, taxon_name="Poaceae")
    out["observations"][0]["source_taxon_identifier_status"] = status
    result = derive(out)
    assert {node.node_level for node in result.nodes} == {
        "source_sample_presence",
        "source_ecological_code",
    }
    assert any(
        row.reason_code == "invalid_source_taxon_identifier"
        for row in result.facet_refusals
    )


def test_invalid_identifier_digest_is_stable_under_object_key_order() -> None:
    from bijux_pollenomics.collection.sources.neotoma.relational.variables import (
        variable_id,
    )

    left = {"taxonid": {"a": 1, "b": [2]}, "variablename": "Poaceae"}
    right = {"taxonid": {"b": [2], "a": 1}, "variablename": "Poaceae"}
    assert variable_id(left) == variable_id(right)
    assert variable_id(left) != variable_id(
        {"taxonid": None, "variablename": "Poaceae"}
    )
