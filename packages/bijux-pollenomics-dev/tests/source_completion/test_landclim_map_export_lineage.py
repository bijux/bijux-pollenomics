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
from bijux_pollenomics_dev.ci.atlas_browser.landclim_export import (
    reconcile as browser_export,
)
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
    assert len(paths) == 3
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
    page = (
        '<script id="atlas-static-bootstrap" type="application/json">'
        + json.dumps(bootstrap)
        + '</script><script id="atlas-modeled-context-binding" type="application/json">'
        + json.dumps(
            owner._map_manifest((ROOT / owner.MAP).read_text(), script=body.decode())
        )
        + "</script>"
        + '<script id="atlas-native-lra-binding" type="application/json">null</script>'
        + _RUNTIME_LOADER
    )
    (repository / owner.MAP).write_text(page)
    return page


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


@pytest.mark.parametrize(
    "name,next_name,guard,replacement",
    [
        (
            "modeledContextFrameFeatures",
            "modeledContextFrameGeoJson",
            "if (!modeledContextActive || !sourceWindow) return [];",
            "",
        ),
        (
            "modeledContextFrameFeatures",
            "modeledContextFrameGeoJson",
            "polygonGeometryIsAdmitted(feature)",
            "true",
        ),
        (
            "modeledContextFrameFeatures",
            "modeledContextFrameGeoJson",
            "&& polygonFeatureVisible(layer, properties)",
            "",
        ),
        (
            "polygonFeatureVisible",
            "geoJsonPositionIsAdmitted",
            "activeLayerKeys.has(layer.key)",
            "true",
        ),
        (
            "polygonFeatureVisible",
            "geoJsonPositionIsAdmitted",
            "&& (!layer.applies_country_filter || activeCountries.has(country))",
            "",
        ),
        (
            "polygonFeatureVisible",
            "geoJsonPositionIsAdmitted",
            "&& featureInTimeWindow(layer, properties)",
            "",
        ),
        (
            "polygonFeatureVisible",
            "geoJsonPositionIsAdmitted",
            "&& modeledContextFeatureVisible(layer, properties)",
            "",
        ),
        (
            "isModeledContextFeature",
            "modeledContextFeatureVisible",
            "&& String(properties.dataset_id || '') === String(MODELED_CONTEXT.dataset_id || '')",
            "",
        ),
        (
            "modeledContextFeatureVisible",
            "modeledContextNumber",
            "properties.time_label === window.label",
            "true",
        ),
        (
            "modeledContextFrameGeoJson",
            "modeledContextFrameQualitySummary",
            "const sourceFeatures = modeledContextFrameFeatures();",
            "const sourceFeatures = [];",
        ),
        (
            "modeledContextFrameGeoJson",
            "modeledContextFrameQualitySummary",
            "reconstruction_values: Object.fromEntries(Object.keys(feature.properties.reconstruction_values || {}).map((key) => [key, null]))",
            "reconstruction_values: feature.properties.reconstruction_values",
        ),
        (
            "modeledContextFrameGeoJson",
            "modeledContextFrameQualitySummary",
            "standard_errors: Object.fromEntries(Object.keys(feature.properties.standard_errors || {}).map((key) => [key, null]))",
            "standard_errors: feature.properties.standard_errors",
        ),
        (
            "modeledContextFrameGeoJson",
            "modeledContextFrameQualitySummary",
            "propagation_use_allowed: false",
            "propagation_use_allowed: true",
        ),
    ],
)
def test_removed_selector_guard_cannot_be_replaced_by_an_unrelated_decoy(
    runtime: bytes, name: str, next_name: str, guard: str, replacement: str
) -> None:
    script = runtime.decode()
    start = script.index(f"function {name}(")
    end = script.index(f"function {next_name}(", start)
    actual = script[start:end]
    assert actual.count(guard) == 1
    changed = (
        script[:start]
        + actual.replace(guard, replacement, 1)
        + script[end:]
        + "\n/* Unrelated retained text: "
        + guard
        + " */\n"
    )
    assert guard in changed
    with pytest.raises(ValueError, match="selector or identity"):
        owner._export_contract(changed)


def test_download_listener_must_be_in_the_actual_control_binding_section(
    runtime: bytes,
) -> None:
    listener = (
        "modeledContextDownload.addEventListener('click', downloadModeledContextFrame)"
    )
    script = runtime.decode()
    assert script.count(listener) == 1
    changed = script.replace(listener, "modeledContextDownload.disabled = true", 1)
    changed += "\n/* " + listener + " */\n"
    with pytest.raises(ValueError, match="selector or identity"):
        owner._export_contract(changed)


def test_ambiguous_published_selector_definitions_are_refused(runtime: bytes) -> None:
    changed = (
        runtime.decode() + "\nfunction polygonFeatureVisible(layer, properties) {}"
    )
    with pytest.raises(ValueError, match="selector or identity"):
        owner._export_contract(changed)


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


def test_browser_export_reads_authenticated_current_and_legacy_metadata(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], runtime: bytes
) -> None:
    repository, manifest, _ = published
    page = page_for(repository, manifest, runtime)
    expected = owner._map_manifest(page, script=runtime.decode())
    assert browser_export._modeled_manifest(repository, page) == expected
    legacy = 'const MODELED_CONTEXT = {"legacy":true};'
    (repository / owner.MAP).write_text(legacy)
    assert browser_export._modeled_manifest(repository, legacy) == {"legacy": True}


def test_browser_export_refuses_runtime_tamper_before_reading_metadata(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], runtime: bytes
) -> None:
    repository, manifest, _ = published
    page = page_for(repository, manifest, runtime)
    digest = hashlib.sha256(runtime).hexdigest()
    (
        repository / owner.CHUNKS / f"nordic_map.atlas-runtime.{digest[:16]}.js"
    ).write_bytes(runtime + b" ")
    with pytest.raises(ValueError, match="Published runtime graph differs"):
        browser_export._modeled_manifest(repository, page)


def test_browser_export_refuses_missing_actual_model_binding_declaration(
    published: tuple[Path, dict[str, Any], list[dict[str, Any]]], runtime: bytes
) -> None:
    repository, manifest, _ = published
    changed = runtime.replace(
        b"const MODELED_CONTEXT = JSON.parse(document.getElementById('atlas-modeled-context-binding').textContent);",
        b"const MODELED_CONTEXT = {};",
    )
    assert changed != runtime
    page = page_for(repository, manifest, runtime)
    original_digest = hashlib.sha256(runtime).hexdigest()
    changed_digest = hashlib.sha256(changed).hexdigest()
    original_name = f"nordic_map.atlas-runtime.{original_digest[:16]}.js"
    changed_name = f"nordic_map.atlas-runtime.{changed_digest[:16]}.js"
    (repository / owner.CHUNKS / changed_name).write_bytes(changed)
    original_sri = (
        "sha256-" + base64.b64encode(hashlib.sha256(runtime).digest()).decode()
    )
    changed_sri = (
        "sha256-" + base64.b64encode(hashlib.sha256(changed).digest()).decode()
    )
    page = page.replace(original_name, changed_name).replace(original_sri, changed_sri)
    page = page.replace(
        f'"byte_count": {len(runtime)}', f'"byte_count": {len(changed)}'
    )
    (repository / owner.MAP).write_text(page)
    with pytest.raises(ValueError, match="modeled-context binding unavailable"):
        browser_export._modeled_manifest(repository, page)


def test_capture_identity_binds_actual_runtime_graph_and_preserves_browser_fields() -> (
    None
):
    import subprocess

    capture = (
        ROOT
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/atlas_browser/landclim_export/capture.mjs"
    ).read_text()
    functions = capture.split("function captureBrowserIdentity", 1)[1].split(
        "let cdp, runtime, captureError;", 1
    )[0]
    script = (
        "import {readFile} from 'node:fs/promises';\n"
        "import {execFileSync} from 'node:child_process';\n"
        "import {createHash} from 'node:crypto';\n"
        "import {basename,dirname,join} from 'node:path';\n"
        "function captureBrowserIdentity"
        + functions
        + "\nconst repository="
        + json.dumps(str(ROOT))
        + r""";
const page=await readFile(join(repository,'docs/report/regions/nordic/nordic_map.html'),'utf8');
const bootstrap=JSON.parse(page.match(/<script id="atlas-static-bootstrap" type="application\/json">([\s\S]*?)<\/script>/)[1]);
const version={product:'SyntheticChrome/1',revision:'test-revision',userAgent:'test-agent',jsVersion:'test-js',protocolVersion:'1.3'};
const refused=[];
for(const key of Object.keys(version)){
 try{captureBrowserIdentity({...version,[key]:''});}catch{refused.push(key);}
}
console.log(JSON.stringify({browser_runtime:captureBrowserIdentity(version),
 candidate:await captureSourceIdentity(repository,bootstrap.runtime),refused}));
"""
    )
    completed = subprocess.run(
        ("node", "--input-type=module", "--eval", script),
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 0, completed.stderr
    observation = json.loads(completed.stdout)
    assert observation.pop("refused") == [
        "product",
        "revision",
        "userAgent",
        "jsVersion",
        "protocolVersion",
    ]
    browser = ROOT / "artifacts/synthetic-browser"
    observation["browser_binary"] = str(browser)
    assert (
        browser_export._capture_identity(ROOT, observation, browser)
        == observation["candidate"]
    )
    for key in ("head", "tree", "files"):
        changed = deepcopy(observation)
        changed["candidate"][key] = [] if key == "files" else "0" * 40
        with pytest.raises(ValueError, match="candidate identity differs"):
            browser_export._capture_identity(ROOT, changed, browser)
    for key in ("bytes", "sha256"):
        changed = deepcopy(observation)
        changed["candidate"]["files"][0][key] = 0 if key == "bytes" else "0" * 64
        with pytest.raises(ValueError, match="candidate identity differs"):
            browser_export._capture_identity(ROOT, changed, browser)
    for key in observation["browser_runtime"]:
        changed = deepcopy(observation)
        changed["browser_runtime"][key] = ""
        with pytest.raises(ValueError, match="browser identity unavailable"):
            browser_export._capture_identity(ROOT, changed, browser)
    with pytest.raises(ValueError, match="browser binary differs"):
        browser_export._capture_identity(
            ROOT, observation, ROOT / "artifacts/other-browser"
        )
