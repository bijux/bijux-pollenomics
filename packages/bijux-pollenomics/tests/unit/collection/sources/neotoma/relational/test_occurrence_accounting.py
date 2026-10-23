"""Native occurrence denominators without inventing independent observations."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
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
    read_validated_neotoma_relational_manifest,
    validate_neotoma_relational_materialization,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import (
    RELATIONAL_TABLE_SURFACES,
    SOURCE_OCCURRENCE_COUNTER_FIELDS,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import nested, rows
from tests.support.repository import REPOSITORY_ROOT


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


@pytest.mark.skipif(
    os.environ.get("BIJUX_POLLENOMICS_NEOTOMA_BOKE_OCCURRENCE_CHECK") != "1",
    reason="explicit opt-in required for the original 24 MB Neotoma source part",
)
def test_native_boke_repeated_download_preserves_all_source_entities(
    tmp_path: Path,
) -> None:
    """Exercise actual native input once and replay it without copying source data."""
    report_path = (
        REPOSITORY_ROOT
        / "docs/report/source-relations/neotoma/boke-native-correspondence/report.json"
    )
    raw_path = (
        REPOSITORY_ROOT
        / "data/neotoma/raw/neotoma_pollen_dataset_downloads/part-008.json"
    )
    for path in (report_path, raw_path):
        assert path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
    authority = json.loads(report_path.read_bytes())
    assert authority["neotoma_dataset_id"] == 54001
    assert authority["neotoma_site_id"] == 28872
    assert 0 < raw_path.stat().st_size <= 32 * 1024**2
    body = raw_path.read_bytes()
    digest = hashlib.sha256(body).hexdigest()
    assert digest == authority["input_sha256"]["neotoma_raw_part"]
    payload = json.loads(body)
    assert payload["row_count"] == len(payload["rows"]) == 25
    selected = [
        r
        for r in payload["rows"]
        if r["site"]["collectionunit"]["dataset"]["datasetid"] == 54001
    ]
    assert len(selected) == 1
    original = selected[0]
    raw_size = len(body)
    del selected, payload, body
    unit = original["site"]["collectionunit"]
    dataset = unit["dataset"]
    assert original["site"]["siteid"] == 28872
    assert unit["collectionunitid"] == 39241 and unit["handle"] == "BOKE"
    native_samples = dataset["samples"]
    assert len(native_samples) == authority["samples"] == 52
    selected_chronologies = [
        c["chronology"]
        for c in unit["chronologies"]
        if c["chronology"]["chronologyid"] == 38422
    ]
    assert len(selected_chronologies) == 1
    assert len(selected_chronologies[0]["chroncontrols"]) == 29
    source_id = "sha256:" + digest
    once = build_neotoma_relational_snapshot(
        [original],
        source_snapshot_id=source_id,
        build_id="native-boke-occurrence-check",
    )
    repeated = build_neotoma_relational_snapshot(
        [original, original],
        source_snapshot_id=source_id,
        build_id="native-boke-occurrence-check",
    )
    for table in RELATIONAL_TABLE_SURFACES:
        assert repeated[table] == once[table]
    check_partitions(once)
    check_partitions(repeated)
    single_review = cast(dict[str, Any], once["reconciliation"])
    repeat_review = cast(dict[str, Any], repeated["reconciliation"])
    assert len(cast(list[object], repeated["samples"])) == 52
    for table, single in single_review["source_occurrence_accounting"].items():
        double = repeat_review["source_occurrence_accounting"][table]
        assert double["registered_occurrences"] == 2 * single["registered_occurrences"]
        assert (
            double["unregistered_source_occurrences"]
            == 2 * single["unregistered_source_occurrences"]
        )
        assert (
            double["excluded_occurrence_counts"][
                "unselected_conflicting_entity_variant"
            ]
            == single["excluded_occurrence_counts"][
                "unselected_conflicting_entity_variant"
            ]
        )
        assert (
            double["excluded_occurrence_counts"]["repeated_identical_entity_record"]
            == single["excluded_occurrence_counts"]["repeated_identical_entity_record"]
            + single["registered_occurrences"]
        )
    for field in (
        "source_row_counts",
        "source_unit_counts",
        "age_comparability_counts",
        "age_reason_counts",
    ):
        assert repeat_review[field] == {
            key: 2 * value for key, value in single_review[field].items()
        }
    for code, values in repeat_review["country_counts"].items():
        for field, value in values.items():
            expected = single_review["country_counts"][code][field]
            assert value == (
                2 * expected
                if field
                in {"site_rows", "collection_unit_rows", "dataset_rows", "sample_rows"}
                else expected
            )

    def identities(records: list[dict[str, Any]]) -> Counter[str]:
        return Counter(
            json.dumps(r, sort_keys=True, separators=(",", ":"), allow_nan=False)
            for r in records
        )

    sample_ids = {s["sampleid"] for s in native_samples}
    assert {
        r["source_sample_id"] for r in cast(list[dict[str, Any]], repeated["samples"])
    } == sample_ids
    for table, field, parent in (
        ("age_claims", "ages", "subject_id"),
        ("observations", "datum", "sample_id"),
    ):
        actual = cast(list[dict[str, Any]], repeated[table])
        for sample in native_samples:
            matching = [
                r for r in actual if r[parent] == f"neotoma:sample:{sample['sampleid']}"
            ]
            assert identities([r["source_payload"] for r in matching]) == identities(
                sample[field]
            )
            if table == "observations":
                assert all(
                    r["source_unit"] == r["source_payload"].get("units")
                    and r["source_value"] == r["source_payload"].get("value")
                    for r in matching
                )
    native_chronologies = [c["chronology"] for c in unit["chronologies"]]
    assert identities(
        [
            r["source_payload"]
            for r in cast(list[dict[str, Any]], repeated["chronologies"])
        ]
    ) == identities(
        [
            {k: v for k, v in c.items() if k != "chroncontrols"}
            for c in native_chronologies
        ]
    )
    assert identities(
        [
            r["source_payload"]
            for r in cast(list[dict[str, Any]], repeated["chronology_controls"])
        ]
    ) == identities(
        [control for c in native_chronologies for control in c["chroncontrols"]]
    )
    sites = cast(list[dict[str, Any]], repeated["sites"])
    assert sites[0]["country_code"] == "UNASSIGNED"
    assert sites[0]["country_decision_method"] == "missing_country_decision"
    assert sites[0]["country_propagation_eligible"] is False
    output = tmp_path / "materialized"
    materialize_neotoma_relational_snapshot(output, repeated)
    manifest = cast(dict[str, Any], read_validated_neotoma_relational_manifest(output))
    for table, surface in manifest["surfaces"].items():
        restored = [
            row
            for part in surface["parts"]
            for row in json.loads((output / part["path"]).read_bytes())["rows"]
        ]
        assert restored == repeated[table]
    print(
        json.dumps(
            {
                "raw_source": str(raw_path.relative_to(REPOSITORY_ROOT)),
                "raw_bytes": raw_size,
                "dataset_id": 54001,
                "site_id": 28872,
                "native_samples": len(native_samples),
                "selected_chronology_id": 38422,
                "selected_controls": 29,
                "normalized_counts": repeat_review["normalized_row_counts"],
                "single_occurrence_accounting": single_review[
                    "source_occurrence_accounting"
                ],
                "repeated_occurrence_accounting": repeat_review[
                    "source_occurrence_accounting"
                ],
                "country_counts": repeat_review["country_counts"],
            },
            sort_keys=True,
        )
    )
