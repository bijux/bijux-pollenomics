"""Authenticate the current atlas transport without widening scientific support."""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.map_document.render import _RUNTIME_LOADER
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.map_document.static_assets.serialization import (
    canonical_json,
    chunk_script_bytes,
    decode_chunk_script,
)
from bijux_pollenomics_dev.ci.atlas_browser.candidate_files import regular_bytes
from bijux_pollenomics_dev.source_completion import landclim_map_export_lineage as owner

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def published(tmp_path: Path) -> tuple[Path, dict[str, Any], list[dict[str, Any]]]:
    features = [
        {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x, 55], [x + 1, 55], [x + 1, 56], [x, 55]]],
            },
            "properties": {"record_id": f"cell-{i}", "country": country},
        }
        for i, (x, country) in enumerate(((10, "Denmark"), (15, "Sweden")))
    ]
    (tmp_path / owner.CHUNKS).mkdir(parents=True)
    assets = write_static_atlas_assets(
        tmp_path / owner.CHUNKS,
        slug="nordic",
        version="fixture",
        point_layers=[
            {"key": "unrelated", "features": [{"latitude": 1, "longitude": 1}]}
        ],
        polygon_layers=[
            {
                "key": "landclim-reveals-temporal-grid",
                "geojson": {"type": "FeatureCollection", "features": features},
            }
        ],
    )
    return tmp_path, assets.manifest, features


@pytest.fixture(scope="module")
def runtime() -> bytes:
    page = (ROOT / owner.MAP).read_text()
    source, paths = owner._published_script(ROOT, page)
    assert len(paths) == 1
    return source.encode()


def page_for(repository: Path, manifest: dict[str, Any], body: bytes) -> str:
    digest = hashlib.sha256(body).hexdigest()
    name = f"nordic_map.atlas-runtime.{digest[:16]}.js"
    (repository / owner.CHUNKS / name).write_bytes(body)
    integrity = "sha256-" + base64.b64encode(hashlib.sha256(body).digest()).decode()
    bootstrap = {
        **manifest,
        "runtime": {"path": name, "byte_count": len(body), "integrity": integrity},
    }
    return (
        '<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps(bootstrap)
        + '</script><script id="atlas-modeled-context-binding" type="application/json">'
        + json.dumps(
            owner._map_manifest((ROOT / owner.MAP).read_text(), script=body.decode())
        )
        + "</script>"
        + _RUNTIME_LOADER
    )


def test_actual_external_runtime_retains_manifest_and_export_contract(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], runtime: bytes
) -> None:
    repository, manifest, projected = published
    script, paths = owner._published_script(
        repository, page_for(repository, manifest, runtime)
    )
    assert script.encode() == runtime
    assert len(paths) == 1
    page = page_for(repository, manifest, runtime)
    assert owner._map_manifest(page, script=script)
    owner._export_contract(script)
    legacy = 'const MODELED_CONTEXT = {"legacy":true};'
    assert owner._published_script(repository, legacy) == (legacy, [])
    assert owner._map_manifest(legacy) == {"legacy": True}


@pytest.mark.parametrize("damage", ["body", "size", "sri", "path", "link"])
def test_runtime_authentication_refuses_independent_damage(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]],
    runtime: bytes,
    damage: str,
) -> None:
    repository, manifest, projected = published
    page = page_for(repository, manifest, runtime)
    digest = hashlib.sha256(runtime).hexdigest()
    if damage == "body":
        (
            repository / owner.CHUNKS / f"nordic_map.atlas-runtime.{digest[:16]}.js"
        ).write_bytes(runtime + b" ")
    elif damage == "size":
        page = page.replace(f'"byte_count": {len(runtime)}', '"byte_count": true')
    elif damage == "sri":
        page = page.replace('"integrity": "sha256-', '"integrity": "sha512-', 1)
    elif damage == "path":
        page = page.replace('"path": "nordic_map.', '"path": "../nordic_map.', 1)
    else:
        page = page.replace(
            "script.src = runtime.path;", "script.src = 'unbound.js';", 1
        )
    with pytest.raises(ValueError, match="(?i)published"):
        owner._published_script(repository, page)


def test_authenticated_runtime_still_requires_real_export_functions(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], runtime: bytes
) -> None:
    repository, manifest, projected = published
    changed = runtime.replace(
        b"function downloadModeledContextFrame()", b"function missingDownload()"
    )
    assert changed != runtime
    script, _ = owner._published_script(
        repository, page_for(repository, manifest, changed)
    )
    with pytest.raises(ValueError, match="selector or identity"):
        owner._export_contract(script)


def test_only_declared_landclim_nodes_are_read_and_membership_is_complete(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, manifest, projected = published
    rows = normalize_asset_inventory(manifest["assets"])
    selected = [
        row for row in rows if row.get("layer_key") == "landclim-reveals-temporal-grid"
    ]
    unrelated = next(row for row in rows if row.get("layer_key") == "unrelated")
    (repository / owner.CHUNKS / cast(str, unrelated["path"])).unlink()
    read = regular_bytes
    observed: list[Path] = []

    def observe(path: Path) -> bytes:
        observed.append(path)
        return read(path)

    monkeypatch.setattr(owner, "regular_bytes", observe)
    features, paths = owner._published_features(repository, projected)
    assert {feature["properties"]["record_id"] for feature in features} == {
        "cell-0",
        "cell-1",
    }
    assert paths == [
        repository / owner.CHUNKS / cast(str, row["path"]) for row in selected
    ]
    assert observed == [repository / owner.ASSETS, *paths]


@pytest.mark.parametrize("damage", ["missing", "body", "duplicate"])
def test_selected_node_damage_is_refused(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], damage: str
) -> None:
    repository, manifest, projected = published
    rows = normalize_asset_inventory(manifest["assets"])
    selected = next(
        row for row in rows if row.get("layer_key") == "landclim-reveals-temporal-grid"
    )
    path = repository / owner.CHUNKS / cast(str, selected["path"])
    if damage == "missing":
        path.unlink()
    elif damage == "body":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        rows.append(deepcopy(selected))
        altered = {
            **manifest,
            "schema_version": "atlas-static-bootstrap.v1",
            "assets": rows,
        }
        (repository / owner.ASSETS).write_text(json.dumps(altered))
    with pytest.raises(ValueError):
        owner._published_features(repository, projected)


def test_resealed_swapped_source_indexes_are_refused(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]],
) -> None:
    repository, manifest, projected = published
    rows = normalize_asset_inventory(manifest["assets"])
    for row in rows:
        if row.get("layer_key") != "landclim-reveals-temporal-grid":
            continue
        old = repository / owner.CHUNKS / cast(str, row["path"])
        payload = decode_chunk_script(
            old.read_bytes(),
            expected_asset_key=cast(str, row["asset_key"]),
            expected_payload_sha256=cast(str, row["payload_sha256"]),
            expected_payload_encoding=cast(str, row["payload_encoding"]),
            expected_decoded_byte_count=cast(int, row["decoded_byte_count"]),
        )
        indexes = cast(list[int], payload["feature_indexes"])
        payload["feature_indexes"] = [1 - index for index in indexes]
        text = canonical_json(payload)
        payload_sha = hashlib.sha256(text.encode()).hexdigest()
        body = chunk_script_bytes(
            asset_key=cast(str, row["asset_key"]),
            payload_sha256=payload_sha,
            payload_json=text,
            payload_encoding=cast(str, row["payload_encoding"]),
        )
        digest = hashlib.sha256(body).hexdigest()
        name = f"nordic.atlas-nodes.{cast(int, row['sequence']):04d}.{digest[:16]}.js"
        (repository / owner.CHUNKS / name).write_bytes(body)
        row.update(
            path=name,
            sha256=digest,
            integrity="sha256-"
            + base64.b64encode(hashlib.sha256(body).digest()).decode(),
            payload_sha256=payload_sha,
            byte_count=len(body),
            decoded_byte_count=len(text.encode()),
        )
    (repository / owner.ASSETS).write_text(
        json.dumps(
            {**manifest, "schema_version": "atlas-static-bootstrap.v1", "assets": rows}
        )
    )
    with pytest.raises(ValueError, match="feature membership"):
        owner._published_features(repository, projected)
