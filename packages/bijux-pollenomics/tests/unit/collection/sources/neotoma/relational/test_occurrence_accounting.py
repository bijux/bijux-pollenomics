"""Native occurrence denominators without inventing independent observations."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

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
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows


def snapshot(source: list[dict[str, object]]) -> dict[str, Any]:
    return build_neotoma_relational_snapshot(
        source, source_snapshot_id="controlled-source", build_id="controlled-build"
    )


def check_partitions(payload: dict[str, Any]) -> None:
    reconciliation = payload["reconciliation"]
    accounting = reconciliation["source_occurrence_accounting"]
    assert set(accounting) == set(SOURCE_OCCURRENCE_COUNTER_FIELDS)
    assert "variables" not in accounting
    for table, row in accounting.items():
        normalized = reconciliation["normalized_row_counts"][table]
        excluded = sum(row["excluded_occurrence_counts"].values())
        assert row["registered_occurrences"] == normalized + excluded
        assert reconciliation["source_row_counts"].get(row["source_counter"], 0) == (
            row["registered_occurrences"] + row["unregistered_source_occurrences"]
        )
    for country, counts in reconciliation["country_counts"].items():
        claims = [r for r in payload["age_claims"] if r["country_code"] == country]
        assert counts["age_claim_rows"] == len(claims)
        assert sum(
            counts["age_" + posture]
            for posture in ("comparable", "context_only", "refused", "unresolved")
        ) == len(claims)
        assert counts["observation_rows"] == sum(
            r["country_code"] == country for r in payload["observations"]
        )


def test_repeated_valid_download_preserves_tables_and_materializes(
    tmp_path: Path,
) -> None:
    original = download_row()
    once = snapshot([original])
    repeated = snapshot([original, deepcopy(original)])
    check_partitions(repeated)
    for table, count in once["reconciliation"]["normalized_row_counts"].items():
        assert repeated[table] == once[table]
        if table == "variables":
            continue
        row = repeated["reconciliation"]["source_occurrence_accounting"][table]
        assert row["registered_occurrences"] == 2 * count
        assert row["unregistered_source_occurrences"] == 0
        assert row["excluded_occurrence_counts"] == {
            "repeated_identical_entity_record": count,
            "unselected_conflicting_entity_variant": 0,
        }
    assert repeated["conflicts"] == repeated["orphans"] == []
    for field in (
        "source_row_counts",
        "source_unit_counts",
        "age_comparability_counts",
        "age_reason_counts",
    ):
        assert repeated["reconciliation"][field] == {
            key: 2 * value for key, value in once["reconciliation"][field].items()
        }
    output = tmp_path / "materialized"
    materialize_neotoma_relational_snapshot(output, repeated)
    validate_neotoma_relational_materialization(output)


def test_noncanonical_repeated_conflict_variants_are_order_independent() -> None:
    first = download_row()
    second = deepcopy(first)
    nested(second, "site")["sitename"] = "Distinct source spelling"
    forward = snapshot([first, second, deepcopy(second)])
    reverse = snapshot([second, deepcopy(second), first])
    assert forward == reverse
    check_partitions(forward)
    row = forward["reconciliation"]["source_occurrence_accounting"]["sites"]
    assert row["excluded_occurrence_counts"] == {
        "repeated_identical_entity_record": 1,
        "unselected_conflicting_entity_variant": 1,
    }
    assert len(forward["conflicts"]) == 1
    detail = forward["conflicts"][0]["detail"]
    assert detail["resolution"] == "canonical_minimum"
    assert len(detail["variants"]) == 2
    assert forward["sites"] == snapshot([first, second])["sites"]


def test_identical_native_child_entries_keep_distinct_occurrence_ids() -> None:
    source = download_row()
    sample = rows(nested(source, "site", "collectionunit", "dataset")["samples"])[0]
    for field in ("datum", "ages"):
        values = cast(list[object], sample[field])
        values.append(deepcopy(values[0]))
    payload = snapshot([source])
    check_partitions(payload)
    for table in ("observations", "age_claims"):
        assert len(payload[table]) == 3
        row = payload["reconciliation"]["source_occurrence_accounting"][table]
        assert row["registered_occurrences"] == 3
        assert not any(row["excluded_occurrence_counts"].values())


def test_shared_parent_metadata_across_distinct_datasets_is_not_extra_pollen() -> None:
    first, second = download_row(201), download_row(202)
    sample = rows(nested(second, "site", "collectionunit", "dataset")["samples"])[0]
    sample["sampleid"], sample["analysisunitid"] = 9999, 9302
    forward = snapshot([first, second])
    assert forward == snapshot([second, first])
    check_partitions(forward)
    accounting = forward["reconciliation"]["source_occurrence_accounting"]
    for table in ("sites", "collection_units"):
        assert accounting[table]["excluded_occurrence_counts"] == {
            "repeated_identical_entity_record": 1,
            "unselected_conflicting_entity_variant": 0,
        }
    assert len(forward["datasets"]) == len(forward["samples"]) == 2
    assert len(forward["observations"]) == 4
    assert not any(accounting["observations"]["excluded_occurrence_counts"].values())


@pytest.mark.parametrize(
    ("condition", "table", "unregistered"),
    [
        ("invalid_datum", "observations", 1),
        ("missing_sample_id", "samples", 1),
        ("fallback_chronology", "chronologies", 0),
        ("fallback_control", "chronology_controls", 0),
        ("missing_site", "sites", 0),
    ],
)
def test_unregistered_rows_are_distinct_from_orphan_identity_diagnostics(
    condition: str, table: str, unregistered: int, tmp_path: Path
) -> None:
    source = download_row()
    unit = nested(source, "site", "collectionunit")
    sample = rows(nested(unit, "dataset")["samples"])[0]
    chronology = nested(rows(unit["chronologies"])[0], "chronology")
    if condition == "invalid_datum":
        cast(list[object], sample["datum"]).append(None)
    elif condition == "missing_sample_id":
        sample["sampleid"] = None
    elif condition == "fallback_chronology":
        chronology["chronologyid"] = None
    elif condition == "fallback_control":
        rows(chronology["chroncontrols"])[0]["chroncontrolid"] = None
    else:
        source["site"] = None
    payload = snapshot([source])
    check_partitions(payload)
    row = payload["reconciliation"]["source_occurrence_accounting"][table]
    assert row["unregistered_source_occurrences"] == unregistered
    assert payload["orphans"]
    if condition.startswith("fallback"):
        assert row["registered_occurrences"] > 0
        assert len(payload["orphans"]) > unregistered
    materialize_neotoma_relational_snapshot(tmp_path / "materialized", payload)


def test_historical_reconciliation_without_optional_accounting_still_opens(
    tmp_path: Path,
) -> None:
    payload = snapshot([download_row()])
    del payload["reconciliation"]["source_occurrence_accounting"]
    output = tmp_path / "materialized"
    materialize_neotoma_relational_snapshot(output, payload)
    validate_neotoma_relational_materialization(output)


@pytest.mark.parametrize(
    "tamper",
    [
        "absent_table",
        "lookup_table",
        "counter_name",
        "boolean",
        "negative",
        "repeat_partition",
        "unregistered_partition",
        "missing_reason",
        "null_accounting",
    ],
)
def test_present_occurrence_accounting_must_match_the_native_partition(
    tamper: str, tmp_path: Path
) -> None:
    payload = snapshot([download_row()])
    accounting = payload["reconciliation"]["source_occurrence_accounting"]
    sample = accounting["samples"]
    if tamper == "absent_table":
        del accounting["samples"]
    elif tamper == "lookup_table":
        accounting["variables"] = deepcopy(sample)
    elif tamper == "counter_name":
        sample["source_counter"] = "observation_rows"
    elif tamper == "boolean":
        sample["registered_occurrences"] = True
    elif tamper == "negative":
        sample["registered_occurrences"] = -1
    elif tamper == "repeat_partition":
        sample["excluded_occurrence_counts"]["repeated_identical_entity_record"] = 1
    elif tamper == "unregistered_partition":
        sample["unregistered_source_occurrences"] = 1
    elif tamper == "missing_reason":
        del sample["excluded_occurrence_counts"][
            "unselected_conflicting_entity_variant"
        ]
    else:
        payload["reconciliation"]["source_occurrence_accounting"] = None
    with pytest.raises(ValueError):
        materialize_neotoma_relational_snapshot(tmp_path / "materialized", payload)
    assert not (tmp_path / "materialized").exists()
