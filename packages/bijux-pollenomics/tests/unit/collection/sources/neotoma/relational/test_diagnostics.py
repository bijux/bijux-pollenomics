from __future__ import annotations

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
