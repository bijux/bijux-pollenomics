"""Selected Nordic point buffers bind the source bytes they supply."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.context.nordic_point_inputs import (
    NordicPointInputs,
    capture_nordic_point_inputs,
)

POINTS = {
    "landclim-sites": "landclim/normalized/nordic_pollen_site_sequences.geojson",
    "neotoma-pollen": "neotoma/normalized/nordic_pollen_sites.geojson",
    "sead-sites": "sead/normalized/nordic_environmental_sites.geojson",
    "sweden-archaeology-site-discovery": "sead/derived/sweden_archaeology_site_discovery.geojson",
}
TEMPORAL = "sead/normalized/nordic_temporal_evidence.geojson"


def source_inputs(root: Path) -> dict[str, str]:
    pins = {}
    for role, member in POINTS.items():
        target = root / member
        target.parent.mkdir(parents=True, exist_ok=True)
        body = json.dumps(
            {"type": "FeatureCollection", "features": [], "role": role}
        ).encode()
        target.write_bytes(body)
        pins[role] = hashlib.sha256(body).hexdigest()
    return pins


def test_capture_refuses_missing_and_swapped_points(tmp_path: Path) -> None:
    pins = source_inputs(tmp_path)
    for name in POINTS.values():
        path = tmp_path / name
        original = path.read_bytes()
        path.unlink()
        with pytest.raises((ValueError, OSError)):
            capture_nordic_point_inputs(tmp_path, pins)
        path.write_bytes(original)
        path.write_bytes(b"replacement")
        with pytest.raises(ValueError, match="digest"):
            capture_nordic_point_inputs(tmp_path, pins)
        path.write_bytes(original)


def test_held_bytes_drive_decode_and_stage_after_source_change(tmp_path: Path) -> None:
    source = tmp_path / "source"
    pins = source_inputs(source)
    snapshot = capture_nordic_point_inputs(source, pins)
    (source / POINTS["neotoma-pollen"]).write_bytes(b"untrusted replacement")
    destination = tmp_path / "stage"
    destination.mkdir()
    parsed = snapshot.decode("neotoma-pollen")
    snapshot.stage("neotoma-pollen", destination)
    assert parsed["role"] == "neotoma-pollen"
    assert (
        hashlib.sha256(
            (destination / Path(POINTS["neotoma-pollen"]).name).read_bytes()
        ).hexdigest()
        == pins["neotoma-pollen"]
    )
    with pytest.raises((ValueError, FileExistsError)):
        snapshot.stage("neotoma-pollen", destination)


def test_suppressed_temporal_presence_is_rechecked(tmp_path: Path) -> None:
    pins = source_inputs(tmp_path)
    snapshot = capture_nordic_point_inputs(tmp_path, pins)
    assert snapshot.temporal_evidence_present is False
    (tmp_path / TEMPORAL).write_bytes(b"new temporal evidence")
    with pytest.raises(ValueError, match="temporal.*presence"):
        snapshot.validate_temporal_presence()


def test_capture_refuses_symlink_and_unreviewed_pin_set(tmp_path: Path) -> None:
    pins = source_inputs(tmp_path)
    path = tmp_path / POINTS["landclim-sites"]
    path.unlink()
    path.symlink_to(tmp_path / POINTS["neotoma-pollen"])
    with pytest.raises((ValueError, OSError)):
        capture_nordic_point_inputs(tmp_path, pins)
    with pytest.raises(ValueError, match="pin"):
        capture_nordic_point_inputs(
            tmp_path, {"neotoma-pollen": pins["neotoma-pollen"]}
        )


def test_temporal_removal_and_symlinked_ancestor_refuse(tmp_path: Path) -> None:
    root = tmp_path / "source"
    pins = source_inputs(root)
    temporal = root / TEMPORAL
    temporal.write_bytes(b"suppressed source")
    snapshot = capture_nordic_point_inputs(root, pins)
    assert snapshot.temporal_evidence_present is True
    temporal.unlink()
    with pytest.raises(ValueError, match="temporal.*presence"):
        snapshot.validate_temporal_presence()
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    with pytest.raises((ValueError, OSError)):
        capture_nordic_point_inputs(alias, pins)


def test_capture_pins_must_be_exact_and_immutable(tmp_path: Path) -> None:
    pins = source_inputs(tmp_path)
    snapshot = capture_nordic_point_inputs(tmp_path, pins)
    pins["neotoma-pollen"] = "0" * 64
    assert snapshot.decode("neotoma-pollen")["role"] == "neotoma-pollen"
    with pytest.raises(TypeError):
        snapshot.buffers["neotoma-pollen"] = b"altered"  # type: ignore[index]
    with pytest.raises(ValueError, match="pin"):
        capture_nordic_point_inputs(tmp_path, {**pins, "unknown": "0" * 64})


def test_staged_set_rejects_substitution_and_suppressed_surface(tmp_path: Path) -> None:
    root = tmp_path / "source"
    pins = source_inputs(root)
    snapshot = capture_nordic_point_inputs(root, pins)
    stage = tmp_path / "stage"
    stage.mkdir()
    for role in POINTS:
        snapshot.stage(role, stage)
    snapshot.validate_staged(stage)
    target = stage / Path(POINTS["neotoma-pollen"]).name
    original = target.read_bytes()
    target.write_bytes(b"replacement")
    with pytest.raises(ValueError, match="staged point"):
        snapshot.validate_staged(stage)
    target.write_bytes(original)
    (stage / Path(TEMPORAL).name).write_bytes(b"not selected")
    with pytest.raises(ValueError, match="suppressed"):
        snapshot.validate_staged(stage)


def test_point_stager_consumes_held_inputs_and_suppresses_temporal(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.context.artifacts import stage_context_point_layers

    root = tmp_path / "source"
    pins = source_inputs(root)
    (root / TEMPORAL).write_bytes(b"suppressed temporal source")
    held = capture_nordic_point_inputs(root, pins)
    for member in POINTS.values():
        (root / member).write_bytes(b"changed after capture")
    output = tmp_path / "stage"
    output.mkdir()
    layers, _ = stage_context_point_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=output,
        build_external_point_layer_fn=lambda geojson, source_path: {
            "key": geojson["role"],
            "source_name": source_path.name,
        },
        nordic_point_inputs=held,
    )
    assert {layer["key"] for layer in layers} == set(POINTS)
    assert not (output / Path(TEMPORAL).name).exists()
    held.validate_staged(output)


def test_point_stager_refuses_non_nordic_scope(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.context.artifacts import stage_context_point_layers

    root = tmp_path / "source"
    held = capture_nordic_point_inputs(root, source_inputs(root))
    output = tmp_path / "stage"
    output.mkdir()
    with pytest.raises(ValueError, match="Nordic"):
        stage_context_point_layers(
            scope_key="custom",
            context_root=root,
            output_dir=output,
            build_external_point_layer_fn=lambda *_args, **_kwargs: {},
            nordic_point_inputs=held,
        )


def test_direct_capture_model_rejects_partial_and_mutable_bodies(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="point"):
        NordicPointInputs(
            tmp_path, {"neotoma-pollen": b"one"}, False, {"neotoma-pollen": "0" * 64}
        )
    pins = source_inputs(tmp_path)
    capture = capture_nordic_point_inputs(tmp_path, pins)
    with pytest.raises(ValueError, match="digest"):
        NordicPointInputs(
            tmp_path, capture.buffers, False, {**pins, "neotoma-pollen": "0" * 64}
        )
    mutable = dict(capture.buffers)
    mutable["neotoma-pollen"] = bytearray(b"not immutable")  # type: ignore[assignment]
    with pytest.raises(ValueError, match="point"):
        NordicPointInputs(tmp_path, mutable, False, pins)


def test_public_map_refuses_selected_points_without_the_bound_context(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.service import generate_multi_country_map

    root = tmp_path / "source"
    held = capture_nordic_point_inputs(root, source_inputs(root))
    with pytest.raises(ValueError, match="Nordic point"):
        generate_multi_country_map(
            tmp_path / "v66",
            ("Denmark", "Finland", "Norway", "Sweden"),
            tmp_path / "output",
            "Nordic",
            "nordic",
            nordic_point_inputs=held,
        )
    assert not (tmp_path / "output").exists()


@pytest.mark.parametrize("tamper", [False, True])
def test_public_map_checks_staged_selected_points_before_attachment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: bool
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.context.artifacts import stage_context_point_layers

    root = tmp_path / "source"
    held = capture_nordic_point_inputs(root, source_inputs(root))
    output = tmp_path / "map"
    if tamper:
        output.mkdir()
        (output / "prior.txt").write_bytes(b"preserve existing output")
    monkeypatch.setattr(
        service, "build_homo_sapiens_runtime_manifest_for_version_dir", lambda _: None
    )
    monkeypatch.setattr(
        service,
        "load_multi_country_map_inputs",
        lambda **_: SimpleNamespace(country_sample_counts={}, all_samples=()),
    )

    def build(staging: Path, **kwargs: object) -> None:
        assert kwargs["nordic_point_inputs"] is held
        stage_context_point_layers(
            scope_key="nordic",
            context_root=root,
            output_dir=staging,
            build_external_point_layer_fn=lambda geojson, source_path: {
                "key": geojson["role"]
            },
            nordic_point_inputs=held,
        )
        if tamper:
            (staging / Path(POINTS["neotoma-pollen"]).name).write_bytes(b"changed")

    monkeypatch.setattr(service, "publish_multi_country_map_bundle", build)
    arguments = (
        tmp_path / "v66",
        ("Denmark", "Finland", "Norway", "Sweden"),
        output,
        "Nordic",
        "nordic",
    )
    if tamper:
        with pytest.raises(ValueError, match="staged point"):
            service.generate_multi_country_map(
                *arguments, context_root=root, nordic_point_inputs=held
            )
        assert (output / "prior.txt").read_bytes() == b"preserve existing output"
    else:
        service.generate_multi_country_map(
            *arguments, context_root=root, nordic_point_inputs=held
        )
        assert (
            output / Path(POINTS["neotoma-pollen"]).name
        ).read_bytes() == held.buffers["neotoma-pollen"]


def test_real_map_path_builds_and_records_held_point_layers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import re
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs
    from bijux_pollenomics.reporting.context.points import build_external_point_layer
    from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
        normalize_asset_inventory,
    )
    from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
        decode_chunk_script,
    )

    root = tmp_path / "source"
    pins = source_inputs(root)
    for role, member in POINTS.items():
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [15, 60]},
            "properties": {
                "layer_key": role,
                "layer_label": role,
                "record_id": role,
                "name": role,
                "country": "Sweden",
                "source_url": "https://example.invalid/source",
                "popup_rows": [{"label": "Source marker", "value": role}],
                "time_label": "source context",
            },
        }
        body = json.dumps({"type": "FeatureCollection", "features": [feature]}).encode()
        (root / member).write_bytes(body)
        pins[role] = hashlib.sha256(body).hexdigest()
    held = capture_nordic_point_inputs(root, pins)
    for member in POINTS.values():
        (root / member).write_bytes(b"replaced after capture")
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
        nordic_point_inputs=held,
    )
    html = (out / "nordic_map.html").read_text()
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        html,
        re.S,
    )
    assert match is not None
    inventory = cast(
        list[dict[str, Any]],
        normalize_asset_inventory(json.loads(match.group(1))["assets"]),
    )
    seen: dict[str, list[dict[str, Any]]] = {}
    provenance: dict[str, Any] | None = None
    for asset in inventory:
        if asset["domain"] == "provenance":
            provenance = cast(
                dict[str, Any],
                decode_chunk_script(
                    (out / asset["path"]).read_bytes(),
                    expected_asset_key=asset["asset_key"],
                    expected_payload_sha256=asset["payload_sha256"],
                    expected_payload_encoding=asset["payload_encoding"],
                    expected_decoded_byte_count=asset.get("decoded_byte_count"),
                ),
            )
        if asset["domain"] != "nodes" or asset.get("layer_key") not in POINTS:
            continue
        body = (out / asset["path"]).read_bytes()
        chunk = cast(
            dict[str, Any],
            decode_chunk_script(
                body,
                expected_asset_key=asset["asset_key"],
                expected_payload_sha256=asset["payload_sha256"],
                expected_payload_encoding=asset["payload_encoding"],
                expected_decoded_byte_count=asset.get("decoded_byte_count"),
            ),
        )
        seen[asset["layer_key"]] = chunk["features"]
    assert set(seen) == set(POINTS)
    assert provenance is not None
    for role, member in POINTS.items():
        expected_layer = build_external_point_layer(
            held.decode(role), source_path=out / Path(member).name
        )
        assert seen[role] == expected_layer["features"]
        stored = next(
            row["layer"] for row in provenance["layers"] if row["layer"]["key"] == role
        )
        for key, value in expected_layer.items():
            if key != "features":
                assert stored[key] == value
        assert (
            hashlib.sha256((out / Path(member).name).read_bytes()).hexdigest()
            == pins[role]
        )
    contract = json.loads((out / "nordic_map_publication_contract.json").read_bytes())
    assert contract["nordic_selected_point_inputs"] == held.identity()


def test_bundle_refuses_custom_context_builder_with_point_capture(
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers

    root = tmp_path / "source"
    held = capture_nordic_point_inputs(root, source_inputs(root))
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
            nordic_point_inputs=held,
        )
    assert not (tmp_path / "stage").exists()
