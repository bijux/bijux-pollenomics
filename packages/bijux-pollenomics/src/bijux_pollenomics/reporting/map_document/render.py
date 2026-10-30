"""Compose Atlas documents and write bounded static runtime resources."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from ...core.geospatial.geojson import JsonObject
from ..map_publication import MapScopePolicy
from ..presentation.text import escape_html
from .payload import build_map_document_payload, serialize_json_for_script
from .static_assets import StaticAtlasAssets, validate_static_atlas_document
from .static_assets.asset_inventory import normalize_asset_inventory
from .static_assets.budgets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from .static_assets.serialization import write_immutable
from .static_assets.stylesheet import compact_stylesheet
from .template import MAP_DOCUMENT_TEMPLATE


def _compact_inline_stylesheet(document: str) -> str:
    """Save document bytes without changing CSS tokens or source readability."""
    start = document.index("<style>") + len("<style>")
    end = document.index("</style>", start)
    stylesheet = document[start:end]
    compact = compact_stylesheet(stylesheet)
    return document[:start] + compact + document[end:]


def _compose_map_document(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    static_assets: StaticAtlasAssets | None = None,
    *,
    native_lra: dict[str, Any] | None = None,
) -> str:
    """Compose source and payload without publishing an intermediate document."""
    rendered_document = (
        _compact_inline_stylesheet(MAP_DOCUMENT_TEMPLATE)
        if static_assets is not None
        else MAP_DOCUMENT_TEMPLATE
    )
    for placeholder, value in build_map_document_payload(
        title=title,
        version=version,
        generated_on=generated_on,
        countries=countries,
        policy=policy,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
        asset_base_path=asset_base_path,
        escape_html_fn=escape_html,
        static_assets=static_assets,
        native_lra=native_lra,
    ).items():
        rendered_document = rendered_document.replace(placeholder, value)
    return rendered_document


def render_multi_country_map_html(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    static_assets: StaticAtlasAssets | None = None,
    *,
    native_lra: dict[str, Any] | None = None,
) -> str:
    """Return inline HTML without writing files; enforce the static document cap."""
    document = _compose_map_document(
        title,
        version,
        generated_on,
        countries,
        policy,
        point_layers,
        polygon_layers,
        asset_base_path,
        static_assets,
        native_lra=native_lra,
    )
    if static_assets is not None:
        validate_static_atlas_document(document)
    return document


_RUNTIME_BEGIN = "<!-- atlas-runtime:begin -->"
_RUNTIME_END = "<!-- atlas-runtime:end -->"
_BOOTSTRAP = re.compile(
    r'(<script id="atlas-static-bootstrap" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)
_NATIVE_BINDING = re.compile(
    r'<script id="atlas-native-lra-binding" type="application/json">(.*?)</script>',
    re.DOTALL,
)
_RUNTIME_LOADER = """<script>
(() => {
  const fail = () => {
    const alert = document.createElement('main');
    alert.setAttribute('role', 'alert');
    alert.setAttribute('aria-live', 'assertive');
    alert.textContent = 'Atlas runtime could not be loaded. Keep the complete atlas files together and reload.';
    document.body.prepend(alert);
  };
  try {
    const runtime = JSON.parse(document.getElementById('atlas-static-bootstrap').textContent).runtime;
    const script = document.createElement('script');
    script.src = runtime.path;
    script.async = false;
    if (location.protocol === 'http:' || location.protocol === 'https:') {
      script.integrity = runtime.integrity;
      script.crossOrigin = 'anonymous';
    } else if (location.protocol !== 'file:') { throw new Error('Unsupported atlas protocol'); }
    script.onerror = fail;
    document.body.append(script);
  } catch (error) { fail(); }
})();
</script>"""


def _runtime_resources(
    assets: StaticAtlasAssets, runtime_bytes: int, document: str
) -> None:
    """Charge executable transport and the actual inline binding to both budgets."""
    bindings = _NATIVE_BINDING.findall(document)
    if len(bindings) != 1:
        raise ValueError("static map document requires one native binding payload")
    json.loads(bindings[0])
    inline_bytes = len(bindings[0].encode("utf-8"))
    if not 0 < runtime_bytes <= ATLAS_DOCUMENT_MAX_BYTES:
        raise ValueError("static atlas runtime exceeds its byte budget")
    rows = normalize_asset_inventory(assets.manifest["assets"])
    counts: list[int] = []
    initial: list[int] = []
    for row in rows:
        count = row.get("byte_count")
        if type(count) is not int or count < 0:
            raise ValueError("static atlas asset byte count is invalid")
        counts.append(count)
        if row.get("initial_load") is True:
            initial.append(count)
    if len(initial) + 1 > ATLAS_INITIAL_MAX_REQUESTS:
        raise ValueError("static atlas runtime exceeds initial request budget")
    if sum(initial) + runtime_bytes + inline_bytes > ATLAS_INITIAL_MAX_BYTES:
        raise ValueError("static atlas runtime exceeds initial byte budget")
    if len(rows) + 1 > ATLAS_STATIC_ASSETS_MAX_FILES:
        raise ValueError("static atlas runtime exceeds total asset count budget")
    if sum(counts) + runtime_bytes + inline_bytes > ATLAS_STATIC_ASSETS_MAX_BYTES:
        raise ValueError("static atlas runtime exceeds total asset byte budget")


def write_static_map_document(
    output_path: Path,
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    policy: MapScopePolicy,
    point_layers: list[JsonObject],
    polygon_layers: list[JsonObject],
    asset_base_path: str,
    static_assets: StaticAtlasAssets,
    *,
    native_lra: dict[str, Any] | None = None,
) -> tuple[Path, Path]:
    """Write bounded HTML and its unchanged main IIFE as one immutable sidecar.

    Runtime identity belongs to the distributed document, outside scientific
    chunk identities. HTTP(S) uses SRI; file transport has no pre-execution SRI,
    matching the existing offline policy. Callers must inventory both paths.
    """
    output = output_path.absolute()
    parent = output.parent
    if (
        not parent.is_dir()
        or parent.resolve(strict=True) != parent
        or static_assets.manifest_path.parent.absolute() != parent
        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", output.stem)
        or output.is_symlink()
        or (output.exists() and (not output.is_file() or output.stat().st_nlink != 1))
    ):
        raise ValueError("static map document requires its physical asset directory")
    document = _compose_map_document(
        title,
        version,
        generated_on,
        countries,
        policy,
        point_layers,
        polygon_layers,
        asset_base_path,
        static_assets,
        native_lra=native_lra,
    )
    if document.count(_RUNTIME_BEGIN) != 1 or document.count(_RUNTIME_END) != 1:
        raise ValueError("static map document requires one runtime boundary")
    before, tail = document.split(_RUNTIME_BEGIN)
    marked, after = tail.split(_RUNTIME_END)
    match = re.fullmatch(r"\s*<script>(.*)</script>\s*", marked, re.DOTALL)
    if match is None:
        raise ValueError("static map runtime boundary is invalid")
    body = match.group(1).encode("utf-8")
    _runtime_resources(static_assets, len(body), document)
    digest = hashlib.sha256(body).digest()
    runtime = parent / f"{output.stem}.atlas-runtime.{digest.hex()[:16]}.js"
    reference = {
        "path": runtime.name,
        "byte_count": len(body),
        "integrity": "sha256-" + base64.b64encode(digest).decode("ascii"),
    }
    document = before + _RUNTIME_LOADER + after
    bootstraps = list(_BOOTSTRAP.finditer(document))
    if (
        len(bootstraps) != 1
        or json.loads(bootstraps[0].group(2)) != static_assets.manifest
    ):
        raise ValueError("static map bootstrap differs from its scientific assets")
    bootstrap = bootstraps[0]
    encoded = serialize_json_for_script(
        {**static_assets.manifest, "runtime": reference}
    )
    if len(encoded.encode("utf-8")) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas runtime bootstrap exceeds its byte budget")
    document = document[: bootstrap.start(2)] + encoded + document[bootstrap.end(2) :]
    validate_static_atlas_document(document)
    if runtime.is_symlink() or (runtime.exists() and runtime.stat().st_nlink != 1):
        raise ValueError("static map runtime must be an unaliased immutable file")
    write_immutable(runtime, body)
    output.write_text(document, encoding="utf-8")
    return output, runtime
