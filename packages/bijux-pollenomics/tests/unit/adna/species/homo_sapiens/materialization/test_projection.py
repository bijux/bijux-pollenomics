"""Versioned AADR accountability projection tests."""

from dataclasses import replace
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization import (
    AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION,
    AadrPanelReconciliation,
    AadrSourceTable,
    build_aadr_accountability_summary,
    iter_aadr_accountability_json_lines,
    iter_aadr_accountability_projection,
    iter_aadr_accountability_records,
    load_aadr_source_table,
    reconcile_aadr_panels,
    validate_aadr_accountability_summary,
)

_HEADER = "\t".join(
    (
        "Genetic ID",
        "Method for Determining Date",
        "Date mean in BP",
        "Date standard deviation in BP",
        "Full Date",
        "Latitude",
        "Longitude",
        "Source note",
    )
)


def _table(
    tmp_path: Path,
    dataset_name: str,
    rows: list[tuple[str, ...]],
    *,
    source_name: str | None = None,
) -> AadrSourceTable:
    source = _HEADER + "\n" + "\n".join("\t".join(row) for row in rows) + "\n"
    source_path = tmp_path / f"{source_name or dataset_name}.anno"
    source_path.write_text(source, encoding="utf-8")
    return load_aadr_source_table(
        source_path, source_release="v66", dataset_name=dataset_name
    )


def _reconciliation(tmp_path: Path) -> AadrPanelReconciliation:
    ho = _table(
        tmp_path,
        "ho",
        [
            (" ID-1 ", "Direct", "0", "0", "100-80 BP", "0", "0", " keep "),
            ("ID-2", "Context", "-25.50", "10.0", "-30--20 BP", "..", "..", "negative"),
            ("  ", "", "..", "", "..", "..", "..", "unkeyed"),
        ],
    )
    capture = _table(
        tmp_path,
        "1240k",
        [
            ("ID-1", "Direct", "0.0", "0.0", "100-80 BP", "1", "2", "conflict"),
        ],
    )
    return reconcile_aadr_panels((ho, capture))


def _record_by_id(
    records: list[dict[str, object]], genetic_id: str
) -> dict[str, object]:
    return next(record for record in records if record.get("genetic_id") == genetic_id)


def test_projection_is_versioned_deterministic_and_json_serializable(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)
    ordered_tables = (
        _table(
            tmp_path,
            "ho-copy",
            [("ID-A", "Modern", "0", "0", "present", "0", "0", "a")],
        ),
        _table(
            tmp_path,
            "capture-copy",
            [("ID-B", "Direct", "1", "1", "1-0 BP", "1", "1", "b")],
        ),
    )

    projected = list(iter_aadr_accountability_projection(reconciliation))
    assert (
        projected[0]["schema_version"] == AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION
    )
    assert all(
        record["schema_version"] == AADR_ACCOUNTABILITY_PROJECTION_SCHEMA_VERSION
        for record in projected
    )
    assert json.loads(json.dumps(projected, allow_nan=False)) == projected
    assert list(
        iter_aadr_accountability_projection(reconcile_aadr_panels(ordered_tables))
    ) == list(
        iter_aadr_accountability_projection(
            reconcile_aadr_panels(tuple(reversed(ordered_tables)))
        )
    )


def test_json_lines_stream_has_stable_encoding_and_no_decimal_objects(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)

    lines = iter_aadr_accountability_json_lines(reconciliation)
    first_line = next(lines)
    remaining_lines = list(lines)
    decoded = [json.loads(first_line), *(json.loads(line) for line in remaining_lines)]

    assert first_line.endswith("\n")
    assert (
        first_line
        == json.dumps(
            decoded[0],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    )
    assert len(decoded) == 1 + len(reconciliation.records) + len(
        reconciliation.unkeyed_rows
    )


def test_projection_preserves_null_zero_negative_and_atomic_conflicts(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)
    records = list(iter_aadr_accountability_records(reconciliation))
    zero = _record_by_id(records, "ID-1")
    negative = _record_by_id(records, "ID-2")

    zero_chronology = cast(list[dict[str, object]], zero["chronology_evidence_groups"])
    zero_means = {
        cast(dict[str, object], group["date_mean_bp"])["decimal_value"]
        for group in zero_chronology
    }
    assert zero_means == {"0", "0.0"}
    zero_coordinates = cast(list[dict[str, object]], zero["coordinate_evidence_groups"])
    assert {(group["latitude"], group["longitude"]) for group in zero_coordinates} == {
        (0.0, 0.0),
        (1.0, 2.0),
    }
    assert {group["refusal_reason_code"] for group in zero_coordinates} == {None}
    assert "latitude" not in zero
    assert "longitude" not in zero
    assert cast(dict[str, object], zero["statuses"])["coordinate"] == "conflict"

    [negative_coordinate] = cast(
        list[dict[str, object]], negative["coordinate_evidence_groups"]
    )
    assert negative_coordinate["latitude_raw"] == ".."
    assert negative_coordinate["latitude"] is None
    assert negative_coordinate["refusal_reason_code"] == "coordinate_missing"
    [negative_chronology] = cast(
        list[dict[str, object]], negative["chronology_evidence_groups"]
    )
    negative_mean = cast(dict[str, object], negative_chronology["date_mean_bp"])
    assert negative_mean == {
        "raw_value": "-25.50",
        "decimal_value": "-25.50",
        "status": "parsed",
        "sign": "negative",
    }
    assert negative_chronology["scientifically_admitted"] is False
    assert negative_chronology["refusal_reason_code"] == (
        "method_specific_policy_required"
    )


def test_projection_preserves_source_links_columns_and_raw_tokens(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)
    records = list(iter_aadr_accountability_records(reconciliation))
    record = _record_by_id(records, "ID-1")
    source_rows = cast(list[dict[str, object]], record["source_rows"])

    assert len(source_rows) == 2
    assert all(
        "source_sha256" in cast(dict[str, object], row["source_row"])
        for row in source_rows
    )
    assert {cast(list[str], row["raw_tokens"])[-1] for row in source_rows} == {
        " keep ",
        "conflict",
    }
    source_row_keys = {
        cast(dict[str, object], row["source_row"])["key"] for row in source_rows
    }
    coordinate_groups = cast(
        list[dict[str, object]], record["coordinate_evidence_groups"]
    )
    chronology_groups = cast(
        list[dict[str, object]], record["chronology_evidence_groups"]
    )
    assert {
        key
        for group in coordinate_groups
        for key in cast(list[str], group["source_row_keys"])
    } == source_row_keys
    assert {
        key
        for group in chronology_groups
        for key in cast(list[str], group["source_row_keys"])
    } == source_row_keys
    assert all(
        row["taxon_scope_status"] == "not_asserted_by_source" for row in source_rows
    )
    assert record["taxon_scope_status"] == "not_asserted_by_source"
    assert record["scientifically_admitted"] is False


def test_summary_denominators_reconcile_every_row_group_and_genetic_id(
    tmp_path: Path,
) -> None:
    summary = build_aadr_accountability_summary(_reconciliation(tmp_path))
    denominators = cast(dict[str, int], summary["denominators"])
    status_counts = cast(dict[str, dict[str, int]], summary["status_counts"])
    dataset_counts = cast(dict[str, dict[str, int]], summary["dataset_counts"])
    source_files = cast(list[dict[str, object]], summary["source_files"])

    assert denominators == {
        "source_file_count": 2,
        "source_row_count": 4,
        "keyed_source_row_count": 3,
        "unkeyed_source_row_count": 1,
        "genetic_id_count": 2,
        "coordinate_evidence_group_count": 4,
        "chronology_evidence_group_count": 4,
    }
    assert sum(status_counts["reconciliation"].values()) == 2
    assert sum(status_counts["coordinate_evidence"].values()) == 4
    assert sum(status_counts["chronology_evaluation"].values()) == 4
    assert sum(dataset_counts["source_rows"].values()) == 4
    assert dataset_counts["source_rows"] == {"1240k": 1, "ho": 3}
    assert len(source_files) == 2
    assert sum(cast(int, item["source_row_count"]) for item in source_files) == 4
    assert all(item["column_names"] == _HEADER.split("\t") for item in source_files)
    assert {cast(str, item["source_file_key"]) for item in source_files} == {
        cast(str, cast(dict[str, object], row["source_row"])["source_file_key"])
        for record in iter_aadr_accountability_records(_reconciliation(tmp_path))
        for row in cast(list[dict[str, object]], record["source_rows"])
    }
    assert status_counts["panel"]["conflict"] == 0
    assert status_counts["coordinate_evidence"]["non_finite"] == 0
    assert status_counts["taxon_scope_unkeyed_rows"] == {"not_asserted_by_source": 1}
    assert summary["scientifically_admitted"] is False
    assert summary["scientifically_admitted_chronology_group_count"] == 0
    assert summary["taxon_scope_status"] == "not_asserted_by_source"


def test_projection_fails_when_source_row_denominator_diverges(tmp_path: Path) -> None:
    reconciliation = _reconciliation(tmp_path)
    invalid = replace(
        reconciliation, source_row_count=reconciliation.source_row_count + 1
    )

    with pytest.raises(ValueError, match="source-row denominator diverges"):
        build_aadr_accountability_summary(invalid)


def test_source_file_ledger_keeps_distinct_files_from_the_same_dataset(
    tmp_path: Path,
) -> None:
    identical_row = (
        "ID-1",
        "Modern",
        "0",
        "0",
        "present",
        "0",
        "0",
        "same bytes",
    )
    first = _table(
        tmp_path,
        "ho",
        [identical_row],
        source_name="ho-first",
    )
    second = _table(
        tmp_path,
        "ho",
        [identical_row],
        source_name="ho-second",
    )

    forward = reconcile_aadr_panels((first, second))
    reverse = reconcile_aadr_panels((second, first))
    forward_projection = list(iter_aadr_accountability_projection(forward))
    reverse_projection = list(iter_aadr_accountability_projection(reverse))
    summary = forward_projection[0]
    source_files = cast(list[dict[str, object]], summary["source_files"])
    dataset_counts = cast(dict[str, dict[str, int]], summary["dataset_counts"])

    assert len(source_files) == 2
    assert len({item["source_file_key"] for item in source_files}) == 2
    assert {item["dataset_name"] for item in source_files} == {"ho"}
    assert len({item["source_sha256"] for item in source_files}) == 1
    assert [item["source_row_count"] for item in source_files] == [1, 1]
    assert dataset_counts["source_rows"] == {"ho": 2}
    assert forward_projection == reverse_projection


def test_source_file_ledger_preserves_header_only_physical_input(
    tmp_path: Path,
) -> None:
    populated = _table(
        tmp_path,
        "ho",
        [("ID-1", "Modern", "0", "0", "present", "0", "0", "populated")],
    )
    empty_path = tmp_path / "header-only.anno"
    empty_path.write_text(_HEADER + "\n", encoding="utf-8")
    header_only = load_aadr_source_table(
        empty_path, source_release="v66", dataset_name="1240k"
    )

    forward = list(
        iter_aadr_accountability_projection(
            reconcile_aadr_panels((populated, header_only))
        )
    )
    reverse = list(
        iter_aadr_accountability_projection(
            reconcile_aadr_panels((header_only, populated))
        )
    )
    summary = forward[0]
    source_files = cast(list[dict[str, object]], summary["source_files"])
    denominators = cast(dict[str, int], summary["denominators"])
    dataset_counts = cast(dict[str, dict[str, int]], summary["dataset_counts"])

    assert forward == reverse
    assert denominators["source_file_count"] == 2
    assert denominators["source_row_count"] == 1
    assert {
        item["dataset_name"]: item["source_row_count"] for item in source_files
    } == {
        "1240k": 0,
        "ho": 1,
    }
    assert all(item["column_names"] == _HEADER.split("\t") for item in source_files)
    assert dataset_counts["source_rows"] == {"1240k": 0, "ho": 1}


def test_summary_validator_rejects_source_file_ledger_tampering(
    tmp_path: Path,
) -> None:
    summary = build_aadr_accountability_summary(_reconciliation(tmp_path))
    tampered = cast(dict[str, object], json.loads(json.dumps(summary)))
    source_files = cast(list[dict[str, object]], tampered["source_files"])
    source_files[0]["source_row_count"] = (
        cast(int, source_files[0]["source_row_count"]) + 1
    )

    with pytest.raises(ValueError, match="source-file ledger denominator diverges"):
        validate_aadr_accountability_summary(tampered)


def test_projection_fails_when_atomic_group_links_drop_a_source_row(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)
    target = reconciliation.records[0]
    truncated_group = replace(target.coordinate_groups[0], source_rows=())
    invalid_record = replace(
        target,
        coordinate_groups=(truncated_group, *target.coordinate_groups[1:]),
    )
    invalid = replace(
        reconciliation,
        records=(invalid_record, *reconciliation.records[1:]),
    )

    with pytest.raises(ValueError, match="coordinate evidence-group links diverge"):
        list(iter_aadr_accountability_records(invalid))


def test_projection_fails_when_atomic_group_changes_linked_source_evidence(
    tmp_path: Path,
) -> None:
    reconciliation = _reconciliation(tmp_path)
    target = reconciliation.records[0]
    first_group, second_group = target.coordinate_groups
    altered_group = replace(first_group, evidence=second_group.evidence)
    invalid_record = replace(
        target,
        coordinate_groups=(altered_group, second_group),
    )
    invalid = replace(
        reconciliation,
        records=(invalid_record, *reconciliation.records[1:]),
    )

    with pytest.raises(ValueError, match="coordinate evidence group changes"):
        list(iter_aadr_accountability_records(invalid))
