"""Selected polygon capture binds consumed and staged bytes."""

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.context.artifacts import stage_context_polygon_layers
from bijux_pollenomics.reporting.context.nordic_polygon_inputs import (
    capture_nordic_polygon_inputs,
)

BOUNDARY = "boundaries/normalized/nordic_country_boundaries.geojson"
TEMPORAL = "landclim/normalized/nordic_reveals_temporal_grid_cells.geojson"
STATIC = "landclim/normalized/nordic_reveals_grid_cells.geojson"


def payload(label: str) -> bytes:
    return json.dumps(
        {"type": "FeatureCollection", "features": [], "label": label}
    ).encode()


def test_captured_polygons_drive_staging_and_temporal_precedence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "data"
    out = tmp_path / "output"
    out.mkdir()
    for name, body in [
        (BOUNDARY, payload("boundary")),
        (TEMPORAL, payload("temporal")),
        (STATIC, payload("fallback")),
    ]:
        p = root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(body)
    pins = {
        "country-boundaries": hashlib.sha256(payload("boundary")).hexdigest(),
        "landclim-reveals-temporal-grid": hashlib.sha256(
            payload("temporal")
        ).hexdigest(),
    }
    held = capture_nordic_polygon_inputs(root, pins)
    (root / BOUNDARY).write_bytes(payload("mutated"))
    (root / TEMPORAL).unlink()
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.context.artifacts.map_allows_context_layer",
        lambda *, scope_key, layer_key: layer_key in pins,
    )
    layers, _ = stage_context_polygon_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=out,
        build_country_boundary_layer_fn=lambda x: {**x, "key": "country-boundaries"},
        build_density_polygon_layer_fn=lambda x: x,
        build_external_polygon_layer_fn=lambda x, **kw: {
            **x,
            "key": "landclim-reveals-temporal-grid",
        },
        nordic_polygon_inputs=held,
    )
    assert [x["label"] for x in layers] == ["boundary", "temporal"]
    assert (out / Path(BOUNDARY).name).read_bytes() == payload("boundary")
    assert (out / Path(TEMPORAL).name).read_bytes() == payload("temporal")
    assert not (out / Path(STATIC).name).exists()
    held.validate_staged(out)
    (out / Path(STATIC).name).write_bytes(payload("fallback"))
    with pytest.raises(ValueError, match="suppressed"):
        held.validate_staged(out)
    (out / Path(STATIC).name).unlink()
    (out / Path(TEMPORAL).name).write_bytes(payload("tampered"))
    with pytest.raises(ValueError, match="staged"):
        held.validate_staged(out)


def test_capture_rejects_missing_temporal_and_bad_pins(tmp_path: Path) -> None:
    boundary = tmp_path / BOUNDARY
    boundary.parent.mkdir(parents=True)
    boundary.write_bytes(payload("boundary"))
    pins = {
        "country-boundaries": hashlib.sha256(payload("boundary")).hexdigest(),
        "landclim-reveals-temporal-grid": "0" * 64,
    }
    with pytest.raises((ValueError, OSError)):
        capture_nordic_polygon_inputs(tmp_path, pins)


def test_polygon_stager_refuses_missing_context_before_writing(tmp_path: Path) -> None:
    root = tmp_path / "data"
    pins = {}
    for role, name in [
        ("country-boundaries", BOUNDARY),
        ("landclim-reveals-temporal-grid", TEMPORAL),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload(role))
        pins[role] = hashlib.sha256(payload(role)).hexdigest()
    held = capture_nordic_polygon_inputs(root, pins)
    output = tmp_path / "output"
    output.mkdir()
    with pytest.raises(ValueError, match="bound Nordic context"):
        stage_context_polygon_layers(
            scope_key="nordic",
            context_root=None,
            output_dir=output,
            build_country_boundary_layer_fn=lambda x: x,
            build_density_polygon_layer_fn=lambda x: x,
            build_external_polygon_layer_fn=lambda x, **kw: x,
            nordic_polygon_inputs=held,
        )
    assert list(output.iterdir()) == []


@pytest.mark.parametrize("tamper", [False, True])
def test_public_map_validates_polygon_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: bool
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service

    root = tmp_path / "data"
    pins = {}
    for role, name in [
        ("country-boundaries", BOUNDARY),
        ("landclim-reveals-temporal-grid", TEMPORAL),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload(role))
        pins[role] = hashlib.sha256(payload(role)).hexdigest()
    held = capture_nordic_polygon_inputs(root, pins)
    output = tmp_path / "output"
    if tamper:
        output.mkdir()
        (output / "prior").write_text("retained")
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(country_sample_counts={}, all_samples=()),
    )

    def build(staging: Path, **kwargs: object) -> None:
        assert kwargs["nordic_polygon_inputs"] is held
        for role in pins:
            held.stage(role, staging)
        if tamper:
            (staging / Path(TEMPORAL).name).write_bytes(b"tampered")

    monkeypatch.setattr(service, "publish_multi_country_map_bundle", build)
    args = (
        tmp_path / "v66",
        ("Denmark", "Finland", "Norway", "Sweden"),
        output,
        "Nordic",
        "nordic",
    )
    if tamper:
        with pytest.raises(ValueError, match="staged polygon"):
            service.generate_multi_country_map(
                *args, context_root=root, nordic_polygon_inputs=held
            )
        assert (output / "prior").read_text() == "retained"
    else:
        service.generate_multi_country_map(
            *args, context_root=root, nordic_polygon_inputs=held
        )
        assert (output / Path(TEMPORAL).name).read_bytes() == payload(
            "landclim-reveals-temporal-grid"
        )


def test_real_public_map_records_captured_polygon_selection(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs

    root = tmp_path / "data"
    feature = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[10, 60], [11, 60], [11, 61], [10, 60]]],
        },
        "properties": {
            "layer_key": "landclim-reveals-temporal-grid",
            "layer_label": "Captured temporal grid",
            "record_id": "held",
            "country": "Sweden",
        },
    }
    boundary = json.dumps({"type": "FeatureCollection", "features": [feature]}).encode()
    grid = json.dumps({"type": "FeatureCollection", "features": [feature]}).encode()
    for member, body in [(BOUNDARY, boundary), (TEMPORAL, grid)]:
        path = root / member
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
    pins = {
        "country-boundaries": hashlib.sha256(boundary).hexdigest(),
        "landclim-reveals-temporal-grid": hashlib.sha256(grid).hexdigest(),
    }
    held = capture_nordic_polygon_inputs(root, pins)
    (root / TEMPORAL).write_bytes(b"altered after capture")
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(
            country_sample_counts=dict.fromkeys(
                ("Denmark", "Finland", "Norway", "Sweden"), 0
            ),
            all_samples=(),
        ),
    )
    monkeypatch.setattr(
        atlas_bundle,
        "build_tracked_animal_atlas_bundle",
        lambda **_: SimpleNamespace(
            point_layers=(),
            extra_artifacts=(),
            localities=(),
            coordinate_review=SimpleNamespace(
                direct_coordinate_feature_count=0,
                named_site_geocoded_feature_count=0,
                weaker_geography_feature_count=0,
            ),
        ),
    )
    monkeypatch.setattr(
        atlas_bundle, "animal_sample_chronology_context_available", lambda _: False
    )
    monkeypatch.setattr(
        atlas_bundle,
        "build_map_evidence_projection",
        lambda *_args, **_kwargs: SimpleNamespace(
            detail_records=(), reconciliation={}, point_layers=()
        ),
    )
    out = tmp_path / "map"
    service.generate_multi_country_map(
        tmp_path / "v66",
        ("Denmark", "Finland", "Norway", "Sweden"),
        out,
        "Nordic",
        "nordic",
        context_root=root,
        lake_inputs=SwedenLakeInputs(),
        nordic_polygon_inputs=held,
    )
    assert (out / Path(BOUNDARY).name).read_bytes() == boundary
    assert (out / Path(TEMPORAL).name).read_bytes() == grid
    contract = json.loads((out / "nordic_map_publication_contract.json").read_bytes())
    assert contract["nordic_selected_polygon_inputs"] == held.identity()
    import re

    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        (out / "nordic_map.html").read_text(),
        re.S,
    )
    assert match is not None
    inventory = cast(
        list[dict[str, Any]],
        normalize_asset_inventory(json.loads(match.group(1))["assets"]),
    )
    provenance = next(item for item in inventory if item["domain"] == "provenance")
    decoded = cast(
        dict[str, Any],
        decode_chunk_script(
            (out / provenance["path"]).read_bytes(),
            expected_asset_key=provenance["asset_key"],
            expected_payload_sha256=provenance["payload_sha256"],
            expected_payload_encoding=provenance["payload_encoding"],
            expected_decoded_byte_count=provenance.get("decoded_byte_count"),
        ),
    )
    layers = {item["layer"]["key"]: item["layer"] for item in decoded["layers"]}
    assert layers["country-boundaries"]["geojson"]["type"] == "FeatureCollection"
    assert layers["landclim-reveals-temporal-grid"]["label"] == "Captured temporal grid"
    for role in pins:
        asset = next(
            item
            for item in inventory
            if item["domain"] == "nodes" and item.get("layer_key") == role
        )
        chunk = cast(
            dict[str, Any],
            decode_chunk_script(
                (out / asset["path"]).read_bytes(),
                expected_asset_key=asset["asset_key"],
                expected_payload_sha256=asset["payload_sha256"],
                expected_payload_encoding=asset["payload_encoding"],
                expected_decoded_byte_count=asset.get("decoded_byte_count"),
            ),
        )
        assert chunk["features"] == [feature]


def test_invalid_grid_is_refused_before_polygon_staging(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = tmp_path / "data"
    out = tmp_path / "out"
    out.mkdir()
    pins = {}
    for role, name, body in [
        ("country-boundaries", BOUNDARY, payload("boundary")),
        ("landclim-reveals-temporal-grid", TEMPORAL, b"not json"),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        pins[role] = hashlib.sha256(body).hexdigest()
    held = capture_nordic_polygon_inputs(root, pins)
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.context.artifacts.map_allows_context_layer",
        lambda **_: True,
    )
    with pytest.raises(ValueError, match="JSON"):
        stage_context_polygon_layers(
            scope_key="nordic",
            context_root=root,
            output_dir=out,
            build_country_boundary_layer_fn=lambda x: {"key": "country-boundaries"},
            build_density_polygon_layer_fn=lambda x: x,
            build_external_polygon_layer_fn=lambda x, **kw: x,
            nordic_polygon_inputs=held,
        )
    assert list(out.iterdir()) == []


def test_capture_refuses_wrong_digest_and_symlink(tmp_path: Path) -> None:
    root = tmp_path / "source"
    pins = {}
    for role, name in [
        ("country-boundaries", BOUNDARY),
        ("landclim-reveals-temporal-grid", TEMPORAL),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload(role))
        pins[role] = hashlib.sha256(payload(role)).hexdigest()
    with pytest.raises(ValueError, match="digest"):
        capture_nordic_polygon_inputs(root, {**pins, "country-boundaries": "0" * 64})
    target = root / TEMPORAL
    target.unlink()
    target.symlink_to(root / BOUNDARY)
    with pytest.raises((ValueError, OSError)):
        capture_nordic_polygon_inputs(root, pins)


def test_bundle_refuses_custom_context_builder_for_polygon_capture(
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers

    root = tmp_path / "source"
    pins = {}
    for role, name in [
        ("country-boundaries", BOUNDARY),
        ("landclim-reveals-temporal-grid", TEMPORAL),
    ]:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload(role))
        pins[role] = hashlib.sha256(payload(role)).hexdigest()
    held = capture_nordic_polygon_inputs(root, pins)
    with pytest.raises(ValueError, match="maintained context owner"):
        prepare_layers(
            tmp_path / "stage",
            report=SimpleNamespace(),
            version="v66",
            all_samples=(),
            context_root=root,
            geography_scope=None,
            build_atlas_bundle_paths_fn=lambda **_: None,
            build_context_layers_fn=lambda **_: ([], [], []),
            build_samples_geojson_fn=lambda _: {},
            atlas_detail_records=None,
            atlas_scientific_signals=None,
            atlas_edge_records=None,
            atlas_sequence_records=None,
            surface=SimpleNamespace(),
            nordic_polygon_inputs=held,
        )
    assert not (tmp_path / "stage").exists()
