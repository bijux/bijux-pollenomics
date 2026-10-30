"""Bind declared relation context and producer inventories to fixed old sources."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from ..presentation_source_roles import atlas_extension_matches
from .documentation import DOCUMENTED_SOURCE_STRINGS, _documented_source_matches

_RELATION_CONTEXT_CONTRACTS: dict[
    str, tuple[int, str, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py": (
        8379,
        "220ba4fbc8e3f884408b6b7bec47d6e70b021a1fe3f4d517c259dabf8681b834",
        "existing_named_documentation",
        (
            (
                (
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/scoring.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/__init__.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/union.py",\n'
                ),
                (
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/candidates/scoring.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/__init__.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/relation.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/selection.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py",\n'
                    b'    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/union.py",\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/geojson.py": (
        2256,
        "45e5cee80192bc03f149bdfc86b0a679875bf8e68146f4342454b8dbec2bfb4b",
        "ordinary_original_bytes",
        (
            (
                (
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                    b"\n"
                    b"from ..network import PhenomenonEvent, PropagationCandidate\n"
                    b"\n"
                    b"\n"
                    b"def candidate_geojson(\n"
                ),
                (
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                    b"\n"
                    b"from ..candidates import CandidatePropagationScenario\n"
                    b"from ..network import PhenomenonEvent, PropagationCandidate\n"
                    b"from .relation import candidate_relation_details\n"
                    b"\n"
                    b"\n"
                    b"def candidate_geojson(\n"
                ),
            ),
            (
                (
                    b"    events: Mapping[str, PhenomenonEvent],\n"
                    b"    *,\n"
                    b"    directional: bool,\n"
                    b") -> dict[str, object]:\n"
                    b'    """Export evaluated rows without inferring a route or changing uncertainty."""\n'
                    b"    features = []\n"
                ),
                (
                    b"    events: Mapping[str, PhenomenonEvent],\n"
                    b"    *,\n"
                    b"    directional: bool,\n"
                    b"    scenario: CandidatePropagationScenario,\n"
                    b") -> dict[str, object]:\n"
                    b'    """Export evaluated rows without inferring a route or changing uncertainty."""\n'
                    b"    features = []\n"
                ),
            ),
            (
                (
                    b'                    "target_observation_ids": list(target.observation_ids),\n'
                    b'                    "source_event": source.as_dict(),\n'
                    b'                    "target_event": target.as_dict(),\n'
                    b"                },\n"
                    b"            }\n"
                    b"        )\n"
                ),
                (
                    b'                    "target_observation_ids": list(target.observation_ids),\n'
                    b'                    "source_event": source.as_dict(),\n'
                    b'                    "target_event": target.as_dict(),\n'
                    b'                    "relation_details": candidate_relation_details(\n'
                    b"                        row, source, target, scenario\n"
                    b"                    ),\n"
                    b"                },\n"
                    b"            }\n"
                    b"        )\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/projection/service.py": (
        5746,
        "32192101f980cedc3291f68795838ab7437404a1697f77ba699c2e21ae15867f",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    return {\n"
                    b'        "directed_candidates.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(directed, events, directional=True),\n"
                    b"        },\n"
                    b'        "indeterminate_pairs.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(indeterminate, events, directional=False),\n"
                    b"        },\n"
                    b'        "lower_level_edge_union.json": {\n'
                    b"            **metadata,\n"
                ),
                (
                    b"    return {\n"
                    b'        "directed_candidates.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(\n"
                    b"                directed, events, directional=True, scenario=result.scenario\n"
                    b"            ),\n"
                    b"        },\n"
                    b'        "indeterminate_pairs.geojson": {\n'
                    b"            **metadata,\n"
                    b"            **candidate_geojson(\n"
                    b"                indeterminate, events, directional=False, scenario=result.scenario\n"
                    b"            ),\n"
                    b"        },\n"
                    b'        "lower_level_edge_union.json": {\n'
                    b"            **metadata,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py": (
        8502,
        "e131724adacd5471cdc1b236079b5d091b33ed618ed5e1e1c8afab49363a0e57",
        "existing_named_native_asset_binding",
        (
            (
                (
                    b'            \'<div class="inline-actions"><button id="lra-download" \'\n'
                    b'            \'class="inline-button is-primary" type="button">\'\n'
                    b'            "Download selected estimates</button></div>"\n'
                    b'            \'<p class="search-meta"><a href="native-view.json">Complete bound model view</a> \xc2\xb7 \'\n'
                    b"            '<a href=\"index.html\">Complete report and original product downloads</a>'\n"
                    b'            "</p></div></details>"\n'
                ),
                (
                    b'            \'<div class="inline-actions"><button id="lra-download" \'\n'
                    b'            \'class="inline-button is-primary" type="button">\'\n'
                    b'            "Download selected estimates</button></div>"\n'
                    b'            \'<section id="lra-method-context" aria-label="Native LRA method and declared uncertainty">\'\n'
                    b"            '<p class=\"search-meta\">Method and uncertainty context unavailable until the bound model view is loaded.</p>'\n"
                    b'            "</section>"\n'
                    b'            \'<p class="search-meta"><a href="native-view.json">Complete bound model view</a> \xc2\xb7 \'\n'
                    b"            '<a href=\"index.html\">Complete report and original product downloads</a>'\n"
                    b'            "</p></div></details>"\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence.py": (
        11083,
        "0042bf044bc3ac845294ae0e060e0e36ce8ebbfbc7c022cddb3987c377aedfc7",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                ),
                (
                    b'"""Validate and normalize optional Atlas source, signal, and relation records."""\n'
                    b"\n"
                    b"from __future__ import annotations\n"
                    b"\n"
                    b"from collections.abc import Mapping, Sequence\n"
                ),
            ),
            (
                (
                    b"\n"
                    b"@dataclass(frozen=True)\n"
                    b"class AtlasEvidence:\n"
                    b"    detail_records: tuple[JsonObject, ...]\n"
                    b"    edge_records: tuple[JsonObject, ...]\n"
                    b"    scientific_signals: tuple[JsonObject, ...]\n"
                ),
                (
                    b"\n"
                    b"@dataclass(frozen=True)\n"
                    b"class AtlasEvidence:\n"
                    b'    """Normalized detail, relation, signal, and sequence records for map display."""\n'
                    b"\n"
                    b"    detail_records: tuple[JsonObject, ...]\n"
                    b"    edge_records: tuple[JsonObject, ...]\n"
                    b"    scientific_signals: tuple[JsonObject, ...]\n"
                ),
            ),
            (
                (
                    b'                "target_record_id": _required_text(row, "target_record_id", "edge"),\n'
                    b'                "source_country": source_country,\n'
                    b'                "target_country": target_country,\n'
                    b'                "cross_border": source_country != target_country,\n'
                    b"            }\n"
                    b"        )\n"
                    b'    normalized.sort(key=lambda item: str(item["edge_id"]))\n'
                ),
                (
                    b'                "target_record_id": _required_text(row, "target_record_id", "edge"),\n'
                    b'                "source_country": source_country,\n'
                    b'                "target_country": target_country,\n'
                    b"                # Historical flat edges use label compatibility. Native candidate\n"
                    b"                # flags retain their original value or absence without inference.\n"
                    b"                **(\n"
                    b'                    {"cross_border": source_country != target_country}\n'
                    b'                    if "candidate_status" not in row\n'
                    b"                    else {}\n"
                    b"                ),\n"
                    b"            }\n"
                    b"        )\n"
                    b'    normalized.sort(key=lambda item: str(item["edge_id"]))\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/native-lra.js": (
        18936,
        "33bd7c0644279d96c37d07960279be04f986c4d91ae42cbaa460536aa659818e",
        "ordinary_original_bytes",
        (
            (
                (
                    b"  return Object.freeze({refresh});\n"
                    b"}\n"
                    b"\n"
                    b"function createNativeLraController(view, viewSha256, adapters) "
                    b"{\n"
                    b"  'use strict';\n"
                    b"  const clone = value => JSON.parse(JSON.stringify(value));\n"
                ),
                (
                    b"  return Object.freeze({refresh});\n"
                    b"}\n"
                    b"\n"
                    b"function nativeLraMethodContextHtml(view) {\n"
                    b"  const object = value => value !== null && typeof value === "
                    b"'object' && !Array.isArray(value);\n"
                    b"  const escape = value => String(value).replace(/[&<>\"']/g, "
                    b"character => ({'&':'&amp;','<':'&lt;','>':'&gt;','\""
                    b"':'&quot;',\"'\":'&#39;'}[character]));\n"
                    b"  const literal = value => escape(JSON.stringify(value));\n"
                    b"  const method = object(view?.method) ? view.method : {};\n"
                    b"  const profile = typeof method.profile === 'string' && "
                    b"method.profile.trim()\n"
                    b"    ? escape(method.profile) : 'Unavailable: no valid method "
                    b"profile supplied.';\n"
                    b"  function settings(value, label) {\n"
                    b"    if (!object(value)) return `<p>${escape(label)} unavailable: "
                    b"no settings object supplied.</p>`;\n"
                    b"    const rows = [];\n"
                    b"    function append(record, prefix) {\n"
                    b"      Object.entries(record).forEach(([key, item]) => {\n"
                    b"        const path = prefix ? `${prefix}.${key}` : key;\n"
                    b"        if (object(item) && Object.keys(item).length) "
                    b"append(item, path);\n"
                    b'        else rows.push(`<tr><th scope="row">${escape(path)}</th><'
                    b"td>${literal(item)}</td></tr>`);\n"
                    b"      });\n"
                    b"    }\n"
                    b"    append(value, '');\n"
                    b"    return rows.length\n"
                    b'      ? `<div class="focus-detail-table-wrap"><table '
                    b'class="focus-detail-table"><caption>${escape(label)}</caption><th'
                    b'ead><tr><th scope="col">Declared field</th><th '
                    b'scope="col">Literal value</th></tr></thead><tbody>${rows.join(\''
                    b"')}</tbody></table></div>`\n"
                    b"      : `<p>${escape(label)}: no fields declared.</p>`;\n"
                    b"  }\n"
                    b"  const omissions = view?.uncertainty_omissions;\n"
                    b"  const uncertainty = Array.isArray(omissions) && "
                    b"omissions.every(value => typeof value === 'string' && "
                    b"value.trim())\n"
                    b"    ? omissions.length ? `<ul>${omissions.map(value => "
                    b"`<li>${escape(value)}</li>`).join('')}</ul>`\n"
                    b"      : '<p>No uncertainty omissions were declared. This does not "
                    b"establish complete uncertainty coverage.</p>'\n"
                    b"    : '<p>Declared uncertainty omissions unavailable: no valid "
                    b"list supplied.</p>';\n"
                    b"  return `<h4>Method and declared uncertainty</h4><p>Method "
                    b"profile: ${profile}</p>${settings(method.configuration, 'Declared "
                    b"configuration')}${settings(method.versions, 'Declared "
                    b"versions')}<h5>Declared uncertainty "
                    b"omissions</h5>${uncertainty}<p>These are declarations from the "
                    b"bound result, not validated assumptions or scientific approval. "
                    b"Display filters do not refit the model. Method summaries do not "
                    b"establish total uncertainty or held-out predictive "
                    b"coverage.</p>`;\n"
                    b"}\n"
                    b"\n"
                    b"function createNativeLraController(view, viewSha256, adapters) "
                    b"{\n"
                    b"  'use strict';\n"
                    b"  const clone = value => JSON.parse(JSON.stringify(value));\n"
                ),
            ),
            (
                (
                    b"  function mount() {\n"
                    b"    const host = document.getElementById('lra-controls');\n"
                    b"    host.hidden = false;\n"
                    b"    Object.entries({roles: 'lra-role', site_ids: 'lra-site', "
                    b"taxa: 'lra-taxon', bin_ids: 'lra-bin'}).forEach(([key, id]) => "
                    b"{\n"
                    b"      const control = document.getElementById(id);\n"
                    b"      allowed[key].forEach(value => {\n"
                ),
                (
                    b"  function mount() {\n"
                    b"    const host = document.getElementById('lra-controls');\n"
                    b"    host.hidden = false;\n"
                    b"    const methodContext = document.getElementById('lra-method-con"
                    b"text');\n"
                    b"    if (methodContext) methodContext.innerHTML = "
                    b"nativeLraMethodContextHtml(view);\n"
                    b"    Object.entries({roles: 'lra-role', site_ids: 'lra-site', "
                    b"taxa: 'lra-taxon', bin_ids: 'lra-bin'}).forEach(([key, id]) => "
                    b"{\n"
                    b"      const control = document.getElementById(id);\n"
                    b"      allowed[key].forEach(value => {\n"
                ),
            ),
        ),
    ),
}
NATIVE_METHOD_CONTEXT_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/assets/native-lra.js"
ATLAS_RELATION_CONTEXT_SOURCES = frozenset(
    name for name in _RELATION_CONTEXT_CONTRACTS if name != NATIVE_METHOD_CONTEXT_SOURCE
)
CHRONOLOGY_ATLAS_RELATION_CONTEXT_SOURCES = frozenset(_RELATION_CONTEXT_CONTRACTS)
_MODELS_SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/propagation/outputs/models.py"
_PAYLOAD_SOURCE = (
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/payload.py"
)
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


def atlas_relation_context_extension_matches(
    name: str, captured: bytes, current: bytes
) -> bool:
    """Restore each fixed source through only relation spans and its named prior law."""
    contract = _RELATION_CONTEXT_CONTRACTS.get(name)
    if contract is None:
        return False
    size, digest, composition, spans = contract
    if len(captured) != size or hashlib.sha256(captured).hexdigest() != digest:
        return False
    restored = current
    for original, extension in spans:
        if restored.count(extension) != 1:
            return False
        restored = restored.replace(extension, original, 1)
    if any(restored.count(original) != 1 for original, _ in spans):
        return False
    if composition == "ordinary_original_bytes":
        return restored == captured
    if composition == "existing_named_documentation":
        return (
            name == _MODELS_SOURCE
            and name in DOCUMENTED_SOURCE_STRINGS
            and _documented_source_matches(name, captured, restored)
        )
    if composition == "existing_named_native_asset_binding":
        return name == _PAYLOAD_SOURCE and atlas_extension_matches(
            name, captured, restored
        )
    return False


def validated_atlas_relation_context_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate changed relation semantics without retagging native observations."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    name = historical.get("path")
    contract = _RELATION_CONTEXT_CONTRACTS.get(name) if isinstance(name, str) else None
    if not isinstance(name, str) or contract is None:
        raise ReportRebuildError("Unknown Atlas relation context source")
    size, digest, composition, spans = contract
    expected = {"sha256": digest, "bytes": size}
    if (
        context is None
        or (
            name == NATIVE_METHOD_CONTEXT_SOURCE
            and source_buffer.prefix
            != "data/atlas/sample-chronology-source-view-capture"
        )
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
        raise ReportRebuildError("Atlas relation context source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        name,
        "current Atlas relation context",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError("Atlas relation context source is linked or unbounded")
    current = current_path.read_bytes()
    if not atlas_relation_context_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Atlas relation context differs beyond its declared source changes"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        name,
        "current Atlas relation context",
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
            "Atlas relation context source changed during verification"
        )
    return {
        "path": name,
        "classification": "atlas_relation_context_extension",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": digest,
        "whole_old_module_reconstructed": True,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "named_relation_and_exact_documentation_spans_reversed": len(spans),
        "preexisting_source_correspondence": composition,
        "projection_method_context_and_refusals_intentionally_extended": True,
        "producer_inventory_intentionally_extended": name == _MODELS_SOURCE,
        "retained_current_producer_digest_guard_relaxed": False,
        "all_current_projection_outputs_equal_claimed": False,
        "historical_native_equal_current_output_claimed": False,
        "historical_browser_equal_current_browser_claimed": False,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
        **(
            {"declared_native_method_display_intentionally_extended": True}
            if name == NATIVE_METHOD_CONTEXT_SOURCE
            else {}
        ),
    }
