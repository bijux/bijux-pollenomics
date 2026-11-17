"""Generated aggregate custody, units and clipped display-footprint contracts."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.raa.point_grid.contracts import BOUNDARY
from bijux_pollenomics.collection.sources.raa.point_grid.projection import GRID


def generated_inputs(root: Path) -> tuple[dict[str, object], bytes]:
    """Build a small disjoint native report without a UUID ledger or database."""
    root.mkdir(exist_ok=True)
    csv = b"west_longitude,south_latitude,uuid_count\n10,57,1\n15,60,2\n"
    report: dict[str, object] = {
        "schema_version": "raa-native-point-grid-v1",
        "source": {"sha256": "a" * 64, "byte_count": 1234},
        "source_CRS": "EPSG:3006",
        "selection": {
            "native_owner": "lamning.uuid",
            "native_class_field": "antikvariskbedomning",
            "native_class_value": "Fornlämning",
            "raw_primary_point_occurrences": 1,
            "valid_primary_point_occurrences": 1,
            "uncertainty_role": "separately_counted_never_selected",
            "disposition_precedence": list(BOUNDARY_DISPOSITIONS),
        },
        "grid": GRID,
        "boundary": BOUNDARY,
        "projection": {"location_support_bounds": [10.03, 54.96, 24.17, 69.07]},
        "counts": {
            "source_uuids": 7,
            "selected_class_uuids": 5,
            "included_uuids": 3,
            "raw_point_occurrences": 6,
            "valid_point_occurrences": 6,
        },
        "dispositions": dict(
            zip(BOUNDARY_DISPOSITIONS, (2, 1, 1, 0, 0, 3), strict=True)
        ),
        "cell_count_total": 3,
        "files": {
            "cell-counts.csv": {
                "sha256": sha256(csv).hexdigest(),
                "byte_count": len(csv),
            }
        },
        "private_path": "never copy this unrecognized input metadata",
    }
    (root / "report.json").write_text(json.dumps(report), encoding="utf-8")
    (root / "cell-counts.csv").write_bytes(csv)
    (root / "uuid-dispositions.ndjson").write_text("MUST NOT READ", encoding="utf-8")
    return report, csv


BOUNDARY_DISPOSITIONS = (
    "unselected_native_class",
    "no_primary_point_occurrence",
    "multiple_primary_point_occurrences",
    "unsupported_sole_point",
    "unsupported_projection_or_location",
    "included",
)


def capture(root: Path):
    """Use independent expected digests and separately declared capture metadata."""
    from bijux_pollenomics.reporting.context.raa_native import (
        NativeRegistrySource,
        capture_native_registry_context,
    )

    return capture_native_registry_context(
        root,
        expected_report_sha256=sha256((root / "report.json").read_bytes()).hexdigest(),
        expected_counts_sha256=sha256(
            (root / "cell-counts.csv").read_bytes()
        ).hexdigest(),
        source=NativeRegistrySource(
            sha256="a" * 64,
            byte_count=1234,
            captured_at_utc="2026-09-13T01:14:04+00:00",
            download_url="https://pub.raa.se/generated.gpkg",
            rights="Public Domain; RAÄ dataset; media excluded",
        ),
    )


def test_full_cell_counts_survive_partial_display_footprint(tmp_path: Path) -> None:
    _, csv = generated_inputs(tmp_path)
    snapshot = capture(tmp_path)
    assert snapshot.counts_bytes == csv
    context = json.loads(snapshot.context_bytes)
    geojson = json.loads(snapshot.cells_bytes)
    assert context["counts"]["included_uuids"] == 3
    assert context["display_accounting"] == {
        "mapped_cells": 2,
        "mapped_full_cell_uuids": 3,
        "partial_footprint_cells": 1,
        "full_cell_uuids_in_partial_cells": 1,
        "withheld_cells": 0,
        "withheld_uuids": 0,
    }
    first, second = geojson["features"]
    assert first["properties"]["native_cell_bounds"] == [10, 57, 11, 58]
    assert first["properties"]["count"] == 1
    assert first["properties"]["partial_display_footprint"] is True
    assert first["geometry"]["coordinates"][0][0] == [10.03, 57.0]
    assert second["geometry"]["coordinates"][0][0] == [15.0, 60.0]
    assert "country" not in first["properties"]
    assert b"private_path" not in snapshot.context_bytes
    assert b"MUST NOT READ" not in snapshot.context_bytes
    assert context["source"]["captured_at_utc"] == "2026-09-13T01:14:04+00:00"
    assert context["scientific_admission"] is False


@pytest.mark.parametrize(
    "field", ["included_uuids", "source_uuids", "selected_class_uuids"]
)
def test_boolean_count_is_not_native_integer(tmp_path: Path, field: str) -> None:
    report, _ = generated_inputs(tmp_path)
    report["counts"][field] = True
    (tmp_path / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="count|integer"):
        capture(tmp_path)


@pytest.mark.parametrize(
    "csv",
    [
        b"west_longitude,south_latitude,uuid_count\n15,60,3\n15,60,0\n",
        b"west_longitude,south_latitude,uuid_count\n15,60,True\n",
        b"west_longitude,south_latitude,uuid_count\n-10,60,3\n",
        b"west_longitude,south_latitude,uuid_count\n15.0,60,3\n",
    ],
)
def test_malformed_or_unowned_cells_refuse(tmp_path: Path, csv: bytes) -> None:
    report, _ = generated_inputs(tmp_path)
    report["files"]["cell-counts.csv"] = {
        "sha256": sha256(csv).hexdigest(),
        "byte_count": len(csv),
    }
    (tmp_path / "report.json").write_text(json.dumps(report))
    (tmp_path / "cell-counts.csv").write_bytes(csv)
    with pytest.raises(ValueError):
        capture(tmp_path)


def test_source_identity_is_bound_to_external_record(tmp_path: Path) -> None:
    report, _ = generated_inputs(tmp_path)
    report["source"]["sha256"] = "b" * 64
    (tmp_path / "report.json").write_text(json.dumps(report))
    with pytest.raises(ValueError, match="source"):
        capture(tmp_path)


def test_zero_included_is_a_valid_empty_sparse_grid(tmp_path: Path) -> None:
    report, _ = generated_inputs(tmp_path)
    csv = b"west_longitude,south_latitude,uuid_count\n"
    report["counts"].update(included_uuids=0, selected_class_uuids=2, source_uuids=4)
    report["dispositions"]["included"] = 0
    report["cell_count_total"] = 0
    report["files"]["cell-counts.csv"] = {
        "sha256": sha256(csv).hexdigest(),
        "byte_count": len(csv),
    }
    (tmp_path / "report.json").write_text(json.dumps(report))
    (tmp_path / "cell-counts.csv").write_bytes(csv)
    snapshot = capture(tmp_path)
    assert json.loads(snapshot.cells_bytes)["features"] == []
    assert json.loads(snapshot.context_bytes)["counts"]["included_uuids"] == 0


def test_alias_input_refused_without_reading_target(tmp_path: Path) -> None:
    generated_inputs(tmp_path)
    target = tmp_path / "marker"
    (tmp_path / "report.json").rename(target)
    (tmp_path / "report.json").symlink_to(target)
    with pytest.raises(ValueError, match="regular|alias"):
        capture(tmp_path)


def test_independent_digest_refuses_redistributed_counts(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.context.raa_native import (
        NativeRegistrySource,
        capture_native_registry_context,
    )

    _, csv = generated_inputs(tmp_path)
    expected = sha256((tmp_path / "report.json").read_bytes()).hexdigest()
    (tmp_path / "cell-counts.csv").write_bytes(csv.replace(b"10,57,1", b"10,57,2"))
    with pytest.raises(ValueError, match="digest"):
        capture_native_registry_context(
            tmp_path,
            expected_report_sha256=expected,
            expected_counts_sha256=sha256(csv).hexdigest(),
            source=NativeRegistrySource(
                "a" * 64,
                1234,
                "2026-09-13T00:00:00Z",
                "https://pub.raa.se/generated.gpkg",
                "Public Domain",
            ),
        )


def test_mutation_between_two_selected_reads_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import BoundedInputTree

    generated_inputs(tmp_path)
    original = BoundedInputTree.read
    fired = []

    def read(tree, path, **kwargs):
        raw = original(tree, path, **kwargs)
        if path.name == "report.json":
            fired.append(path.name)
            counts = tmp_path / "cell-counts.csv"
            counts.write_bytes(counts.read_bytes().replace(b"10,57,1", b"10,57,2"))
        return raw

    monkeypatch.setattr(BoundedInputTree, "read", read)
    with pytest.raises(ValueError, match="identity|namespace|changed"):
        capture(tmp_path)
    assert fired == ["report.json"]


def test_changed_display_operation_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.context.raa_native import projection

    generated_inputs(tmp_path)
    create = projection.Transformer.from_crs

    class ChangedOperation:
        def __init__(self, real):
            self.real = real

        def __getattr__(self, name):
            return (
                "changed_operation"
                if name == "definition"
                else getattr(self.real, name)
            )

    monkeypatch.setattr(
        projection.Transformer,
        "from_crs",
        lambda *args, **kwargs: ChangedOperation(create(*args, **kwargs)),
    )
    with pytest.raises(ValueError, match="operation"):
        capture(tmp_path)
