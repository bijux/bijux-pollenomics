"""RAÄ map selection is pinned to the status used for publication."""

import hashlib
import json
from pathlib import Path
import shutil
from typing import cast

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
