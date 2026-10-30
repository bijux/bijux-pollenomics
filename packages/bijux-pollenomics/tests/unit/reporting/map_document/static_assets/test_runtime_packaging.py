"""Static documents preserve the full runtime and account for its distribution."""

from __future__ import annotations

import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.reporting.bundles.atlas_bundle.finalization import (
    finalize_bundle,
)
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.map_document import render as subject
from bijux_pollenomics.reporting.map_document.static_assets import (
    write_static_atlas_assets,
)
from bijux_pollenomics.reporting.map_document.static_assets.asset_inventory import (
    normalize_asset_inventory,
)
from bijux_pollenomics.reporting.scope_policy import MAP_SCOPE_POLICIES

from ..browser_semantics.support import check_javascript_syntax, run_node_json


@pytest.fixture
def request_args(tmp_path: Path) -> dict[str, Any]:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="runtime",
        version="runtime-check",
        point_layers=[],
        polygon_layers=[],
    )
    return {
        "title": "Source atlas",
        "version": "runtime-check",
        "generated_on": "Fixed source",
        "countries": (),
        "policy": MAP_SCOPE_POLICIES["custom"],
        "point_layers": [],
        "polygon_layers": [],
        "asset_base_path": "_map_assets",
        "static_assets": assets,
    }


def bootstrap(document: str) -> dict[str, Any]:
    match = re.search(
        r'<script id="atlas-static-bootstrap" type="application/json">(.*?)</script>',
        document,
        re.DOTALL,
    )
    assert match is not None
    return cast(dict[str, Any], json.loads(match.group(1)))


def test_runtime_is_exact_original_iife_and_scientific_inventory_stays_unchanged(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    assets = request_args["static_assets"]
    original = deepcopy(assets.manifest)
    before = subject._compose_map_document(**request_args)
    marked = before.split("<!-- atlas-runtime:begin -->")[1].split(
        "<!-- atlas-runtime:end -->"
    )[0]
    body = re.fullmatch(r"\s*<script>(.*)</script>\s*", marked, re.DOTALL)
    assert body is not None
    html, runtime = subject.write_static_map_document(
        tmp_path / "atlas.html", **request_args
    )
    document = html.read_text()
    raw = runtime.read_bytes()
    assert raw == body.group(1).encode()
    assert b"BijuxPollenomicsAtlasCapture" in raw
    assert "(async () => {" not in document
    assert len(document.encode()) <= 524288 and len(raw) <= 524288
    reference = bootstrap(document).pop("runtime")
    assert bootstrap(document) == {**original, "runtime": reference}
    assert reference == {
        "path": runtime.name,
        "byte_count": len(raw),
        "integrity": "sha256-"
        + base64.b64encode(hashlib.sha256(raw).digest()).decode(),
    }
    assert re.fullmatch(r"atlas\.atlas-runtime\.[a-f0-9]{16}\.js", runtime.name)
    assert (
        assets.manifest == original
        and json.loads(assets.manifest_path.read_bytes()) == original
    )
    assert runtime not in assets.asset_paths
    assert all(
        row["domain"] != "runtime"
        for row in normalize_asset_inventory(original["assets"])
    )
    rows = normalize_asset_inventory(original["assets"])
    assert sum(row["initial_load"] is True for row in rows) + 1 == 4
    assert (
        sum(cast(int, row["byte_count"]) for row in rows if row["initial_load"] is True)
        + len(raw)
        <= 1048576
    )
    check_javascript_syntax(raw.decode(), tmp_path / "checked-runtime.js")


def test_pure_renderer_does_not_materialize_and_keeps_static_size_guard(
    tmp_path: Path, request_args: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    before = set(tmp_path.iterdir())
    subject.render_multi_country_map_html(**{**request_args, "static_assets": None})
    assert set(tmp_path.iterdir()) == before
    monkeypatch.setattr(subject, "_compose_map_document", lambda *a, **k: "x" * 524289)
    with pytest.raises(ValueError, match="document exceeds"):
        subject.render_multi_country_map_html(**request_args)
    assert set(tmp_path.iterdir()) == before


def test_identical_runtime_is_reused_and_changed_existing_bytes_refuse(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    html, runtime = subject.write_static_map_document(
        tmp_path / "atlas.html", **request_args
    )
    stamp, body = runtime.stat().st_mtime_ns, html.read_bytes()
    assert subject.write_static_map_document(html, **request_args) == (html, runtime)
    assert runtime.stat().st_mtime_ns == stamp
    runtime.write_bytes(b"changed runtime")
    with pytest.raises(ValueError, match="collision"):
        subject.write_static_map_document(html, **request_args)
    assert html.read_bytes() == body


@pytest.mark.parametrize(
    "alias",
    ["runtime_symlink", "runtime_hardlink", "html_symlink", "directory_symlink"],
)
def test_distribution_paths_cannot_escape_through_aliases(
    tmp_path: Path, request_args: dict[str, Any], alias: str
) -> None:
    html, runtime = subject.write_static_map_document(
        tmp_path / "atlas.html", **request_args
    )
    if alias.startswith("runtime"):
        target = tmp_path / "original.js"
        runtime.rename(target)
        if alias == "runtime_symlink":
            runtime.symlink_to(target)
        else:
            runtime.hardlink_to(target)
    elif alias == "html_symlink":
        target = tmp_path / "original.html"
        html.rename(target)
        html.symlink_to(target)
    else:
        directory = tmp_path / "linked"
        directory.symlink_to(tmp_path, target_is_directory=True)
        html = directory / "atlas.html"
    with pytest.raises(ValueError, match="physical|immutable"):
        subject.write_static_map_document(html, **request_args)


@pytest.mark.parametrize(
    "limit,value,reason",
    [
        ("ATLAS_DOCUMENT_MAX_BYTES", 1, "runtime exceeds its byte"),
        ("ATLAS_INITIAL_MAX_REQUESTS", 3, "initial request"),
        ("ATLAS_INITIAL_MAX_BYTES", 1, "initial byte"),
        ("ATLAS_STATIC_ASSETS_MAX_FILES", 4, "asset count"),
        ("ATLAS_STATIC_ASSETS_MAX_BYTES", 1, "asset byte"),
        ("ATLAS_BOOTSTRAP_MAX_BYTES", 1, "bootstrap exceeds"),
    ],
)
def test_runtime_is_included_in_existing_resource_limits_before_any_write(
    tmp_path: Path,
    request_args: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    limit: str,
    value: int,
    reason: str,
) -> None:
    before = set(tmp_path.iterdir())
    monkeypatch.setattr(subject, limit, value)
    with pytest.raises(ValueError, match=reason):
        subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize("defect", ["missing", "duplicate", "malformed", "bootstrap"])
def test_incomplete_runtime_or_changed_scientific_bootstrap_refuses_before_publication(
    tmp_path: Path,
    request_args: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    defect: str,
) -> None:
    document = subject._compose_map_document(**request_args)
    if defect == "missing":
        document = document.replace("<!-- atlas-runtime:begin -->", "")
    elif defect == "duplicate":
        document += "<!-- atlas-runtime:begin -->"
    elif defect == "malformed":
        document = document.replace(
            "<!-- atlas-runtime:begin -->", "<!-- atlas-runtime:begin -->invalid"
        )
    else:
        document = document.replace('"runtime-check"', '"changed-version"', 1)
    monkeypatch.setattr(subject, "_compose_map_document", lambda *a, **k: document)
    before = set(tmp_path.iterdir())
    with pytest.raises(ValueError):
        subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    assert set(tmp_path.iterdir()) == before


@pytest.mark.parametrize("protocol", ["http:", "https:", "file:", "data:"])
def test_actual_html_loader_uses_protocol_aware_integrity_and_accessible_failure(
    tmp_path: Path, request_args: dict[str, Any], protocol: str
) -> None:
    html, _ = subject.write_static_map_document(tmp_path / "atlas.html", **request_args)
    document = html.read_text()
    scripts = [
        body
        for attributes, body in re.findall(
            r"<script([^>]*)>(.*?)</script>", document, re.DOTALL
        )
        if not attributes.strip() and body.strip()
    ]
    assert len(scripts) == 1
    output = run_node_json(
        "const appended=[],alerts=[];const runtime="
        + json.dumps(bootstrap(document))
        + ";const location={protocol:"
        + json.dumps(protocol)
        + """};
const document={getElementById(){return {textContent:JSON.stringify(runtime)};},
createElement(tag){return {tag,setAttribute(key,value){this[key]=value;}};},
body:{append(script){appended.push(script);},prepend(alert){alerts.push(alert);}}};
"""
        + scripts[0]
        + "if(appended.length)appended[0].onerror();console.log(JSON.stringify({appended,alerts}));"
    )
    if protocol == "data:":
        assert output["appended"] == []
    else:
        script = output["appended"][0]
        assert script["src"] == bootstrap(document)["runtime"]["path"]
        assert script["async"] is False
        if protocol == "file:":
            assert "integrity" not in script and "crossOrigin" not in script
        else:
            assert script["integrity"] == bootstrap(document)["runtime"]["integrity"]
            assert script["crossOrigin"] == "anonymous"
    assert len(output["alerts"]) == 1
    assert output["alerts"][0]["role"] == "alert"
    assert output["alerts"][0]["aria-live"] == "assertive"


def test_atlas_bundle_inventories_runtime_before_manifest_and_summary(
    tmp_path: Path, request_args: dict[str, Any]
) -> None:
    paths = build_atlas_bundle_paths(tmp_path, "runtime", "runtime-check")
    checked = []

    def inventory(*args: Any, **kwargs: Any) -> dict[str, object]:
        artifacts = args[2]
        name = next(
            name for label, name in artifacts if label == "Static atlas runtime"
        )
        assert (tmp_path / name).is_file() and paths.map_html_path.is_file()
        checked.append(name)
        return {"runtime": name}

    def write(path: Path, value: Any) -> None:
        path.write_text(json.dumps(value))

    finalize_bundle(
        staging_output_dir=tmp_path,
        report=None,
        title=request_args["title"],
        version=request_args["version"],
        generated_on=request_args["generated_on"],
        countries=(),
        country_sample_counts={},
        asset_base_path="_map_assets",
        bundle_paths=paths,
        point_layers=[],
        polygon_layers=[],
        extra_artifacts=[],
        map_policy=request_args["policy"],
        map_publication_contract={},
        animal_atlas_summary={},
        static_assets=request_args["static_assets"],
        build_multi_country_map_summary_fn=inventory,
        copy_map_assets_fn=lambda _: None,
        write_static_map_document_fn=subject.write_static_map_document,
        render_multi_country_map_markdown_fn=lambda **_: "Atlas files are complete.",
        write_summary_json_fn=write,
        surface=SimpleNamespace(build_multi_country_bundle_manifest=inventory),
    )
    assert len(checked) == 2 and checked[0] == checked[1]
