"""Compose Atlas documents and write bounded static runtime resources."""

from __future__ import annotations

import base64
import hashlib
from html.parser import HTMLParser
from importlib.resources import files
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
_EVIDENCE_BEGIN = "/* atlas-evidence-tools:begin */"
_EVIDENCE_END = "/* atlas-evidence-tools:end */"
_EVIDENCE_FACTORY = """globalThis.BijuxPollenomicsEvidenceTools=function(escapeHtml,scientificCueGlyph){
%s
return Object.freeze({countryData:relationSummaryData,countryHtml:renderRelationSummary,timeData:relationTimeSummaryData,timeHtml:renderRelationTimeSummary,pickerCatalog:scientificPickerCatalog,pickerSearch:scientificPickerSearch,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker,sourceDetails:createSourceRecordDetails,selectionExport:prepareAtlasSelectionExport});
};
"""
_BOOTSTRAP = re.compile(
    r'(<script id="atlas-static-bootstrap" type="application/json">)(.*?)(</script>)',
    re.DOTALL,
)
_NATIVE_BINDING = re.compile(
    r'<script id="atlas-native-lra-binding" type="application/json">(.*?)</script>',
    re.DOTALL,
)
_MODELED_BINDING = re.compile(
    r'<script id="atlas-modeled-context-binding" type="application/json">(.*?)</script>',
    re.DOTALL,
)
_OPTIONAL_CONTROLLERS = {
    "evidence_tools": "atlas-evidence-tools",
    "index_transport": "atlas-index-transport",
}
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


class _FixedJsonBindings(HTMLParser):
    """Read the two document-owned JSON nodes without treating tag order as identity."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.bindings: dict[str, list[list[str] | None]] = {
            "atlas-native-lra-binding": [],
            "atlas-modeled-context-binding": [],
        }
        self.active: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        identities = [value for key, value in attrs if key == "id"]
        for identity in identities:
            if identity is None or identity not in self.bindings:
                continue
            value: list[str] | None = (
                []
                if tag == "script"
                and len(identities) == 1
                and [value for key, value in attrs if key == "type"]
                == ["application/json"]
                else None
            )
            self.bindings[identity].append(value)
            if value is not None:
                self.active = value

    def handle_data(self, data: str) -> None:
        if self.active is not None:
            self.active.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "script":
            self.active = None


def _runtime_resources(
    assets: StaticAtlasAssets,
    runtime_bytes: int,
    document: str,
    optional_bytes: int | tuple[int, ...] = 0,
) -> None:
    """Charge executable transport and the actual inline binding to both budgets."""
    parser = _FixedJsonBindings()
    parser.feed(document)
    parser.close()
    inline_bytes = 0
    for bindings in parser.bindings.values():
        if len(bindings) != 1 or bindings[0] is None:
            raise ValueError(
                "static map document requires one of each fixed JSON binding"
            )
        body = "".join(bindings[0])
        json.loads(body)
        inline_bytes += len(body.encode("utf-8"))
    if not 0 < runtime_bytes <= ATLAS_DOCUMENT_MAX_BYTES:
        raise ValueError("static atlas runtime exceeds its byte budget")
    controllers = (
        (() if optional_bytes == 0 else (optional_bytes,))
        if type(optional_bytes) is int
        else optional_bytes
    )
    if (
        type(controllers) is not tuple
        or len(controllers) > len(_OPTIONAL_CONTROLLERS)
        or any(
            type(size) is not int or not 0 < size <= ATLAS_DOCUMENT_MAX_BYTES
            for size in controllers
        )
    ):
        raise ValueError("static atlas optional controller exceeds its byte budget")
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
    if len(rows) + 1 + len(controllers) > ATLAS_STATIC_ASSETS_MAX_FILES:
        raise ValueError("static atlas runtime exceeds total asset count budget")
    if (
        sum(counts) + runtime_bytes + inline_bytes + sum(controllers)
        > ATLAS_STATIC_ASSETS_MAX_BYTES
    ):
        raise ValueError("static atlas runtime exceeds total asset byte budget")


def _separate_evidence_tools(body: str) -> tuple[bytes, bytes]:
    """Move only the complete marked helper block into its explicit factory."""
    if body.count(_EVIDENCE_BEGIN) != 1 or body.count(_EVIDENCE_END) != 1:
        raise ValueError("static map requires one evidence tools boundary")
    matches = [
        re.search(r"(?m)^[ \t]*" + re.escape(marker) + r"[ \t]*$", body)
        for marker in (_EVIDENCE_BEGIN, _EVIDENCE_END)
    ]
    begin, end = matches
    opening = re.match(r"\s*\(async \(\) => \{", body)
    closing = re.search(r"(?m)^[ \t]*\}\)\(\)\.catch\(", body)
    if (
        begin is None
        or end is None
        or opening is None
        or closing is None
        or not opening.end() <= begin.start() < end.start() < closing.start()
    ):
        raise ValueError("static map evidence tools boundary is unsafe")
    helpers = body[begin.end() : end.start()]
    if not helpers.strip():
        raise ValueError("static map evidence tools block is empty")
    return (
        (body[: begin.start()] + body[end.end() :]).encode("utf-8"),
        (_EVIDENCE_FACTORY % helpers).encode("utf-8"),
    )


def _code_reference(
    parent: Path, stem: str, kind: str, body: bytes
) -> tuple[Path, dict[str, object]]:
    digest = hashlib.sha256(body).digest()
    path = parent / f"{stem}.{kind}.{digest.hex()[:16]}.js"
    return path, {
        "path": path.name,
        "byte_count": len(body),
        "integrity": "sha256-" + base64.b64encode(digest).decode("ascii"),
    }


def _check_code_target(path: Path, payload: bytes) -> None:
    if path.is_symlink() or (
        path.exists() and (not path.is_file() or path.stat().st_nlink != 1)
    ):
        raise ValueError("static map code must be an unaliased immutable file")
    if path.exists() and path.read_bytes() != payload:
        raise ValueError(f"static atlas asset collision: {path.name}")


def static_map_optional_controller_paths(document_path: Path) -> tuple[Path, ...]:
    """Read the exact distributed code reference for bundle inventory closure."""
    document_path = document_path.absolute()
    if (
        document_path.resolve(strict=True) != document_path
        or not document_path.is_file()
        or document_path.stat().st_nlink != 1
    ):
        raise ValueError("static map inventory requires a physical document")
    bootstraps = list(_BOOTSTRAP.finditer(document_path.read_text(encoding="utf-8")))
    if len(bootstraps) != 1:
        raise ValueError("static map inventory requires one bootstrap")
    bootstrap = json.loads(bootstraps[0].group(2))
    if not isinstance(bootstrap, dict) or not isinstance(
        bootstrap.get("runtime", {}), dict
    ):
        raise ValueError("static map runtime identity is invalid")
    runtime = bootstrap.get("runtime", {})
    if "optional_controllers" not in runtime:
        return ()
    optional = runtime["optional_controllers"]
    if not isinstance(optional, dict) or set(optional) not in (
        {"evidence_tools"},
        set(_OPTIONAL_CONTROLLERS),
    ):
        raise ValueError("static map optional controller identity is invalid")
    result = []
    for key, kind in _OPTIONAL_CONTROLLERS.items():
        if key not in optional:
            continue
        reference = optional[key]
        if not isinstance(reference, dict) or not isinstance(
            reference.get("path"), str
        ):
            raise ValueError("static map optional controller identity is invalid")
        name = reference["path"]
        if not re.fullmatch(
            re.escape(document_path.stem)
            + r"\."
            + re.escape(kind)
            + r"\.[a-f0-9]{16}\.js",
            name,
        ):
            raise ValueError("static map optional controller path is invalid")
        path = document_path.parent / name
        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:
            raise ValueError("static map optional controller must be an unaliased file")
        payload = path.read_bytes()
        _, actual = _code_reference(path.parent, document_path.stem, kind, payload)
        if (
            reference != actual
            or not 0 < len(payload) <= ATLAS_DOCUMENT_MAX_BYTES
            or path in result
        ):
            raise ValueError("static map optional controller bytes differ")
        result.append(path)
    return tuple(result)


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
    """Write bounded HTML, main IIFE and lazily requested evidence tools.

    Runtime identity belongs to the distributed document, outside scientific
    chunk identities. HTTP(S) uses SRI; file transport has no pre-execution SRI,
    matching the existing offline policy. The return remains HTML/main runtime;
    bundle inventories must also include the declared optional controller path.
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
    body, evidence_body = _separate_evidence_tools(match.group(1))
    index_body = files(__package__).joinpath("assets/index-transport.js").read_bytes()
    _runtime_resources(
        static_assets, len(body), document, (len(evidence_body), len(index_body))
    )
    runtime, reference = _code_reference(parent, output.stem, "atlas-runtime", body)
    evidence, evidence_reference = _code_reference(
        parent, output.stem, "atlas-evidence-tools", evidence_body
    )
    indexes, index_reference = _code_reference(
        parent, output.stem, "atlas-index-transport", index_body
    )
    reference["optional_controllers"] = {
        "evidence_tools": evidence_reference,
        "index_transport": index_reference,
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
    _check_code_target(runtime, body)
    _check_code_target(evidence, evidence_body)
    _check_code_target(indexes, index_body)
    write_immutable(runtime, body)
    write_immutable(evidence, evidence_body)
    write_immutable(indexes, index_body)
    output.write_text(document, encoding="utf-8")
    return output, runtime
