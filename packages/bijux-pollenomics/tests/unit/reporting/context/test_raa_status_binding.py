"""RAÄ map selection is pinned to the status used for publication."""

import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, cast

import pytest

from bijux_pollenomics.core.repository import repository_data_root
from bijux_pollenomics.reporting.context.artifacts import stage_context_polygon_layers
from bijux_pollenomics.reporting.context.polygons import (
    build_country_boundary_layer,
    build_density_polygon_layer,
    build_external_polygon_layer,
)
from bijux_pollenomics.reporting.context.raa import (
    RaaAtlasInputSnapshot,
    capture_raa_atlas_input_snapshot,
)


def stage(
    root: Path, output: Path, pin: str
) -> tuple[list[dict[str, object]], list[tuple[str, str]]]:
    return stage_context_polygon_layers(
        scope_key="nordic",
        context_root=root,
        output_dir=output,
        build_country_boundary_layer_fn=build_country_boundary_layer,
        build_density_polygon_layer_fn=build_density_polygon_layer,
        build_external_polygon_layer_fn=build_external_polygon_layer,
        raa_status_sha256=pin,
    )


def test_status_pin_preserves_retained_pair_and_refuses_missing(tmp_path: Path) -> None:
    source = repository_data_root(__file__) / "raa/normalized"
    root = tmp_path / "data"
    target = root / "raa/normalized"
    target.mkdir(parents=True)
    for name in ("sweden_archaeology_layer.json", "sweden_archaeology_density.geojson"):
        shutil.copyfile(source / name, target / name)
    snapshot = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(snapshot.status_bytes).hexdigest()
    assert (
        cast(dict[str, object], snapshot.status()["geometry_publication"])["status"]
        == "retained_context"
    )
    (target / "sweden_archaeology_layer.json").unlink()
    out = tmp_path / "stage"
    out.mkdir()
    with pytest.raises(ValueError, match="status digest"):
        stage(root, out, pin)
    assert list(out.iterdir()) == []
    absent = capture_raa_atlas_input_snapshot(root)
    missing_pin = hashlib.sha256(absent.status_bytes).hexdigest()
    layers, _ = stage(root, out, missing_pin)
    assert not any(x.get("key") == "raa-archaeology" for x in layers)
    status = (out / "context/raa/raa_atlas_input_status.json").read_bytes()
    assert status == absent.status_bytes
    assert json.loads(status)["geometry_publication"]["status"] == "withheld"


def test_capture_and_staging_use_same_held_raa_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.reporting.context import artifacts

    source = repository_data_root(__file__) / "raa/normalized"
    root = tmp_path / "data"
    target = root / "raa/normalized"
    target.mkdir(parents=True)
    for name in ("sweden_archaeology_layer.json", "sweden_archaeology_density.geojson"):
        shutil.copyfile(source / name, target / name)
    original = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(original.status_bytes).hexdigest()

    def capture_then_remove(
        path: Path, *, expected_status_sha256: str
    ) -> RaaAtlasInputSnapshot:
        held = capture_raa_atlas_input_snapshot(
            path, expected_status_sha256=expected_status_sha256
        )
        (target / "sweden_archaeology_layer.json").unlink()
        return held

    monkeypatch.setattr(
        artifacts, "capture_raa_atlas_input_snapshot", capture_then_remove
    )
    out = tmp_path / "stage"
    out.mkdir()
    layers, _ = stage(root, out, pin)
    assert sum(x.get("key") == "raa-archaeology" for x in layers) == 1
    assert (
        out / "context/raa/raa_atlas_input_status.json"
    ).read_bytes() == original.status_bytes
    assert (
        out / "context/raa/sweden_archaeology_density.geojson"
    ).read_bytes() == original.density_bytes
    assert (
        out / "context/raa/sweden_archaeology_layer.json"
    ).read_bytes() == original.metadata_bytes
    manifest = json.loads((out / "context/raa/publication_manifest.json").read_bytes())
    assert manifest["files"]["raa_atlas_input_status.json"]["sha256"] == pin


@pytest.mark.parametrize("root,scope", [(None, "nordic"), ("root", "custom")])
def test_status_pin_cannot_be_silently_ignored(
    tmp_path: Path, root: str | None, scope: str
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(ValueError, match="Nordic RAÄ context"):
        stage_context_polygon_layers(
            scope_key=scope,
            context_root=tmp_path if root else None,
            output_dir=out,
            build_country_boundary_layer_fn=build_country_boundary_layer,
            build_density_polygon_layer_fn=build_density_polygon_layer,
            build_external_polygon_layer_fn=build_external_polygon_layer,
            raa_status_sha256="0" * 64,
        )
    assert list(out.iterdir()) == []


def test_status_pin_rejects_substituted_snapshot_buffers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from dataclasses import replace

    from bijux_pollenomics.reporting.context import artifacts

    source = repository_data_root(__file__) / "raa/normalized"
    root = tmp_path / "data"
    target = root / "raa/normalized"
    target.mkdir(parents=True)
    for name in ("sweden_archaeology_layer.json", "sweden_archaeology_density.geojson"):
        shutil.copyfile(source / name, target / name)
    original = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(original.status_bytes).hexdigest()
    substituted = replace(
        original, density_bytes=b'{"type":"FeatureCollection","features":[]}'
    )
    monkeypatch.setattr(
        artifacts,
        "capture_raa_atlas_input_snapshot",
        lambda *_args, **_kwargs: substituted,
    )
    out = tmp_path / "out"
    out.mkdir()
    with pytest.raises(ValueError, match="captured.*digest"):
        stage(root, out, pin)
    assert list(out.iterdir()) == []


def test_pinned_publication_readback_refuses_tampered_density_and_receipt(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.context.raa_staging import (
        validate_pinned_raa_publication,
    )

    source = repository_data_root(__file__) / "raa/normalized"
    root = tmp_path / "data"
    target = root / "raa/normalized"
    target.mkdir(parents=True)
    for name in ("sweden_archaeology_layer.json", "sweden_archaeology_density.geojson"):
        shutil.copyfile(source / name, target / name)
    snapshot = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(snapshot.status_bytes).hexdigest()
    out = tmp_path / "out"
    out.mkdir()
    stage(root, out, pin)
    validate_pinned_raa_publication(out, pin)
    publication = out / "context/raa"
    density = publication / "sweden_archaeology_density.geojson"
    density.write_bytes(b'{"type":"FeatureCollection","features":[]}')
    manifest_path = publication / "publication_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    manifest["files"][density.name] = {
        "sha256": hashlib.sha256(density.read_bytes()).hexdigest(),
        "byte_count": density.stat().st_size,
    }
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="captured.*digest"):
        validate_pinned_raa_publication(out, pin)


def test_pinned_publication_rejects_boolean_to_integer_manifest_tampering(
    tmp_path: Path,
) -> None:
    from bijux_pollenomics.reporting.context.raa_staging import (
        validate_pinned_raa_publication,
    )

    source = repository_data_root(__file__) / "raa/normalized"
    root = tmp_path / "data"
    target = root / "raa/normalized"
    target.mkdir(parents=True)
    for name in ("sweden_archaeology_layer.json", "sweden_archaeology_density.geojson"):
        shutil.copyfile(source / name, target / name)
    snapshot = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(snapshot.status_bytes).hexdigest()
    out = tmp_path / "out"
    out.mkdir()
    stage(root, out, pin)
    manifest_path = out / "context/raa/publication_manifest.json"
    manifest = json.loads(manifest_path.read_bytes())
    assert manifest["inputs"]["normalized_density"]["present"] is True
    manifest["inputs"]["normalized_density"]["present"] = 1
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="status"):
        validate_pinned_raa_publication(out, pin)


def test_public_map_requires_context_for_raa_status_pin(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.service import generate_multi_country_map

    out = tmp_path / "map"
    out.mkdir()
    (out / "prior").write_text("preserved")
    with pytest.raises(ValueError, match="RAÄ.*context"):
        generate_multi_country_map(
            tmp_path / "v66",
            ("Sweden",),
            out,
            "Nordic",
            "nordic",
            raa_status_sha256="0" * 64,
        )
    assert (out / "prior").read_text() == "preserved"


@pytest.mark.parametrize("mode", ["degraded", "withheld", "wrong_pin", "tamper"])
def test_public_map_binds_selected_raa_status_and_preserves_prior(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting import service
    from bijux_pollenomics.reporting.bundles import atlas_bundle
    from bijux_pollenomics.reporting.bundles.sweden_lake_inputs import SwedenLakeInputs

    root = tmp_path / "data"
    root.mkdir()
    if mode != "withheld":
        source = repository_data_root(__file__) / "raa/normalized"
        target = root / "raa/normalized"
        target.mkdir(parents=True)
        for name in (
            "sweden_archaeology_layer.json",
            "sweden_archaeology_density.geojson",
        ):
            shutil.copyfile(source / name, target / name)
    snapshot = capture_raa_atlas_input_snapshot(root)
    pin = hashlib.sha256(snapshot.status_bytes).hexdigest()
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
    if mode == "tamper":
        original = cast(Any, service).publish_multi_country_map_bundle

        def alter_after_owner(staging: Path, **kwargs: Any) -> None:
            original(staging, **kwargs)
            publication = staging / "context/raa"
            density = publication / "sweden_archaeology_density.geojson"
            density.write_bytes(b'{"type":"FeatureCollection","features":[]}')
            path = publication / "publication_manifest.json"
            manifest = json.loads(path.read_bytes())
            manifest["files"][density.name] = {
                "sha256": hashlib.sha256(density.read_bytes()).hexdigest(),
                "byte_count": density.stat().st_size,
            }
            path.write_text(json.dumps(manifest))

        monkeypatch.setattr(
            service, "publish_multi_country_map_bundle", alter_after_owner
        )
    out = tmp_path / "map"
    out.mkdir()
    (out / "prior").write_text("preserved")
    args = (
        tmp_path / "v66",
        ("Denmark", "Finland", "Norway", "Sweden"),
        out,
        "Nordic",
        "nordic",
    )
    if mode in {"wrong_pin", "tamper"}:
        with pytest.raises(ValueError, match="digest"):
            service.generate_multi_country_map(
                *args,
                context_root=root,
                lake_inputs=SwedenLakeInputs(),
                raa_status_sha256="0" * 64 if mode == "wrong_pin" else pin,
            )
        assert (out / "prior").read_text() == "preserved"
    else:
        service.generate_multi_country_map(
            *args,
            context_root=root,
            lake_inputs=SwedenLakeInputs(),
            raa_status_sha256=pin,
        )
        status = (out / "context/raa/raa_atlas_input_status.json").read_bytes()
        assert status == snapshot.status_bytes
        contract = json.loads(
            (out / "nordic_map_publication_contract.json").read_bytes()
        )
        assert contract["raa_status_binding"]["sha256"] == pin
        assert (out / "context/raa/sweden_archaeology_density.geojson").exists() == (
            mode == "degraded"
        )
        import re

        from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
            normalize_asset_inventory,
        )
        from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
            decode_chunk_script,
        )

        html = (out / "nordic_map.html").read_text()
        match = re.search(
            r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
            html,
            re.S,
        )
        assert match is not None
        assets = cast(
            list[dict[str, Any]],
            normalize_asset_inventory(json.loads(match.group(1))["assets"]),
        )
        nodes = [
            x
            for x in assets
            if x["domain"] == "nodes" and x.get("layer_key") == "raa-archaeology"
        ]
        if mode == "withheld":
            assert nodes == []
        else:
            assert len(nodes) == 1
            asset = nodes[0]
            node = cast(
                dict[str, Any],
                decode_chunk_script(
                    (out / asset["path"]).read_bytes(),
                    expected_asset_key=asset["asset_key"],
                    expected_payload_sha256=asset["payload_sha256"],
                    expected_payload_encoding=asset["payload_encoding"],
                    expected_decoded_byte_count=asset.get("decoded_byte_count"),
                ),
            )
            assert (
                node["features"]
                == json.loads(cast(bytes, snapshot.density_bytes))["features"]
            )


def test_raa_status_pin_refuses_custom_context_builder(tmp_path: Path) -> None:
    from types import SimpleNamespace

    from bijux_pollenomics.reporting.bundles.atlas_bundle.layers import prepare_layers

    root = tmp_path / "source"
    root.mkdir()
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
            raa_status_sha256="0" * 64,
        )
    assert not (tmp_path / "stage").exists()
