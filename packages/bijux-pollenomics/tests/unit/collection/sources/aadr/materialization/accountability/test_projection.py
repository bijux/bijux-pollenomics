"""Compact AADR accountability receipt tests."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS,
    AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION,
    build_aadr_source_accountability_receipt,
    validate_aadr_source_accountability_receipt,
)

from .support import reconciliation, release_manifest_identity, source_table


def _political(receipt: dict[str, object]) -> dict[str, object]:
    return cast(dict[str, object], receipt["source_reported_political_entity"])


def _partitions(receipt: dict[str, object]) -> dict[str, dict[str, object]]:
    return {
        cast(str, row["disposition"]): row
        for row in cast(
            list[dict[str, object]], _political(receipt)["review_partitions"]
        )
    }


def test_receipt_reconciles_every_row_id_and_country_disposition(
    tmp_path: Path,
) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path), release_manifest=release_manifest_identity()
    )
    political = _political(receipt)

    assert receipt["schema_version"] == AADR_SOURCE_ACCOUNTABILITY_SCHEMA_VERSION
    assert cast(dict[str, int], political["denominators"]) == {
        "source_row_count": 12,
        "keyed_source_row_count": 11,
        "unkeyed_source_row_count": 1,
        "genetic_id_count": 7,
    }
    assert cast(dict[str, int], political["genetic_id_disposition_counts"]) == {
        "DK": 1,
        "FI": 1,
        "NO": 1,
        "SE": 1,
        "conflict": 1,
        "missing": 1,
        "other": 1,
    }
    assert cast(
        dict[str, int], political["record_linked_source_row_disposition_counts"]
    ) == {
        "DK": 2,
        "FI": 1,
        "NO": 2,
        "SE": 2,
        "other": 1,
        "missing": 1,
        "conflict": 2,
        "unkeyed": 1,
    }
    assert cast(
        dict[str, int], political["physical_source_row_exact_value_counts"]
    ) == {
        "DK": 3,
        "FI": 1,
        "NO": 2,
        "SE": 3,
        "missing": 2,
        "other": 1,
    }
    assert (
        sum(
            cast(int, row["source_row_count"])
            for row in cast(list[dict[str, object]], political["source_value_counts"])
        )
        == 12
    )
    assert json.loads(json.dumps(receipt, allow_nan=False)) == receipt
    validate_aadr_source_accountability_receipt(receipt)


def test_country_partitions_keep_coordinate_and_chronology_review_separate(
    tmp_path: Path,
) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path), release_manifest=release_manifest_identity()
    )
    partitions = _partitions(receipt)
    denmark_coordinate = cast(dict[str, object], partitions["DK"]["coordinate_review"])
    finland_coordinate = cast(dict[str, object], partitions["FI"]["coordinate_review"])
    other_coordinate = cast(dict[str, object], partitions["other"]["coordinate_review"])
    denmark_chronology = cast(dict[str, object], partitions["DK"]["chronology_review"])
    finland_chronology = cast(dict[str, object], partitions["FI"]["chronology_review"])

    assert denmark_coordinate["genetic_id_availability_counts"] == {
        "missing": 0,
        "present": 1,
        "unusable": 0,
    }
    assert finland_coordinate["genetic_id_availability_counts"] == {
        "missing": 1,
        "present": 0,
        "unusable": 0,
    }
    assert other_coordinate["genetic_id_availability_counts"] == {
        "missing": 0,
        "present": 0,
        "unusable": 1,
    }
    assert (
        cast(dict[str, int], denmark_chronology["date_mean_sign_counts"])["zero"] == 2
    )
    assert (
        cast(dict[str, int], finland_chronology["date_mean_sign_counts"])["negative"]
        == 1
    )
    assert (
        cast(dict[str, int], finland_chronology["date_stddev_sign_counts"])["null"] == 1
    )
    assert all(
        partition["country_assignment_admitted"] is False
        and partition["map_admitted"] is False
        and partition["scientifically_admitted"] is False
        and partition["taxon_scope_status"] == "not_asserted_by_source"
        for partition in partitions.values()
    )
    assert receipt["country_assignment_admitted"] is False
    assert receipt["map_admitted"] is False
    assert receipt["scientifically_admitted"] is False
    assert receipt["taxon_scope_status"] == "not_asserted_by_source"


def test_stream_is_hashed_but_never_materialized_or_tracked(tmp_path: Path) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path), release_manifest=release_manifest_identity()
    )
    projection = cast(dict[str, object], receipt["accountability_projection"])
    stream = cast(dict[str, object], projection["stream"])

    assert stream["line_count"] == 9
    assert cast(int, stream["byte_count"]) > 0
    assert len(cast(str, stream["sha256"])) == 64
    assert stream["materialized"] is False
    assert stream["tracked"] is False
    assert stream["storage_class"] == AADR_ACCOUNTABILITY_STREAM_STORAGE_CLASS
    assert not tuple(tmp_path.rglob("*.jsonl"))


def test_receipt_is_deterministic_when_panel_input_order_changes(
    tmp_path: Path,
) -> None:
    first_reconciliation = reconciliation(tmp_path)
    second_reconciliation = reconcile_aadr_panels(
        tuple(reversed(first_reconciliation.source_tables))
    )

    first = build_aadr_source_accountability_receipt(
        first_reconciliation, release_manifest=release_manifest_identity()
    )
    second = build_aadr_source_accountability_receipt(
        second_reconciliation, release_manifest=release_manifest_identity()
    )

    assert first == second


def test_header_only_source_file_remains_in_compact_accountability(
    tmp_path: Path,
) -> None:
    panel = reconcile_aadr_panels((source_table(tmp_path, "ho", ()),))

    receipt = build_aadr_source_accountability_receipt(
        panel, release_manifest=release_manifest_identity()
    )
    projection = cast(dict[str, object], receipt["accountability_projection"])
    summary = cast(dict[str, object], projection["summary"])
    source_files = cast(list[dict[str, object]], summary["source_files"])

    assert len(source_files) == 1
    assert source_files[0]["source_row_count"] == 0
    assert cast(dict[str, object], projection["stream"])["line_count"] == 1
    assert cast(dict[str, int], _political(receipt)["denominators"]) == {
        "source_row_count": 0,
        "keyed_source_row_count": 0,
        "unkeyed_source_row_count": 0,
        "genetic_id_count": 0,
    }


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("genetic_count", "Genetic-ID dispositions diverge"),
        ("source_value_count", "source-value row denominator diverges"),
        ("stream_materialized", "cannot claim a stored full stream"),
        ("map_admitted", "map_admitted boundary diverges"),
    ),
)
def test_validator_refuses_tampered_denominators_and_admission_claims(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    receipt = build_aadr_source_accountability_receipt(
        reconciliation(tmp_path), release_manifest=release_manifest_identity()
    )
    tampered = deepcopy(receipt)
    political = _political(tampered)
    if mutation == "genetic_count":
        counts = cast(dict[str, int], political["genetic_id_disposition_counts"])
        counts["DK"] += 1
    elif mutation == "source_value_count":
        values = cast(list[dict[str, object]], political["source_value_counts"])
        values[0]["source_row_count"] = cast(int, values[0]["source_row_count"]) + 1
    elif mutation == "stream_materialized":
        projection = cast(dict[str, object], tampered["accountability_projection"])
        cast(dict[str, object], projection["stream"])["materialized"] = True
    else:
        _partitions(tampered)["DK"]["map_admitted"] = True

    with pytest.raises(ValueError, match=message):
        validate_aadr_source_accountability_receipt(tampered)


def test_receipt_refuses_release_or_checkout_identity_mismatch(tmp_path: Path) -> None:
    panel = reconciliation(tmp_path)

    with pytest.raises(ValueError, match="release differs"):
        build_aadr_source_accountability_receipt(
            panel,
            release_manifest=replace(release_manifest_identity(), source_release="v67"),
        )

    absolute_source = replace(
        panel.source_tables[0].source,
        source_path="/checkout/data/aadr/v66/ho/ho.anno",
    )
    absolute_table = replace(
        panel.source_tables[0],
        source=absolute_source,
        rows=tuple(
            replace(row, source=absolute_source) for row in panel.source_tables[0].rows
        ),
    )
    with pytest.raises(ValueError, match="logical source path"):
        build_aadr_source_accountability_receipt(
            reconcile_aadr_panels((absolute_table, panel.source_tables[1])),
            release_manifest=release_manifest_identity(),
        )
