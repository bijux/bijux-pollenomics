from __future__ import annotations

import copy
import unittest

import pytest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import mapping, nested, rows


class NeotomaRelationalDiagnosticTests(unittest.TestCase):
    def test_missing_chronology_identifiers_are_preserved_and_reported(self) -> None:
        row = download_row()
        chronology = nested(
            rows(nested(row, "site", "collectionunit")["chronologies"])[0], "chronology"
        )
        chronology["chronologyid"] = None
        rows(chronology["chroncontrols"])[0]["chroncontrolid"] = None
        nested(row, "site", "collectionunit")["defaultchronology"] = 7002

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        self.assertEqual(len(rows(payload["chronologies"])), 2)
        self.assertEqual(len(rows(payload["chronology_controls"])), 1)
        self.assertEqual(mapping(payload["reconciliation"])["orphan_count"], 3)
        self.assertEqual(
            {orphan["entity_type"] for orphan in rows(payload["orphans"])},
            {"chronology", "chronology_control", "age_claim"},
        )


@pytest.mark.parametrize("_fixture_id", ["SOURCE-007"])
def test_malformed_datum_reconciles_raw_rows_and_explicit_orphans(
    _fixture_id: str,
) -> None:
    row = download_row()
    sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
    datum = sample["datum"]
    assert isinstance(datum, list)
    datum.append(None)
    payload = build_neotoma_relational_snapshot(
        [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    reconciliation = mapping(payload["reconciliation"])
    raw = mapping(reconciliation["source_row_counts"])["observation_rows"]
    normalized = mapping(reconciliation["normalized_row_counts"])["observations"]
    assert isinstance(raw, int) and isinstance(normalized, int)
    refused = [
        orphan
        for orphan in rows(payload["orphans"])
        if orphan["reason"] == "invalid_observation_row"
    ]
    assert (raw, normalized, len(refused)) == (3, 2, 1)
    assert raw == normalized + len(refused)
    assert refused[0]["source_value"] is None
    assert refused[0]["parent_id"] == rows(payload["samples"])[0]["sample_id"]


@pytest.mark.parametrize(
    ("surface", "raw_count", "table", "reason"),
    [
        ("datum", "observation_rows", "observations", "invalid_observation_row"),
        ("ages", "age_claim_rows", "age_claims", "invalid_age_row"),
        ("samples", "sample_rows", "samples", "invalid_sample_row"),
        ("chronologies", "chronology_rows", "chronologies", "invalid_chronology_row"),
        (
            "controls",
            "chronology_control_rows",
            "chronology_controls",
            "invalid_chronology_control_row",
        ),
        (
            "chronology_payload",
            "chronology_rows",
            "chronologies",
            "missing_chronology_payload",
        ),
    ],
)
def test_malformed_source_rows_retain_exact_payload_multiplicity_and_denominators(
    surface: str, raw_count: str, table: str, reason: str
) -> None:
    row = download_row()
    unit = nested(row, "site", "collectionunit")
    dataset = nested(unit, "dataset")
    sample = rows(dataset["samples"])[0]
    original = [
        "malformed native row",
        {"native_null": None, "native_flag": False},
        9007199254740993,
    ]
    malformed: object = (
        {"chronology": copy.deepcopy(original), "native_label": "malformed wrapper"}
        if surface == "chronology_payload"
        else original
    )
    if surface == "samples":
        target = dataset["samples"]
    elif surface in {"chronologies", "chronology_payload"}:
        target = unit["chronologies"]
    elif surface == "controls":
        target = nested(rows(unit["chronologies"])[0], "chronology")["chroncontrols"]
    else:
        target = sample[surface]
    assert isinstance(target, list)
    target.extend([copy.deepcopy(malformed), copy.deepcopy(malformed)])
    before = copy.deepcopy(row)
    payload = build_neotoma_relational_snapshot(
        [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    excluded = [
        orphan for orphan in rows(payload["orphans"]) if orphan["reason"] == reason
    ]
    assert len(excluded) == 2
    assert len({orphan["orphan_id"] for orphan in excluded}) == 2
    assert all(orphan["source_value"] == malformed for orphan in excluded)
    assert all(orphan["parent_id"] is not None for orphan in excluded)
    reconciliation = mapping(payload["reconciliation"])
    source = mapping(reconciliation["source_row_counts"])[raw_count]
    normalized = mapping(reconciliation["normalized_row_counts"])[table]
    assert isinstance(source, int) and isinstance(normalized, int)
    assert source == normalized + len(excluded)
    assert row == before
    target.reverse()
    reverse = build_neotoma_relational_snapshot(
        [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    assert reverse == payload
    if surface == "chronology_payload":
        failed = next(
            value
            for value in target
            if isinstance(value, dict) and "native_label" in value
        )
        failed["native_label"] = "caller mutation"
    else:
        failed_list = next(value for value in target if isinstance(value, list))
        failed_list.append("caller mutation")
    assert all(orphan["source_value"] == malformed for orphan in excluded)
