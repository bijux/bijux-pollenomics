"""Refused native parents preserve extractable child populations and payloads."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import (
    SOURCE_OCCURRENCE_COUNTER_FIELDS,
    canonical_json_bytes,
    materialization_digest,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows

_REASON_FIELD = "unregistered_source_occurrence_counts_by_reason"
_NATIVE_COUNTS = {
    "site_rows": 1,
    "collection_unit_rows": 1,
    "dataset_rows": 1,
    "sample_rows": 1,
    "chronology_rows": 2,
    "chronology_control_rows": 1,
    "age_claim_rows": 2,
    "observation_rows": 2,
}


def snapshot(source: list[dict[str, object]]) -> dict[str, Any]:
    return build_neotoma_relational_snapshot(
        source, source_snapshot_id="controlled-source", build_id="controlled-build"
    )


def native_parents(source: dict[str, object]) -> dict[str, dict[str, object]]:
    site = nested(source, "site")
    unit = nested(site, "collectionunit")
    dataset = nested(unit, "dataset")
    return {
        "site": site,
        "collection_unit": unit,
        "dataset": dataset,
        "sample": rows(dataset["samples"])[0],
    }


def assert_partition(payload: dict[str, Any]) -> None:
    review = payload["reconciliation"]
    observed: dict[str, dict[str, int]] = {}
    for orphan in payload["orphans"]:
        for counter, count in orphan.get("excluded_source_row_counts", {}).items():
            reasons = observed.setdefault(counter, {})
            reasons[orphan["reason"]] = reasons.get(orphan["reason"], 0) + count
    for table, counter in SOURCE_OCCURRENCE_COUNTER_FIELDS.items():
        entry = review["source_occurrence_accounting"][table]
        reasons = review[_REASON_FIELD][table]
        assert reasons == observed.get(counter, {})
        assert sum(reasons.values()) == entry["unregistered_source_occurrences"]
        assert review["source_row_counts"].get(counter, 0) == (
            review["normalized_row_counts"][table]
            + sum(entry["excluded_occurrence_counts"].values())
            + sum(reasons.values())
        )


@pytest.mark.parametrize(
    ("level", "id_field"),
    [
        ("site", "siteid"),
        ("collection_unit", "collectionunitid"),
        ("dataset", "datasetid"),
        ("sample", "sampleid"),
    ],
)
def test_missing_parent_retains_each_known_child_once(
    level: str, id_field: str, tmp_path: Path
) -> None:
    source = download_row()
    parents = native_parents(source)
    parents[level][id_field] = None
    original = deepcopy(source)
    once = snapshot([source])
    repeated = snapshot([source, deepcopy(source)])
    assert source == original
    for payload, multiplicity in ((once, 1), (repeated, 2)):
        assert_partition(payload)
        assert payload["reconciliation"]["source_row_counts"] == {
            "download_rows": multiplicity,
            **{key: multiplicity * value for key, value in _NATIVE_COUNTS.items()},
        }
        failed = [
            r
            for r in payload["orphans"]
            if r["entity_type"] == level and r["reason"] == "missing_source_identifier"
        ]
        assert len(failed) == multiplicity
        assert all(r["source_value"] == parents[level] for r in failed)
        assert len({r["orphan_id"] for r in failed}) == multiplicity
        for ancestor in ("sites", "collection_units", "datasets", "samples"):
            assert len(payload[ancestor]) == len(once[ancestor])
        output = tmp_path / f"materialized-{multiplicity}"
        materialize_neotoma_relational_snapshot(output, payload, rows_per_part=1)
        validate_neotoma_relational_materialization(output)
    if level == "dataset":
        chronology = [
            r
            for r in once["orphans"]
            if r["reason"] == "dataset_identity_unavailable_for_chronology_projection"
        ]
        assert len(chronology) == 1
        assert chronology[0]["source_value"] == {
            field: parents["collection_unit"][field]
            for field in ("chronologies", "defaultchronology")
        }
        assert chronology[0]["excluded_source_row_counts"] == {
            "chronology_rows": 2,
            "chronology_control_rows": 1,
        }
        assert "chronologies" not in parents["dataset"]
    context = [
        r
        for r in once["orphans"]
        if r["reason"] == "dataset_context_unavailable_for_projection"
    ]
    assert len(context) == (level in {"collection_unit", "dataset"})
    if context:
        assert context[0]["source_value"] == parents["site"]["dataset"]
        assert context[0]["excluded_source_row_counts"] == {}
    parents[level]["caller_mutation"] = True
    assert all(
        "caller_mutation" not in r["source_value"]
        for r in once["orphans"]
        if isinstance(r["source_value"], dict)
    )


@pytest.mark.parametrize("chronologies_present", [False, True])
@pytest.mark.parametrize("default", [None, 7001])
def test_refused_dataset_keeps_native_chronology_selection_context(
    chronologies_present: bool, default: object, tmp_path: Path
) -> None:
    source = download_row()
    parents = native_parents(source)
    unit = parents["collection_unit"]
    unit["defaultchronology"] = default
    if not chronologies_present:
        del unit["chronologies"]
    parents["dataset"]["datasetid"] = None
    payload = snapshot([source])
    assert_partition(payload)
    failed = [
        r
        for r in payload["orphans"]
        if r["reason"] == "dataset_identity_unavailable_for_chronology_projection"
    ]
    assert len(failed) == 1
    assert failed[0]["source_value"] == {
        field: unit[field]
        for field in ("chronologies", "defaultchronology")
        if field in unit
    }
    assert failed[0]["excluded_source_row_counts"] == (
        {"chronology_rows": 2, "chronology_control_rows": 1}
        if chronologies_present
        else {}
    )
    materialize_neotoma_relational_snapshot(tmp_path / "native", payload)


@pytest.mark.parametrize(
    "field", ["samples", "ages", "datum", "chronologies", "chroncontrols"]
)
def test_wrong_list_container_preserves_literal_without_inventing_rows(
    field: str, tmp_path: Path
) -> None:
    for index, value in enumerate((None, {"native": [1, None]}, "literal")):
        source = download_row()
        parents = native_parents(source)
        parent = (
            parents["dataset"]
            if field == "samples"
            else parents["collection_unit"]
            if field == "chronologies"
            else nested(
                rows(parents["collection_unit"]["chronologies"])[0], "chronology"
            )
            if field == "chroncontrols"
            else parents["sample"]
        )
        parent[field] = deepcopy(value)
        payload = snapshot([source])
        assert_partition(payload)
        refused = [
            r for r in payload["orphans"] if r["reason"] == f"invalid_{field}_container"
        ]
        assert len(refused) == 1
        assert refused[0]["source_value"] == value
        assert refused[0]["source_field_present"] is True
        assert refused[0]["excluded_source_row_counts"] == {}
        del parent[field]
        absent = snapshot([source])
        assert not any(
            r["reason"] == f"invalid_{field}_container" for r in absent["orphans"]
        )
        assert (
            absent["reconciliation"]["source_row_counts"]
            == payload["reconciliation"]["source_row_counts"]
        )
        materialize_neotoma_relational_snapshot(tmp_path / f"native-{index}", payload)


@pytest.mark.parametrize("field", ["site", "collectionunit", "dataset"])
def test_wrong_parent_container_retains_exact_value_and_presence(
    field: str, tmp_path: Path
) -> None:
    reasons = {
        "site": "missing_site",
        "collectionunit": "missing_collection_unit",
        "dataset": "missing_dataset",
    }
    for index, value in enumerate((None, [None, "literal"], "literal")):
        source = download_row()
        parents = native_parents(source)
        parent = (
            source
            if field == "site"
            else parents["site"]
            if field == "collectionunit"
            else parents["collection_unit"]
        )
        parent[field] = deepcopy(value)
        payload = snapshot([source])
        assert_partition(payload)
        refused = [r for r in payload["orphans"] if r["reason"] == reasons[field]]
        assert len(refused) == 1
        assert refused[0]["source_value"] == value
        assert refused[0]["source_field_present"] is True
        assert refused[0]["excluded_source_row_counts"] == {}
        del parent[field]
        absent = snapshot([source])
        absent_refused = next(
            r for r in absent["orphans"] if r["reason"] == reasons[field]
        )
        assert absent_refused["source_value"] is None
        assert absent_refused["source_field_present"] is False
        materialize_neotoma_relational_snapshot(tmp_path / f"native-{index}", payload)


def test_registered_identity_fallbacks_are_not_row_exclusions(tmp_path: Path) -> None:
    source = download_row()
    unit = native_parents(source)["collection_unit"]
    chronology = nested(rows(unit["chronologies"])[0], "chronology")
    chronology["chronologyid"] = None
    rows(chronology["chroncontrols"])[0]["chroncontrolid"] = None
    payload = snapshot([source])
    assert_partition(payload)
    fallbacks = [
        r
        for r in payload["orphans"]
        if r["entity_type"] in {"chronology", "chronology_control"}
    ]
    assert len(fallbacks) == 2
    assert all("excluded_source_row_counts" not in r for r in fallbacks)
    assert all(
        not reasons for reasons in payload["reconciliation"][_REASON_FIELD].values()
    )
    materialize_neotoma_relational_snapshot(tmp_path / "native", payload)


def test_malformed_list_entries_have_exact_excluded_counter_maps(
    tmp_path: Path,
) -> None:
    source = download_row()
    parents = native_parents(source)
    unit, dataset, sample = (
        parents[level] for level in ("collection_unit", "dataset", "sample")
    )
    chronology = nested(rows(unit["chronologies"])[0], "chronology")
    for parent, field, malformed in (
        (dataset, "samples", 17),
        (sample, "ages", None),
        (sample, "datum", False),
        (unit, "chronologies", None),
        (unit, "chronologies", {"chronology": False}),
        (chronology, "chroncontrols", "literal"),
    ):
        values = parent[field]
        assert isinstance(values, list)
        values.append(malformed)
    payload = snapshot([source])
    assert_partition(payload)
    expected = {
        "invalid_sample_row": "sample_rows",
        "invalid_age_row": "age_claim_rows",
        "invalid_observation_row": "observation_rows",
        "invalid_chronology_row": "chronology_rows",
        "missing_chronology_payload": "chronology_rows",
        "invalid_chronology_control_row": "chronology_control_rows",
    }
    assert len(payload["orphans"]) == len(expected)
    for orphan in payload["orphans"]:
        assert orphan["excluded_source_row_counts"] == {expected[orphan["reason"]]: 1}
    materialize_neotoma_relational_snapshot(tmp_path / "native", payload)


def refused_sample() -> dict[str, Any]:
    source = download_row()
    native_parents(source)["sample"]["sampleid"] = None
    return snapshot([source])


def tamper(payload: dict[str, Any], condition: str) -> None:
    reasons = payload["reconciliation"][_REASON_FIELD]
    orphan = next(r for r in payload["orphans"] if r["entity_type"] == "sample")
    if condition == "swapped_reason":
        reasons["samples"] = {"invalid_sample_row": 1}
    elif condition == "wrong_reason":
        reasons["samples"] = {"invented_reason": 1}
    elif condition == "missing_table":
        del reasons["observations"]
    elif condition == "boolean":
        reasons["samples"]["missing_source_identifier"] = True
    elif condition == "negative":
        reasons["samples"]["missing_source_identifier"] = -1
    elif condition == "null_block":
        payload["reconciliation"][_REASON_FIELD] = None
    elif condition == "absent_block":
        del payload["reconciliation"][_REASON_FIELD]
    elif condition == "missing_orphan_map":
        del orphan["excluded_source_row_counts"]
    elif condition == "unknown_counter":
        orphan["excluded_source_row_counts"]["variables"] = 1
    elif condition == "orphan_boolean":
        orphan["excluded_source_row_counts"]["sample_rows"] = True
    elif condition == "orphan_reason":
        orphan["reason"] = "invalid_sample_row"
    else:
        raise AssertionError(condition)


def rewrite_published(root: Path, payload: dict[str, Any]) -> None:
    manifest = json.loads((root / "manifest.json").read_bytes())
    part_record = manifest["surfaces"]["orphans"]["parts"][0]
    part = json.loads((root / part_record["path"]).read_bytes())
    part["rows"] = payload["orphans"]
    body = canonical_json_bytes(part)
    (root / part_record["path"]).write_bytes(body)
    part_record["sha256"] = hashlib.sha256(body).hexdigest()
    review_path = root / "reconciliation.json"
    review = json.loads(review_path.read_bytes())
    review["reconciliation"] = payload["reconciliation"]
    body = canonical_json_bytes(review)
    review_path.write_bytes(body)
    manifest["reconciliation"]["sha256"] = hashlib.sha256(body).hexdigest()
    records = [
        {"path": part["path"], "sha256": part["sha256"]}
        for surface in manifest["surfaces"].values()
        for part in surface["parts"]
    ]
    records.append(
        {"path": "reconciliation.json", "sha256": manifest["reconciliation"]["sha256"]}
    )
    manifest["materialization_sha256"] = materialization_digest(records)
    (root / "manifest.json").write_bytes(canonical_json_bytes(manifest))


@pytest.mark.parametrize("boundary", ["writer", "reader"])
@pytest.mark.parametrize(
    "condition",
    [
        "swapped_reason",
        "wrong_reason",
        "missing_table",
        "boolean",
        "negative",
        "null_block",
        "absent_block",
        "missing_orphan_map",
        "unknown_counter",
        "orphan_boolean",
        "orphan_reason",
    ],
)
def test_public_boundaries_bind_reason_partition_to_actual_orphans(
    boundary: str, condition: str, tmp_path: Path
) -> None:
    payload = refused_sample()
    output = tmp_path / "native"
    if boundary == "reader":
        materialize_neotoma_relational_snapshot(output, payload)
    tamper(payload, condition)
    with pytest.raises(ValueError):
        if boundary == "writer":
            materialize_neotoma_relational_snapshot(output, payload)
        else:
            rewrite_published(output, payload)
            validate_neotoma_relational_materialization(output)
    if boundary == "writer":
        assert not output.exists()
        assert not (tmp_path / ".native.staging").exists()


def test_legacy_absence_remains_valid_without_new_orphan_maps(tmp_path: Path) -> None:
    payload = refused_sample()
    del payload["reconciliation"][_REASON_FIELD]
    for orphan in payload["orphans"]:
        orphan.pop("excluded_source_row_counts", None)
    output = tmp_path / "native"
    materialize_neotoma_relational_snapshot(output, payload)
    validate_neotoma_relational_materialization(output)
