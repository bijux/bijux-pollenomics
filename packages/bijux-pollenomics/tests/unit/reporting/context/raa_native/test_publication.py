"""Finite public derivative ownership and explicit opt-in scope contracts."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from .test_snapshot import capture, generated_inputs


def test_owned_publication_has_only_four_public_aggregate_members(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.context.raa_native.publication import (
        build_native_registry_layer,
        publish_native_registry_context,
    )

    inputs = tmp_path / "input"
    generated_inputs(inputs)
    snapshot = capture(inputs)
    output = tmp_path / "atlas"
    output.mkdir()
    artifacts = publish_native_registry_context(snapshot, output_dir=output)
    root = output / "context/raa-native-registry"
    assert {path.name for path in root.iterdir()} == {
        "context.json",
        "cell-counts.csv",
        "cells.geojson",
        "publication_manifest.json",
    }
    assert len(artifacts) == 4
    manifest = json.loads((root / "publication_manifest.json").read_bytes())
    assert set(manifest["files"]) == {
        "context.json",
        "cell-counts.csv",
        "cells.geojson",
    }
    assert (root / "cell-counts.csv").read_bytes() == snapshot.counts_bytes
    layer = build_native_registry_layer(snapshot)
    assert layer["count"] == 2
    assert layer["kind"] == "cell-counts"
    assert layer["default_enabled"] is False
    assert layer["applies_country_filter"] is False
    assert layer["applies_time_filter"] is False
    assert layer["source_authority_admitted"] is False
    assert layer["scientific_selection_enabled"] is False
    assert "Sweden only" not in layer["coverage_label"]


def test_candidate_substitution_preserves_original_and_foreign(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.core.filesystem import callback_publication
    from bijux_pollenomics.reporting.context.raa_native.publication import (
        publish_native_registry_context,
    )

    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    output = tmp_path / "atlas"
    output.mkdir()
    publish_native_registry_context(snapshot, output_dir=output)
    final = output / "context/raa-native-registry"
    original = (final / "context.json").read_bytes()
    seal = callback_publication.seal_completed_callback_tree
    fired = []

    def substitute(root):
        if root.name == "candidate":
            fired.append(root)
            root.rename(root.with_name("displaced"))
            root.mkdir()
            (root / "foreign").write_bytes(b"preserve")
        return seal(root)

    monkeypatch.setattr(
        callback_publication, "seal_completed_callback_tree", substitute
    )
    with pytest.raises(ValueError):
        publish_native_registry_context(snapshot, output_dir=output)
    assert len(fired) == 1
    assert (final / "context.json").read_bytes() == original
    assert (fired[0] / "foreign").read_bytes() == b"preserve"


def test_explicit_native_scope_and_no_legacy_default(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.context import build_context_layers
    from bijux_pollenomics.reporting.map_publication import map_allows_context_layer

    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    assert map_allows_context_layer(
        scope_key="custom", layer_key="raa-native-registry-cells"
    )
    assert not map_allows_context_layer(
        scope_key="world", layer_key="raa-native-registry-cells"
    )
    assert not map_allows_context_layer(
        scope_key="europe", layer_key="raa-native-registry-cells"
    )
    output = tmp_path / "atlas"
    output.mkdir()
    _, layers, artifacts = build_context_layers(
        (),
        "generated",
        output,
        None,
        native_registry_context=snapshot,
    )
    assert [layer["key"] for layer in layers] == ["raa-native-registry-cells"]
    assert len(artifacts) == 4
    assert not any("raa_atlas_input_status" in relative for _, relative in artifacts)


def test_posture_refuses_scientific_promotion(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.context.raa_native.publication import (
        build_native_registry_layer,
    )
    from bijux_pollenomics.reporting.map_publication_raa_native import (
        native_registry_posture,
    )

    generated_inputs(tmp_path / "input")
    layer = build_native_registry_layer(capture(tmp_path / "input"))
    native_registry_posture(layer)
    for key, bad in (
        ("default_enabled", True),
        ("applies_country_filter", True),
        ("scientific_selection_enabled", True),
        ("edge_count", False),
    ):
        with pytest.raises(ValueError, match="posture"):
            native_registry_posture({**layer, key: bad})


def test_constructed_snapshot_cannot_publish_private_metadata(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.context.raa_native import (
        NativeRegistryContextSnapshot,
    )
    from bijux_pollenomics.reporting.context.raa_native.publication import (
        publish_native_registry_context,
    )

    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    context = json.loads(snapshot.context_bytes)
    context["uuid_ledger"] = "private UUIDs must never be copied"
    forged = NativeRegistryContextSnapshot(
        json.dumps(context).encode(), snapshot.counts_bytes, snapshot.cells_bytes
    )
    output = tmp_path / "atlas"
    output.mkdir()
    with pytest.raises(ValueError):
        publish_native_registry_context(forged, output_dir=output)
    assert not (output / "context").exists()


def test_publication_write_error_survives_secondary_descriptor_close(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import os

    from bijux_pollenomics.reporting.context.raa_native.publication import (
        publish_native_registry_context,
    )

    generated_inputs(tmp_path / "input")
    snapshot = capture(tmp_path / "input")
    output = tmp_path / "atlas"
    output.mkdir()
    write, close = os.write, os.close
    fault = {"fd": None, "closed": False}

    def write_then_refuse(descriptor, body):
        size = write(descriptor, body)
        if b'"raa-native-registry-context-v1"' in bytes(body):
            fault["fd"] = descriptor
            raise ValueError("primary aggregate write refusal")
        return size

    def close_then_refuse(descriptor):
        close(descriptor)
        if descriptor == fault["fd"] and not fault["closed"]:
            fault["closed"] = True
            raise OSError("secondary aggregate close refusal")

    monkeypatch.setattr(os, "write", write_then_refuse)
    monkeypatch.setattr(os, "close", close_then_refuse)
    with pytest.raises(ValueError, match="primary aggregate write refusal") as caught:
        publish_native_registry_context(snapshot, output_dir=output)
    assert fault["closed"]
    assert any("close failed" in note for note in caught.value.__notes__)
    assert not (output / "context/raa-native-registry").exists()


def test_real_generated_producer_to_public_context(tmp_path: Path) -> None:
    from pyproj import Transformer

    from bijux_pollenomics.collection.sources.raa.point_grid import (
        NativePointGridLimits,
        materialize_raa_native_point_grid,
    )
    from bijux_pollenomics.reporting.context.raa_native import (
        NativeRegistrySource,
        capture_native_registry_context,
    )
    from bijux_pollenomics.reporting.context.raa_native.publication import (
        build_native_registry_layer,
    )
    from tests.unit.collection.sources.raa.geometry.support import (
        add_geometry,
        database,
        gpkg,
        identity,
        point,
    )

    source = database(tmp_path)
    import sqlite3

    with sqlite3.connect(source) as connection:
        connection.execute(
            "UPDATE lamning SET antikvariskbedomning=?", ("Fornlämning",)
        )
    east, north = Transformer.from_crs(4619, 3006, always_xy=True).transform(15.5, 60.5)
    add_geometry(source, "point", gpkg(point(east, north)))
    digest, size = identity(source)
    private = tmp_path / "private"
    product = materialize_raa_native_point_grid(
        source,
        expected_sha256=digest,
        expected_byte_count=size,
        destination=private,
        limits=NativePointGridLimits(10, 10, 1024, 1024 * 1024),
    )
    from hashlib import sha256

    snapshot = capture_native_registry_context(
        private,
        expected_report_sha256=product.report_sha256,
        expected_counts_sha256=sha256(
            (private / "cell-counts.csv").read_bytes()
        ).hexdigest(),
        source=NativeRegistrySource(
            digest,
            size,
            "2026-09-13T00:00:00Z",
            "https://pub.raa.se/generated.gpkg",
            "Public Domain",
        ),
    )
    layer = build_native_registry_layer(snapshot)
    assert layer["counts"]["included_uuids"] == 1
    assert layer["geojson"]["features"][0]["properties"]["native_cell_bounds"] == [
        15,
        60,
        16,
        61,
    ]
