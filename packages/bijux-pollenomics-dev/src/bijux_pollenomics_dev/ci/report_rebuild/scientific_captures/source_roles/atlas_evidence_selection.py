"""Authenticate bounded Atlas controller transport and selected-interval refinements."""

from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from .atlas_runtime_transport import atlas_runtime_transport_extension_matches

_SELECTION_TRANSPORT_CONTRACTS: dict[
    str, tuple[int, str, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py": (
        2007,
        "5d4e6e72c8794e40d6a741d40a74d7c0e3dbe6de9791e0c555f3043da5bf0def",
        "runtime_transport_extension",
        (
            (
                (
                    b'</script>"""\n'
                    b"\n"
                    b"\n"
                    b"def _runtime_resources(assets: StaticAtlasAssets, runtime_bytes: "
                    b"int) -> None:\n"
                    b'    """Include executable transport in the existing initial and '
                    b'total budgets."""\n'
                    b"    if not 0 < runtime_bytes <= ATLAS_DOCUMENT_MAX_BYTES:\n"
                    b'        raise ValueError("static atlas runtime exceeds its byte '
                    b'budget")\n'
                    b'    rows = normalize_asset_inventory(assets.manifest["assets"])\n'
                    b"    counts: list[int] = []\n"
                    b"    initial: list[int] = []\n"
                ),
                (
                    b'</script>"""\n'
                    b"\n"
                    b"\n"
                    b"def _runtime_resources(\n"
                    b"    assets: StaticAtlasAssets,\n"
                    b"    runtime_bytes: int,\n"
                    b"    document: str,\n"
                    b"    optional_bytes: int = 0,\n"
                    b") -> None:\n"
                    b'    """Charge executable transport and the actual inline binding '
                    b'to both budgets."""\n'
                    b"    bindings = _NATIVE_BINDING.findall(document)\n"
                    b"    if len(bindings) != 1:\n"
                    b'        raise ValueError("static map document requires one native '
                    b'binding payload")\n'
                    b"    json.loads(bindings[0])\n"
                    b'    inline_bytes = len(bindings[0].encode("utf-8"))\n'
                    b"    if not 0 < runtime_bytes <= ATLAS_DOCUMENT_MAX_BYTES:\n"
                    b'        raise ValueError("static atlas runtime exceeds its byte '
                    b'budget")\n'
                    b"    if (\n"
                    b"        type(optional_bytes) is not int\n"
                    b"        or not 0 <= optional_bytes <= ATLAS_DOCUMENT_MAX_BYTES\n"
                    b"    ):\n"
                    b'        raise ValueError("static atlas optional controller '
                    b'exceeds its byte budget")\n'
                    b'    rows = normalize_asset_inventory(assets.manifest["assets"])\n'
                    b"    counts: list[int] = []\n"
                    b"    initial: list[int] = []\n"
                ),
            ),
            (
                (
                    b"            initial.append(count)\n"
                    b"    if len(initial) + 1 > ATLAS_INITIAL_MAX_REQUESTS:\n"
                    b'        raise ValueError("static atlas runtime exceeds initial '
                    b'request budget")\n'
                    b"    if sum(initial) + runtime_bytes > ATLAS_INITIAL_MAX_BYTES:\n"
                    b'        raise ValueError("static atlas runtime exceeds initial '
                    b'byte budget")\n'
                    b"    if len(rows) + 1 > ATLAS_STATIC_ASSETS_MAX_FILES:\n"
                    b'        raise ValueError("static atlas runtime exceeds total '
                    b'asset count budget")\n'
                    b"    if sum(counts) + runtime_bytes > "
                    b"ATLAS_STATIC_ASSETS_MAX_BYTES:\n"
                    b'        raise ValueError("static atlas runtime exceeds total '
                    b'asset byte budget")\n'
                    b"\n"
                    b"\n"
                ),
                (
                    b"            initial.append(count)\n"
                    b"    if len(initial) + 1 > ATLAS_INITIAL_MAX_REQUESTS:\n"
                    b'        raise ValueError("static atlas runtime exceeds initial '
                    b'request budget")\n'
                    b"    if sum(initial) + runtime_bytes + inline_bytes > "
                    b"ATLAS_INITIAL_MAX_BYTES:\n"
                    b'        raise ValueError("static atlas runtime exceeds initial '
                    b'byte budget")\n'
                    b"    if len(rows) + 1 + bool(optional_bytes) > "
                    b"ATLAS_STATIC_ASSETS_MAX_FILES:\n"
                    b'        raise ValueError("static atlas runtime exceeds total '
                    b'asset count budget")\n'
                    b"    if (\n"
                    b"        sum(counts) + runtime_bytes + inline_bytes + "
                    b"optional_bytes\n"
                    b"        > ATLAS_STATIC_ASSETS_MAX_BYTES\n"
                    b"    ):\n"
                    b'        raise ValueError("static atlas runtime exceeds total '
                    b'asset byte budget")\n'
                    b"\n"
                    b"\n"
                ),
            ),
            (
                (
                    b"    *,\n"
                    b"    native_lra: dict[str, Any] | None = None,\n"
                    b") -> tuple[Path, Path]:\n"
                    b'    """Write bounded HTML and its unchanged main IIFE as one '
                    b"immutable sidecar.\n"
                    b"\n"
                    b"    Runtime identity belongs to the distributed document, outside "
                    b"scientific\n"
                    b"    chunk identities. HTTP(S) uses SRI; file transport has no "
                    b"pre-execution SRI,\n"
                    b"    matching the existing offline policy. Callers must inventory "
                    b"both paths.\n"
                    b'    """\n'
                    b"    output = output_path.absolute()\n"
                    b"    parent = output.parent\n"
                ),
                (
                    b"    *,\n"
                    b"    native_lra: dict[str, Any] | None = None,\n"
                    b") -> tuple[Path, Path]:\n"
                    b'    """Write bounded HTML, main IIFE and lazily requested '
                    b"evidence tools.\n"
                    b"\n"
                    b"    Runtime identity belongs to the distributed document, outside "
                    b"scientific\n"
                    b"    chunk identities. HTTP(S) uses SRI; file transport has no "
                    b"pre-execution SRI,\n"
                    b"    matching the existing offline policy. The return remains "
                    b"HTML/main runtime;\n"
                    b"    bundle inventories must also include the declared optional "
                    b"controller path.\n"
                    b'    """\n'
                    b"    output = output_path.absolute()\n"
                    b"    parent = output.parent\n"
                ),
            ),
            (
                (
                    b'    match = re.fullmatch(r"\\s*<script>(.*)</script>\\s*", '
                    b"marked, re.DOTALL)\n"
                    b"    if match is None:\n"
                    b'        raise ValueError("static map runtime boundary is '
                    b'invalid")\n'
                    b'    body = match.group(1).encode("utf-8")\n'
                    b"    _runtime_resources(static_assets, len(body))\n"
                    b"    digest = hashlib.sha256(body).digest()\n"
                    b'    runtime = parent / f"{output.stem}.atlas-runtime.{digest.hex('
                    b')[:16]}.js"\n'
                    b"    reference = {\n"
                    b'        "path": runtime.name,\n'
                    b'        "byte_count": len(body),\n'
                    b'        "integrity": "sha256-" + '
                    b'base64.b64encode(digest).decode("ascii"),\n'
                    b"    }\n"
                    b"    document = before + _RUNTIME_LOADER + after\n"
                    b"    bootstraps = list(_BOOTSTRAP.finditer(document))\n"
                    b"    if (\n"
                ),
                (
                    b'    match = re.fullmatch(r"\\s*<script>(.*)</script>\\s*", '
                    b"marked, re.DOTALL)\n"
                    b"    if match is None:\n"
                    b'        raise ValueError("static map runtime boundary is '
                    b'invalid")\n'
                    b"    body, evidence_body = _separate_evidence_tools(match.group(1)"
                    b")\n"
                    b"    _runtime_resources(static_assets, len(body), document, "
                    b"len(evidence_body))\n"
                    b"    runtime, reference = _code_reference(parent, output.stem, "
                    b'"atlas-runtime", body)\n'
                    b"    evidence, evidence_reference = _code_reference(\n"
                    b'        parent, output.stem, "atlas-evidence-tools", '
                    b"evidence_body\n"
                    b"    )\n"
                    b'    reference["optional_controllers"] = {"evidence_tools": '
                    b"evidence_reference}\n"
                    b"    document = before + _RUNTIME_LOADER + after\n"
                    b"    bootstraps = list(_BOOTSTRAP.finditer(document))\n"
                    b"    if (\n"
                ),
            ),
            (
                (
                    b'        raise ValueError("static atlas runtime bootstrap exceeds '
                    b'its byte budget")\n'
                    b"    document = document[: bootstrap.start(2)] + encoded + "
                    b"document[bootstrap.end(2) :]\n"
                    b"    validate_static_atlas_document(document)\n"
                    b"    if runtime.is_symlink() or (runtime.exists() and "
                    b"runtime.stat().st_nlink != 1):\n"
                    b'        raise ValueError("static map runtime must be an unaliased '
                    b'immutable file")\n'
                    b"    write_immutable(runtime, body)\n"
                    b'    output.write_text(document, encoding="utf-8")\n'
                    b"    return output, runtime\n"
                ),
                (
                    b'        raise ValueError("static atlas runtime bootstrap exceeds '
                    b'its byte budget")\n'
                    b"    document = document[: bootstrap.start(2)] + encoded + "
                    b"document[bootstrap.end(2) :]\n"
                    b"    validate_static_atlas_document(document)\n"
                    b"    _check_code_target(runtime, body)\n"
                    b"    _check_code_target(evidence, evidence_body)\n"
                    b"    write_immutable(runtime, body)\n"
                    b"    write_immutable(evidence, evidence_body)\n"
                    b'    output.write_text(document, encoding="utf-8")\n'
                    b"    return output, runtime\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/finalization.py": (
        3225,
        "fcf8be43d6c73e7acc3be4db275bdcb8e2a8d9a81069e00dbe35432185375cd6",
        "runtime_transport_extension",
        (
            (
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from typing import Any\n"
                    b"\n"
                    b"\n"
                    b"def finalize_bundle(\n"
                ),
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from typing import Any\n"
                    b"\n"
                    b"from ...map_document.render import "
                    b"static_map_optional_controller_paths\n"
                    b"\n"
                    b"\n"
                    b"def finalize_bundle(\n"
                ),
            ),
            (
                (
                    b"        static_assets=static_assets,\n"
                    b"    )\n"
                    b'    extra_artifacts.append(("Static atlas runtime", '
                    b"runtime_path.name))\n"
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.bundle_manifest_path,\n"
                    b"        surface.build_multi_country_bundle_manifest(\n"
                ),
                (
                    b"        static_assets=static_assets,\n"
                    b"    )\n"
                    b'    extra_artifacts.append(("Static atlas runtime", '
                    b"runtime_path.name))\n"
                    b"    extra_artifacts.extend(\n"
                    b'        ("Interactive evidence tools", path.name)\n'
                    b"        for path in static_map_optional_controller_paths(bundle_p"
                    b"aths.map_html_path)\n"
                    b"    )\n"
                    b"    write_summary_json_fn(\n"
                    b"        bundle_paths.bundle_manifest_path,\n"
                    b"        surface.build_multi_country_bundle_manifest(\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/source_chronology/features.py": (
        3399,
        "ddf0605c0a0f1476c9ff6d7ce33235a84ca552eff2323e3e7737dcb9d034361e",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    SourceChronologyNode,\n"
                    b")\n"
                    b"from bijux_pollenomics.core.geospatial.geojson import "
                    b"JsonObject\n"
                    b"\n"
                    b"from .facets import COUNTRY_NAMES, source_ecological_code_label\n"
                    b"\n"
                    b"\n"
                    b"def build_atlas_feature(node: SourceChronologyNode) -> "
                    b"JsonObject:\n"
                    b'    """Project one validated source node without introducing '
                    b'event semantics."""\n'
                    b"    code = node.source_ecological_group\n"
                    b"    name = node.source_reported_name\n"
                    b"    title = (\n"
                ),
                (
                    b"    SourceChronologyNode,\n"
                    b")\n"
                    b"from bijux_pollenomics.core.geospatial.geojson import "
                    b"JsonObject\n"
                    b"from bijux_pollenomics.core.temporal_semantics import "
                    b"canonical_bp_interval\n"
                    b"\n"
                    b"from .facets import COUNTRY_NAMES, source_ecological_code_label\n"
                    b"\n"
                    b"\n"
                    b"def build_atlas_feature(node: SourceChronologyNode) -> "
                    b"JsonObject:\n"
                    b'    """Project one validated source node without introducing '
                    b'event semantics."""\n'
                    b"    if canonical_bp_interval(node.younger_bp, node.older_bp) is "
                    b"None:\n"
                    b"        raise ValueError(\n"
                    b'            "source chronology feature requires a selected '
                    b'numeric interval"\n'
                    b"        )\n"
                    b"    code = node.source_ecological_group\n"
                    b"    name = node.source_reported_name\n"
                    b"    title = (\n"
                ),
            ),
            (
                (
                    b'        "time_start_bp": node.younger_bp,\n'
                    b'        "time_end_bp": node.older_bp,\n'
                    b'        "time_label": _time_label(node.younger_bp, '
                    b"node.older_bp),\n"
                    b'        "provenance_record_id": node.provenance_record_id,\n'
                    b'        "input_digest": node.input_digest,\n'
                    b'        "coordinate_quality": node.coordinate_quality,\n'
                ),
                (
                    b'        "time_start_bp": node.younger_bp,\n'
                    b'        "time_end_bp": node.older_bp,\n'
                    b'        "time_label": _time_label(node.younger_bp, '
                    b"node.older_bp),\n"
                    b'        "temporal_semantics": {\n'
                    b'            "schema_version": "temporal-semantics.v1",\n'
                    b'            "comparability_posture": '
                    b'"numeric_interval_with_caveat",\n'
                    b'            "evidence_class": "source_selected_sample_chronology"'
                    b",\n"
                    b'            "precision_posture": "source_reported_interval",\n'
                    b'            "time_start_bp": node.younger_bp,\n'
                    b'            "time_end_bp": node.older_bp,\n'
                    b'            "chronology_claim_id": node.chronology_claim_id,\n'
                    b'            "comparison_note": (\n'
                    b'                "Selected comparable source sample age only; no '
                    b'harmonized event "\n'
                    b'                "or propagation admission."\n'
                    b"            ),\n"
                    b"        },\n"
                    b'        "provenance_record_id": node.provenance_record_id,\n'
                    b'        "input_digest": node.input_digest,\n'
                    b'        "coordinate_quality": node.coordinate_quality,\n'
                ),
            ),
        ),
    ),
}
ATLAS_EVIDENCE_SELECTION_SOURCES = frozenset(_SELECTION_TRANSPORT_CONTRACTS)
_RENDER_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/render.py"
)
_FEATURES_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/source_chronology/features.py"
_RENDER_DECLARATION_ORDER = (
    "_EVIDENCE_BEGIN",
    "_EVIDENCE_END",
    "_EVIDENCE_FACTORY",
    "_NATIVE_BINDING",
    "_separate_evidence_tools",
    "_code_reference",
    "_check_code_target",
    "static_map_optional_controller_paths",
)
_RENDER_GLOBAL_DECLARATIONS = {
    "_EVIDENCE_BEGIN": '_EVIDENCE_BEGIN = "/* atlas-evidence-tools:begin */"',
    "_EVIDENCE_END": '_EVIDENCE_END = "/* atlas-evidence-tools:end */"',
    "_EVIDENCE_FACTORY": '_EVIDENCE_FACTORY = """globalThis.BijuxPollenomicsEvidenceTools=function(escapeHtml,scientificCueGlyph){\n%s\nreturn Object.freeze({countryData:relationSummaryData,countryHtml:renderRelationSummary,timeData:relationTimeSummaryData,timeHtml:renderRelationTimeSummary,pickerCatalog:scientificPickerCatalog,pickerSearch:scientificPickerSearch,pickerInitial:scientificPickerInitialState,pickerAction:scientificPickerAction,pickerHtml:renderScientificPicker,pickerMount:mountScientificPicker,sourceDetails:createSourceRecordDetails,selectionExport:prepareAtlasSelectionExport});\n};\n"""',
    "_NATIVE_BINDING": '_NATIVE_BINDING = re.compile(\n    r\'<script id="atlas-native-lra-binding" type="application/json">(.*?)</script>\',\n    re.DOTALL,\n)',
}
_RENDER_DEFERRED_SIGNATURES = {
    "_separate_evidence_tools": "def _separate_evidence_tools(body: str) -> tuple[bytes, bytes]:\n    pass",
    "_code_reference": "def _code_reference(parent: Path, stem: str, kind: str, body: bytes) -> tuple[Path, dict[str, object]]:\n    pass",
    "_check_code_target": "def _check_code_target(path: Path, payload: bytes) -> None:\n    pass",
    "static_map_optional_controller_paths": "def static_map_optional_controller_paths(document_path: Path) -> tuple[Path, ...]:\n    pass",
}
_CAPTURE_CONTEXTS = {
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
}


def _declaration_name(node: ast.stmt) -> str | None:
    if isinstance(node, ast.FunctionDef):
        return node.name
    if (
        isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and isinstance(node.targets[0], ast.Name)
    ):
        return node.targets[0].id
    return None


def _signature(node: ast.FunctionDef) -> str:
    skeleton = copy.deepcopy(node)
    skeleton.body = [ast.Pass()]
    return ast.dump(skeleton, include_attributes=False)


def _strip_controller_declarations(current: bytes) -> bytes | None:
    """Remove only eight closed declarations; new deferred bodies are software scope."""
    try:
        text = current.decode("utf-8")
        tree = ast.parse(text)
    except (UnicodeDecodeError, SyntaxError):
        return None
    if not any(
        isinstance(node, ast.ImportFrom)
        and node.module == "__future__"
        and any(item.name == "annotations" for item in node.names)
        for node in tree.body
    ):
        return None
    selected = [
        node
        for node in tree.body
        if _declaration_name(node) in _RENDER_DECLARATION_ORDER
    ]
    if tuple(_declaration_name(node) for node in selected) != _RENDER_DECLARATION_ORDER:
        return None
    lines = text.splitlines(keepends=True)
    ranges = []
    for node in selected:
        name = _declaration_name(node)
        if (
            name is None
            or node.col_offset != 0
            or node.end_lineno is None
            or node.end_col_offset is None
            or lines[node.end_lineno - 1][node.end_col_offset :].strip()
        ):
            return None
        stop = node.end_lineno
        if name in _RENDER_GLOBAL_DECLARATIONS:
            expected = ast.parse(_RENDER_GLOBAL_DECLARATIONS[name]).body
            if len(expected) != 1 or ast.dump(
                node, include_attributes=False
            ) != ast.dump(expected[0], include_attributes=False):
                return None
        else:
            if not isinstance(node, ast.FunctionDef) or node.decorator_list:
                return None
            expected_function = ast.parse(_RENDER_DEFERRED_SIGNATURES[name]).body[0]
            if not isinstance(expected_function, ast.FunctionDef) or _signature(
                node
            ) != _signature(expected_function):
                return None
            if lines[stop : stop + 2] != ["\n", "\n"]:
                return None
            stop += 2
        ranges.append((node.lineno - 1, stop))
    for start, stop in sorted(ranges, reverse=True):
        del lines[start:stop]
    return "".join(lines).encode("utf-8")


def atlas_evidence_selection_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Reconstruct fixed old bytes through declared changes and its exact prior law."""
    contract = _SELECTION_TRANSPORT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, digest, composition, spans = contract
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != digest:
        return False
    if name == _RENDER_SOURCE:
        stripped = _strip_controller_declarations(current)
        if stripped is None:
            return False
        current = stripped
    restored = current
    for original, extension in spans:
        if restored.count(extension) != 1:
            return False
        restored = restored.replace(extension, original, 1)
    if any(restored.count(original) != 1 for original, _ in spans):
        return False
    if composition == "runtime_transport_extension":
        return atlas_runtime_transport_extension_matches(name, captured, restored)
    return composition == "ordinary_original_bytes" and restored == captured


def validated_atlas_evidence_selection_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate selected transport and interval refinements at fixed source epochs."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    name = historical.get("path")
    contract = (
        _SELECTION_TRANSPORT_CONTRACTS.get(name) if isinstance(name, str) else None
    )
    if not isinstance(name, str) or contract is None:
        raise ReportRebuildError("Unknown Atlas evidence selection source")
    size, digest, composition, spans = contract
    expected = {"sha256": digest, "bytes": size}
    if (
        context is None
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for original, path in group["resolved_paths"]
            if original == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Atlas evidence selection source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        name,
        "current Atlas evidence selection",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError(
            "Atlas evidence selection source is linked or unbounded"
        )
    current = current_path.read_bytes()
    if not atlas_evidence_selection_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Atlas evidence selection differs beyond its declared source changes"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        name,
        "current Atlas evidence selection",
    )
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError(
            "Atlas evidence selection source changed during verification"
        )
    return {
        "path": name,
        "classification": "atlas_evidence_selection_extension",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": digest,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "named_selection_transport_spans_reversed": len(spans),
        "preexisting_source_correspondence": composition,
        "eight_closed_controller_declarations_checked": name == _RENDER_SOURCE,
        "optional_transport_and_budget_inventory_intentionally_changed": name
        != _FEATURES_SOURCE,
        "selected_interval_refusal_and_metadata_intentionally_extended": name
        == _FEATURES_SOURCE,
        "current_ordinary_software_controls_required": True,
        "new_deferred_controller_bodies_part_of_historical_equality_claimed": False,
        "current_scientific_chunk_identity_preservation_requires_separate_controls": name
        != _FEATURES_SOURCE,
        "all_current_source_projection_outputs_equal_claimed": False,
        "historical_native_equal_current_output_claimed": False,
        "historical_browser_equal_current_browser_claimed": False,
        "current_runtime_transport_byte_equal_claimed": False,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
    }
