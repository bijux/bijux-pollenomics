"""Canonical relational evidence preserves every native identity variant."""

from __future__ import annotations

import copy
import hashlib
import itertools
import json
from pathlib import Path
import unittest

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.evidence.sources.neotoma import (
    validate_neotoma_relational_materialization,
)
from bijux_pollenomics.evidence.sources.neotoma.contract import canonical_json_bytes
from tests.support.neotoma import (
    download_row,
)
from tests.support.neotoma.relational_shapes import mapping, nested, rows


class NeotomaRelationalDeterminismTests(unittest.TestCase):
    def test_output_is_invariant_to_download_row_order(self) -> None:
        first = download_row(201)
        second = download_row(202)
        rows(nested(second, "site", "collectionunit", "dataset")["samples"])[0][
            "sampleid"
        ] = 9999
        rows(nested(second, "site", "collectionunit", "dataset")["samples"])[0][
            "analysisunitid"
        ] = 9302

        forward = build_neotoma_relational_snapshot(
            [first, second],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )
        reverse = build_neotoma_relational_snapshot(
            [copy.deepcopy(second), copy.deepcopy(first)],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        self.assertEqual(forward, reverse)


def _named_row(dataset_id: int, label: str) -> dict[str, object]:
    row = download_row(dataset_id)
    sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
    rows(sample["datum"])[0]["variablename"] = label
    return row


def _snapshot(source: list[dict[str, object]]) -> dict[str, object]:
    return build_neotoma_relational_snapshot(
        source,
        source_snapshot_id="sha256:generated-variable-conflicts",
        build_id="generated-variable-conflicts",
    )


def test_variable_identity_is_invariant_to_label_arrival_order() -> None:
    source = [_named_row(201, "Name A"), _named_row(202, "Name B")]
    assert _snapshot(source) == _snapshot(copy.deepcopy(source[::-1]))


def test_chronology_conflicts_preserve_native_json_scalar_types(tmp_path: Path) -> None:
    source = download_row(201)
    chronologies = rows(nested(source, "site", "collectionunit")["chronologies"])
    original = chronologies[0]
    variants = []
    for value in (True, 1, 1.0):
        variant = copy.deepcopy(original)
        mapping(variant["chronology"])["source_quality"] = value
        variants.append(variant)

    snapshots = []
    for order in itertools.permutations(variants):
        candidate = copy.deepcopy(source)
        nested(candidate, "site", "collectionunit")["chronologies"] = [
            *copy.deepcopy(order),
            copy.deepcopy(chronologies[1]),
        ]
        snapshots.append(_snapshot([candidate]))

    assert all(
        canonical_json_bytes(snapshot) == canonical_json_bytes(snapshots[0])
        for snapshot in snapshots[1:]
    )
    conflicts = [
        row
        for row in rows(snapshots[0]["conflicts"])
        if row["conflict_kind"] == "chronology_payload_conflict"
    ]
    assert len(conflicts) == 1
    variants = rows(mapping(conflicts[0]["detail"])["variants"])
    assert {
        json.dumps(mapping(variant["source_payload"])["source_quality"])
        for variant in variants
    } == {"true", "1", "1.0"}
    manifest_path = materialize_neotoma_relational_snapshot(
        tmp_path / "published", snapshots[0], rows_per_part=2
    )
    validate_neotoma_relational_materialization(manifest_path.parent)


def test_repeated_variable_conflict_publishes_six_native_observations(
    tmp_path: Path,
) -> None:
    source = [
        _named_row(201, "Name A"),
        _named_row(202, "Name B"),
        _named_row(203, "Name B"),
    ]
    snapshot = _snapshot(source)
    manifest_path = materialize_neotoma_relational_snapshot(
        tmp_path / "published", snapshot, rows_per_part=2
    )
    manifest = validate_neotoma_relational_materialization(manifest_path.parent)
    surfaces = mapping(manifest["surfaces"])
    assert mapping(surfaces["observations"])["row_count"] == 6
    published = []
    for part in rows(mapping(surfaces["observations"])["parts"]):
        payload = json.loads((manifest_path.parent / str(part["path"])).read_text())
        published.extend(rows(payload["rows"]))
    assert published == rows(snapshot["observations"])
    reverse_root = tmp_path / "reverse-publication"
    materialize_neotoma_relational_snapshot(
        reverse_root, _snapshot(copy.deepcopy(source[::-1])), rows_per_part=2
    )
    published_bytes = {
        path.relative_to(manifest_path.parent): path.read_bytes()
        for path in manifest_path.parent.rglob("*")
        if path.is_file()
    }
    reversed_bytes = {
        path.relative_to(reverse_root): path.read_bytes()
        for path in reverse_root.rglob("*")
        if path.is_file()
    }
    assert published_bytes == reversed_bytes
    conflicts = rows(snapshot["conflicts"])
    assert len(conflicts) == len({row["conflict_id"] for row in conflicts})
    variable_conflicts = [
        row for row in conflicts if row["conflict_kind"] == "variable_identity_conflict"
    ]
    assert len(variable_conflicts) == 1
    assert [
        row["source_reported_name"]
        for row in rows(mapping(variable_conflicts[0]["detail"])["variants"])
    ] == ["Name A", "Name B"]


def test_three_label_multiset_has_canonical_variants_and_native_provenance() -> None:
    source = [
        _named_row(201 + i, label)
        for i, label in enumerate(["Name C", "Name A", "Name B", "Name B"])
    ]
    baseline = _snapshot(source)
    expected_payloads = {
        f"neotoma:dataset:{nested(row, 'site', 'collectionunit', 'dataset')['datasetid']}": copy.deepcopy(
            rows(
                rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0][
                    "datum"
                ]
            )
        )
        for row in source
    }
    for permutation in itertools.permutations(source):
        snapshot = _snapshot(list(copy.deepcopy(permutation)))
        assert snapshot == baseline
        observations = rows(snapshot["observations"])
        assert len(observations) == 8
        for dataset_id, native in expected_payloads.items():
            retained = [
                observation["source_payload"]
                for observation in observations
                if observation["dataset_id"] == dataset_id
            ]
            assert sorted(
                retained, key=lambda datum: str(mapping(datum)["taxonid"])
            ) == sorted(native, key=lambda datum: str(datum["taxonid"]))
        assert all(
            observation["source_snapshot_id"] == "sha256:generated-variable-conflicts"
            and observation["build_id"] == "generated-variable-conflicts"
            for observation in observations
        )
    variable = next(
        row
        for row in rows(baseline["variables"])
        if row["variable_id"] == "neotoma:variable:1947"
    )
    assert variable["source_reported_name"] == "Name A"
    conflict = next(
        row
        for row in rows(baseline["conflicts"])
        if row["conflict_kind"] == "variable_identity_conflict"
    )
    assert mapping(conflict["detail"]) == {
        "resolution": "canonical_minimum",
        "variants": [
            {"source_taxon_id": 1947, "source_reported_name": label}
            for label in ["Name A", "Name B", "Name C"]
        ],
    }


def test_conflicting_identity_preserves_raw_taxon_units_and_element_semantics() -> None:
    source = [_named_row(201, "Name B"), _named_row(202, "Name A")]
    sample = rows(nested(source[1], "site", "collectionunit", "dataset")["samples"])[0]
    datum = rows(sample["datum"])[0]
    datum.update(
        taxonid="1947",
        units="grains/cm3",
        element="measurement",
        elementtype="concentration",
        taxongroup="Laboratory",
        ecologicalgroup="LABO",
    )
    snapshot = _snapshot(source)
    assert snapshot == _snapshot(copy.deepcopy(source[::-1]))
    variable = next(
        row
        for row in rows(snapshot["variables"])
        if row["variable_id"] == "neotoma:variable:1947"
    )
    assert variable["source_units"] == ["NISP", "grains/cm3"]
    semantics = rows(variable["source_semantics"])
    assert {row["source_element"] for row in semantics} == {"pollen", "measurement"}
    assert {row["source_element_type"] for row in semantics} == {
        "pollen",
        "concentration",
    }
    observations = [
        row
        for row in rows(snapshot["observations"])
        if row["variable_id"] == "neotoma:variable:1947"
    ]
    assert len(observations) == 2
    for observation in observations:
        native = mapping(observation["source_payload"])
        for projected, field in (
            ("source_reported_name", "variablename"),
            ("source_taxon_id", "taxonid"),
            ("source_unit", "units"),
            ("source_element", "element"),
            ("source_element_type", "elementtype"),
        ):
            assert observation[projected] == native[field]
        assert observation["aggregation_key"] == f"neotoma:exact-unit:{native['units']}"
    assert {row["unit_family"] for row in observations} == {
        "count",
        "concentration_per_volume",
    }


def test_nonconflicting_snapshot_serialization_is_unchanged() -> None:
    snapshot = _snapshot([download_row()])
    assert (
        hashlib.sha256(canonical_json_bytes(snapshot)).hexdigest()
        == "32c8de3faf1911d1061fb1f4976cc2dc8037435e2e2e96e675e20922bd361ee0"
    )


def test_equal_numeric_taxon_representations_remain_native_variants() -> None:
    source = [_named_row(201 + i, "Name A") for i in range(3)]
    for row, taxon in zip(source, [1947, 1947.0, "1947"], strict=True):
        sample = rows(nested(row, "site", "collectionunit", "dataset")["samples"])[0]
        rows(sample["datum"])[0]["taxonid"] = taxon
    baseline = _snapshot(source)
    for permutation in itertools.permutations(source):
        assert canonical_json_bytes(
            _snapshot(list(permutation))
        ) == canonical_json_bytes(baseline)
    conflict = next(
        row
        for row in rows(baseline["conflicts"])
        if row["conflict_kind"] == "variable_identity_conflict"
    )
    variants = rows(mapping(conflict["detail"])["variants"])
    assert len(variants) == 3
    assert {type(row["source_taxon_id"]) for row in variants} == {int, float, str}
    for observation in rows(baseline["observations"]):
        native = mapping(observation["source_payload"])
        assert type(observation["source_taxon_id"]) is type(native["taxonid"])
