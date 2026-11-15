"""Reconstruct the complete original renderer through fixed transport source spans."""

from __future__ import annotations

from hashlib import sha256

_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py"
)
_ORIGINAL_SHA256 = "5d4e6e72c8794e40d6a741d40a74d7c0e3dbe6de9791e0c555f3043da5bf0def"
_TRANSPORT_SHA256 = "90f8eb23ef08df8664cea3d0a5cff577b99a4c79d947e367f1ab9b27145baf65"
_TRANSPORT_SPANS: tuple[tuple[bytes, bytes], ...] = (
    (
        (b"from __future__ import annotations\n\nfrom typing import Any\n"),
        (
            b'"""Compose Atlas documents and write bounded static runtime resources."""\n'
            b"\n"
            b"from __future__ import annotations\n"
            b"\n"
            b"import base64\n"
            b"import hashlib\n"
            b"from html.parser import HTMLParser\n"
            b"from importlib.resources import files\n"
            b"import json\n"
            b"from pathlib import Path\n"
            b"import re\n"
            b"from typing import Any\n"
        ),
    ),
    (
        (
            b"from ..presentation.text import escape_html\n"
            b"from .payload import build_map_document_payload\n"
            b"from .static_assets import StaticAtlasAssets, validate_static_atlas_document\n"
            b"from .static_assets.stylesheet import compact_stylesheet\n"
        ),
        (
            b"from ..presentation.text import escape_html\n"
            b"from .payload import build_map_document_payload, serialize_json_for_script\n"
            b"from .static_assets import StaticAtlasAssets, validate_static_atlas_document\n"
            b"from .static_assets.asset_inventory import normalize_asset_inventory\n"
            b"from .static_assets.budgets import (\n"
            b"    ATLAS_BOOTSTRAP_MAX_BYTES,\n"
            b"    ATLAS_DOCUMENT_MAX_BYTES,\n"
            b"    ATLAS_INITIAL_MAX_BYTES,\n"
            b"    ATLAS_INITIAL_MAX_REQUESTS,\n"
            b"    ATLAS_STATIC_ASSETS_MAX_BYTES,\n"
            b"    ATLAS_STATIC_ASSETS_MAX_FILES,\n"
            b")\n"
            b"from .static_assets.serialization import write_immutable\n"
            b"from .static_assets.stylesheet import compact_stylesheet\n"
        ),
    ),
    (
        (b"\ndef render_multi_country_map_html(\n    title: str,\n"),
        (b"\ndef _compose_map_document(\n    title: str,\n"),
    ),
    (
        (
            b") -> str:\n"
            b'    """Render the standalone interactive map document."""\n'
            b"    rendered_document = (\n"
        ),
        (
            b") -> str:\n"
            b'    """Compose source and payload without publishing an intermediate document."""\n'
            b"    rendered_document = (\n"
        ),
    ),
    (
        (
            b"        rendered_document = rendered_document.replace(placeholder, value)\n"
            b"    if static_assets is not None:\n"
            b"        validate_static_atlas_document(rendered_document)\n"
            b"    return rendered_document\n"
        ),
        (
            b"        rendered_document = rendered_document.replace(placeholder, value)\n"
            b"    return rendered_document\n"
            b"\n"
            b"\n"
            b"def render_multi_country_map_html(\n"
            b"    title: str,\n"
            b"    version: str,\n"
            b"    generated_on: str,\n"
            b"    countries: tuple[str, ...],\n"
            b"    policy: MapScopePolicy,\n"
            b"    point_layers: list[JsonObject],\n"
            b"    polygon_layers: list[JsonObject],\n"
            b"    asset_base_path: str,\n"
            b"    static_assets: StaticAtlasAssets | None = None,\n"
            b"    *,\n"
            b"    native_lra: dict[str, Any] | None = None,\n"
            b") -> str:\n"
            b'    """Return inline HTML without writing files; enforce the static document cap."""\n'
            b"    document = _compose_map_document(\n"
            b"        title,\n"
            b"        version,\n"
            b"        generated_on,\n"
            b"        countries,\n"
            b"        policy,\n"
            b"        point_layers,\n"
            b"        polygon_layers,\n"
            b"        asset_base_path,\n"
            b"        static_assets,\n"
            b"        native_lra=native_lra,\n"
            b"    )\n"
            b"    if static_assets is not None:\n"
            b"        validate_static_atlas_document(document)\n"
            b"    return document\n"
            b"\n"
            b"\n"
            b'_RUNTIME_BEGIN = "<!-- atlas-runtime:begin -->"\n'
            b'_RUNTIME_END = "<!-- atlas-runtime:end -->"\n'
            b'_EVIDENCE_BEGIN = "/* atlas-evidence-tools:begin */"\n'
            b'_EVIDENCE_END = "/* atlas-evidence-tools:end */"\n'
            b'_EVIDENCE_FACTORY = """globalThis.BijuxPollenomicsEvidenceTools=function(escapeHtml,scientificCueGlyph){\n'
            b"%s\n"
            b"return Object.freeze({countryData:relationSummaryData,countryHtml:renderRelationSummary,timeData:relationTimeSummaryData,timeHtml:renderRelationTimeSummary,pickerCatalog:scientificPickerCatalog,pickerSearch:scientificPickerSearch,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker,sourceDetails:createSourceRecordDetails,sourceExport:createSourceRecordExport,selectionExport:prepareAtlasSelectionExport});\n"
            b"};\n"
            b'"""\n'
            b"_BOOTSTRAP = re.compile(\n"
            b'    r\'(<script id="atlas-static-bootstrap" type="application/json">)(.*?)(</script>)\',\n'
            b"    re.DOTALL,\n"
            b")\n"
            b"_NATIVE_BINDING = re.compile(\n"
            b'    r\'<script id="atlas-native-lra-binding" type="application/json">(.*?)</script>\',\n'
            b"    re.DOTALL,\n"
            b")\n"
            b"_MODELED_BINDING = re.compile(\n"
            b'    r\'<script id="atlas-modeled-context-binding" type="application/json">(.*?)</script>\',\n'
            b"    re.DOTALL,\n"
            b")\n"
            b"_OPTIONAL_CONTROLLERS = {\n"
            b'    "evidence_tools": "atlas-evidence-tools",\n'
            b'    "index_transport": "atlas-index-transport",\n'
            b"}\n"
            b'_RUNTIME_LOADER = """<script>\n'
            b"(() => {\n"
            b"  const fail = () => {\n"
            b"    const alert = document.createElement('main');\n"
            b"    alert.setAttribute('role', 'alert');\n"
            b"    alert.setAttribute('aria-live', 'assertive');\n"
            b"    alert.textContent = 'Atlas runtime could not be loaded. Keep the complete atlas files together and reload.';\n"
            b"    document.body.prepend(alert);\n"
            b"  };\n"
            b"  try {\n"
            b"    const runtime = JSON.parse(document.getElementById('atlas-static-bootstrap').textContent).runtime;\n"
            b"    const script = document.createElement('script');\n"
            b"    script.src = runtime.path;\n"
            b"    script.async = false;\n"
            b"    if (location.protocol === 'http:' || location.protocol === 'https:') {\n"
            b"      script.integrity = runtime.integrity;\n"
            b"      script.crossOrigin = 'anonymous';\n"
            b"    } else if (location.protocol !== 'file:') { throw new Error('Unsupported atlas protocol'); }\n"
            b"    script.onerror = fail;\n"
            b"    document.body.append(script);\n"
            b"  } catch (error) { fail(); }\n"
            b"})();\n"
            b'</script>"""\n'
            b"\n"
            b"\n"
            b"class _FixedJsonBindings(HTMLParser):\n"
            b'    """Read the two document-owned JSON nodes without treating tag order as identity."""\n'
            b"\n"
            b"    def __init__(self) -> None:\n"
            b"        super().__init__(convert_charrefs=False)\n"
            b"        self.bindings: dict[str, list[list[str] | None]] = {\n"
            b'            "atlas-native-lra-binding": [],\n'
            b'            "atlas-modeled-context-binding": [],\n'
            b"        }\n"
            b"        self.active: list[str] | None = None\n"
            b"\n"
            b"    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:\n"
            b'        identities = [value for key, value in attrs if key == "id"]\n'
            b"        for identity in identities:\n"
            b"            if identity is None or identity not in self.bindings:\n"
            b"                continue\n"
            b"            value: list[str] | None = (\n"
            b"                []\n"
            b'                if tag == "script"\n'
            b"                and len(identities) == 1\n"
            b'                and [value for key, value in attrs if key == "type"]\n'
            b'                == ["application/json"]\n'
            b"                else None\n"
            b"            )\n"
            b"            self.bindings[identity].append(value)\n"
            b"            if value is not None:\n"
            b"                self.active = value\n"
            b"\n"
            b"    def handle_data(self, data: str) -> None:\n"
            b"        if self.active is not None:\n"
            b"            self.active.append(data)\n"
            b"\n"
            b"    def handle_endtag(self, tag: str) -> None:\n"
            b'        if tag == "script":\n'
            b"            self.active = None\n"
            b"\n"
            b"\n"
            b"def _runtime_resources(\n"
            b"    assets: StaticAtlasAssets,\n"
            b"    runtime_bytes: int,\n"
            b"    document: str,\n"
            b"    optional_bytes: int | tuple[int, ...] = 0,\n"
            b") -> None:\n"
            b'    """Charge executable transport and the actual inline binding to both budgets."""\n'
            b"    parser = _FixedJsonBindings()\n"
            b"    parser.feed(document)\n"
            b"    parser.close()\n"
            b"    inline_bytes = 0\n"
            b"    for bindings in parser.bindings.values():\n"
            b"        if len(bindings) != 1 or bindings[0] is None:\n"
            b"            raise ValueError(\n"
            b'                "static map document requires one of each fixed JSON binding"\n'
            b"            )\n"
            b'        body = "".join(bindings[0])\n'
            b"        json.loads(body)\n"
            b'        inline_bytes += len(body.encode("utf-8"))\n'
            b"    if not 0 < runtime_bytes <= ATLAS_DOCUMENT_MAX_BYTES:\n"
            b'        raise ValueError("static atlas runtime exceeds its byte budget")\n'
            b"    controllers = (\n"
            b"        (() if optional_bytes == 0 else (optional_bytes,))\n"
            b"        if type(optional_bytes) is int\n"
            b"        else optional_bytes\n"
            b"    )\n"
            b"    if (\n"
            b"        type(controllers) is not tuple\n"
            b"        or len(controllers) > len(_OPTIONAL_CONTROLLERS)\n"
            b"        or any(\n"
            b"            type(size) is not int or not 0 < size <= ATLAS_DOCUMENT_MAX_BYTES\n"
            b"            for size in controllers\n"
            b"        )\n"
            b"    ):\n"
            b'        raise ValueError("static atlas optional controller exceeds its byte budget")\n'
            b'    rows = normalize_asset_inventory(assets.manifest["assets"])\n'
            b"    counts: list[int] = []\n"
            b"    initial: list[int] = []\n"
            b"    for row in rows:\n"
            b'        count = row.get("byte_count")\n'
            b"        if type(count) is not int or count < 0:\n"
            b'            raise ValueError("static atlas asset byte count is invalid")\n'
            b"        counts.append(count)\n"
            b'        if row.get("initial_load") is True:\n'
            b"            initial.append(count)\n"
            b"    if len(initial) + 1 > ATLAS_INITIAL_MAX_REQUESTS:\n"
            b'        raise ValueError("static atlas runtime exceeds initial request budget")\n'
            b"    if sum(initial) + runtime_bytes + inline_bytes > ATLAS_INITIAL_MAX_BYTES:\n"
            b'        raise ValueError("static atlas runtime exceeds initial byte budget")\n'
            b"    if len(rows) + 1 + len(controllers) > ATLAS_STATIC_ASSETS_MAX_FILES:\n"
            b'        raise ValueError("static atlas runtime exceeds total asset count budget")\n'
            b"    if (\n"
            b"        sum(counts) + runtime_bytes + inline_bytes + sum(controllers)\n"
            b"        > ATLAS_STATIC_ASSETS_MAX_BYTES\n"
            b"    ):\n"
            b'        raise ValueError("static atlas runtime exceeds total asset byte budget")\n'
            b"\n"
            b"\n"
            b"def _separate_evidence_tools(body: str) -> tuple[bytes, bytes]:\n"
            b'    """Move only the complete marked helper block into its explicit factory."""\n'
            b"    if body.count(_EVIDENCE_BEGIN) != 1 or body.count(_EVIDENCE_END) != 1:\n"
            b'        raise ValueError("static map requires one evidence tools boundary")\n'
            b"    matches = [\n"
            b'        re.search(r"(?m)^[ \\t]*" + re.escape(marker) + r"[ \\t]*$", body)\n'
            b"        for marker in (_EVIDENCE_BEGIN, _EVIDENCE_END)\n"
            b"    ]\n"
            b"    begin, end = matches\n"
            b'    opening = re.match(r"\\s*\\(async \\(\\) => \\{", body)\n'
            b'    closing = re.search(r"(?m)^[ \\t]*\\}\\)\\(\\)\\.catch\\(", body)\n'
            b"    if (\n"
            b"        begin is None\n"
            b"        or end is None\n"
            b"        or opening is None\n"
            b"        or closing is None\n"
            b"        or not opening.end() <= begin.start() < end.start() < closing.start()\n"
            b"    ):\n"
            b'        raise ValueError("static map evidence tools boundary is unsafe")\n'
            b"    helpers = body[begin.end() : end.start()]\n"
            b"    if not helpers.strip():\n"
            b'        raise ValueError("static map evidence tools block is empty")\n'
            b"    return (\n"
            b'        (body[: begin.start()] + body[end.end() :]).encode("utf-8"),\n'
            b'        (_EVIDENCE_FACTORY % helpers).encode("utf-8"),\n'
            b"    )\n"
            b"\n"
            b"\n"
            b"def _code_reference(\n"
            b"    parent: Path, stem: str, kind: str, body: bytes\n"
            b") -> tuple[Path, dict[str, object]]:\n"
            b"    digest = hashlib.sha256(body).digest()\n"
            b'    path = parent / f"{stem}.{kind}.{digest.hex()[:16]}.js"\n'
            b"    return path, {\n"
            b'        "path": path.name,\n'
            b'        "byte_count": len(body),\n'
            b'        "integrity": "sha256-" + base64.b64encode(digest).decode("ascii"),\n'
            b"    }\n"
            b"\n"
            b"\n"
            b"def _check_code_target(path: Path, payload: bytes) -> None:\n"
            b"    if path.is_symlink() or (\n"
            b"        path.exists() and (not path.is_file() or path.stat().st_nlink != 1)\n"
            b"    ):\n"
            b'        raise ValueError("static map code must be an unaliased immutable file")\n'
            b"    if path.exists() and path.read_bytes() != payload:\n"
            b'        raise ValueError(f"static atlas asset collision: {path.name}")\n'
            b"\n"
            b"\n"
            b"def static_map_optional_controller_paths(document_path: Path) -> tuple[Path, ...]:\n"
            b'    """Read the exact distributed code reference for bundle inventory closure."""\n'
            b"    document_path = document_path.absolute()\n"
            b"    if (\n"
            b"        document_path.resolve(strict=True) != document_path\n"
            b"        or not document_path.is_file()\n"
            b"        or document_path.stat().st_nlink != 1\n"
            b"    ):\n"
            b'        raise ValueError("static map inventory requires a physical document")\n'
            b'    bootstraps = list(_BOOTSTRAP.finditer(document_path.read_text(encoding="utf-8")))\n'
            b"    if len(bootstraps) != 1:\n"
            b'        raise ValueError("static map inventory requires one bootstrap")\n'
            b"    bootstrap = json.loads(bootstraps[0].group(2))\n"
            b"    if not isinstance(bootstrap, dict) or not isinstance(\n"
            b'        bootstrap.get("runtime", {}), dict\n'
            b"    ):\n"
            b'        raise ValueError("static map runtime identity is invalid")\n'
            b'    runtime = bootstrap.get("runtime", {})\n'
            b'    if "optional_controllers" not in runtime:\n'
            b"        return ()\n"
            b'    optional = runtime["optional_controllers"]\n'
            b"    if not isinstance(optional, dict) or set(optional) not in (\n"
            b'        {"evidence_tools"},\n'
            b"        set(_OPTIONAL_CONTROLLERS),\n"
            b"    ):\n"
            b'        raise ValueError("static map optional controller identity is invalid")\n'
            b"    result = []\n"
            b"    for key, kind in _OPTIONAL_CONTROLLERS.items():\n"
            b"        if key not in optional:\n"
            b"            continue\n"
            b"        reference = optional[key]\n"
            b"        if not isinstance(reference, dict) or not isinstance(\n"
            b'            reference.get("path"), str\n'
            b"        ):\n"
            b'            raise ValueError("static map optional controller identity is invalid")\n'
            b'        name = reference["path"]\n'
            b"        if not re.fullmatch(\n"
            b"            re.escape(document_path.stem)\n"
            b'            + r"\\."\n'
            b"            + re.escape(kind)\n"
            b'            + r"\\.[a-f0-9]{16}\\.js",\n'
            b"            name,\n"
            b"        ):\n"
            b'            raise ValueError("static map optional controller path is invalid")\n'
            b"        path = document_path.parent / name\n"
            b"        if path.is_symlink() or not path.is_file() or path.stat().st_nlink != 1:\n"
            b'            raise ValueError("static map optional controller must be an unaliased file")\n'
            b"        payload = path.read_bytes()\n"
            b"        _, actual = _code_reference(path.parent, document_path.stem, kind, payload)\n"
            b"        if (\n"
            b"            reference != actual\n"
            b"            or not 0 < len(payload) <= ATLAS_DOCUMENT_MAX_BYTES\n"
            b"            or path in result\n"
            b"        ):\n"
            b'            raise ValueError("static map optional controller bytes differ")\n'
            b"        result.append(path)\n"
            b"    return tuple(result)\n"
            b"\n"
            b"\n"
            b"def write_static_map_document(\n"
            b"    output_path: Path,\n"
            b"    title: str,\n"
            b"    version: str,\n"
            b"    generated_on: str,\n"
            b"    countries: tuple[str, ...],\n"
            b"    policy: MapScopePolicy,\n"
            b"    point_layers: list[JsonObject],\n"
            b"    polygon_layers: list[JsonObject],\n"
            b"    asset_base_path: str,\n"
            b"    static_assets: StaticAtlasAssets,\n"
            b"    *,\n"
            b"    native_lra: dict[str, Any] | None = None,\n"
            b") -> tuple[Path, Path]:\n"
            b'    """Write bounded HTML, main IIFE and lazily requested evidence tools.\n'
            b"\n"
            b"    Runtime identity belongs to the distributed document, outside scientific\n"
            b"    chunk identities. HTTP(S) uses SRI; file transport has no pre-execution SRI,\n"
            b"    matching the existing offline policy. The return remains HTML/main runtime;\n"
            b"    bundle inventories must also include the declared optional controller path.\n"
            b'    """\n'
            b"    output = output_path.absolute()\n"
            b"    parent = output.parent\n"
            b"    if (\n"
            b"        not parent.is_dir()\n"
            b"        or parent.resolve(strict=True) != parent\n"
            b"        or static_assets.manifest_path.parent.absolute() != parent\n"
            b'        or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", output.stem)\n'
            b"        or output.is_symlink()\n"
            b"        or (output.exists() and (not output.is_file() or output.stat().st_nlink != 1))\n"
            b"    ):\n"
            b'        raise ValueError("static map document requires its physical asset directory")\n'
            b"    document = _compose_map_document(\n"
            b"        title,\n"
            b"        version,\n"
            b"        generated_on,\n"
            b"        countries,\n"
            b"        policy,\n"
            b"        point_layers,\n"
            b"        polygon_layers,\n"
            b"        asset_base_path,\n"
            b"        static_assets,\n"
            b"        native_lra=native_lra,\n"
            b"    )\n"
            b"    if document.count(_RUNTIME_BEGIN) != 1 or document.count(_RUNTIME_END) != 1:\n"
            b'        raise ValueError("static map document requires one runtime boundary")\n'
            b"    before, tail = document.split(_RUNTIME_BEGIN)\n"
            b"    marked, after = tail.split(_RUNTIME_END)\n"
            b'    match = re.fullmatch(r"\\s*<script>(.*)</script>\\s*", marked, re.DOTALL)\n'
            b"    if match is None:\n"
            b'        raise ValueError("static map runtime boundary is invalid")\n'
            b"    body, evidence_body = _separate_evidence_tools(match.group(1))\n"
            b'    index_body = files(__package__).joinpath("assets/index-transport.js").read_bytes()\n'
            b"    _runtime_resources(\n"
            b"        static_assets, len(body), document, (len(evidence_body), len(index_body))\n"
            b"    )\n"
            b'    runtime, reference = _code_reference(parent, output.stem, "atlas-runtime", body)\n'
            b"    evidence, evidence_reference = _code_reference(\n"
            b'        parent, output.stem, "atlas-evidence-tools", evidence_body\n'
            b"    )\n"
            b"    indexes, index_reference = _code_reference(\n"
            b'        parent, output.stem, "atlas-index-transport", index_body\n'
            b"    )\n"
            b'    reference["optional_controllers"] = {\n'
            b'        "evidence_tools": evidence_reference,\n'
            b'        "index_transport": index_reference,\n'
            b"    }\n"
            b"    document = before + _RUNTIME_LOADER + after\n"
            b"    bootstraps = list(_BOOTSTRAP.finditer(document))\n"
            b"    if (\n"
            b"        len(bootstraps) != 1\n"
            b"        or json.loads(bootstraps[0].group(2)) != static_assets.manifest\n"
            b"    ):\n"
            b'        raise ValueError("static map bootstrap differs from its scientific assets")\n'
            b"    bootstrap = bootstraps[0]\n"
            b"    encoded = serialize_json_for_script(\n"
            b'        {**static_assets.manifest, "runtime": reference}\n'
            b"    )\n"
            b'    if len(encoded.encode("utf-8")) > ATLAS_BOOTSTRAP_MAX_BYTES:\n'
            b'        raise ValueError("static atlas runtime bootstrap exceeds its byte budget")\n'
            b"    document = document[: bootstrap.start(2)] + encoded + document[bootstrap.end(2) :]\n"
            b"    validate_static_atlas_document(document)\n"
            b"    _check_code_target(runtime, body)\n"
            b"    _check_code_target(evidence, evidence_body)\n"
            b"    _check_code_target(indexes, index_body)\n"
            b"    write_immutable(runtime, body)\n"
            b"    write_immutable(evidence, evidence_body)\n"
            b"    write_immutable(indexes, index_body)\n"
            b'    output.write_text(document, encoding="utf-8")\n'
            b"    return output, runtime\n"
        ),
    ),
)


def atlas_renderer_transport_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Admit two exact current factory bindings, preserving every original byte."""
    if (
        name != _SOURCE
        or len(captured) != 2007
        or sha256(captured).hexdigest() != _ORIGINAL_SHA256
    ):
        return False
    resource = b"sourceExport:createSourceRecordExport,sourceResources:createSourceResourceBrowser,"
    if resource in current:
        if current.count(resource) != 1:
            return False
        current = current.replace(
            resource, b"sourceExport:createSourceRecordExport,", 1
        )
    if sha256(current).hexdigest() != _TRANSPORT_SHA256:
        return False
    restored = current
    for prior, extension in _TRANSPORT_SPANS:
        if restored.count(extension) != 1:
            return False
        restored = restored.replace(extension, prior, 1)
    return restored == captured
