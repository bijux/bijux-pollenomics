"""Bind source-view context extensions to two exact historical input catalogues."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule
from .atlas_runtime_transport import atlas_runtime_transport_extension_matches

_SOURCE_CONTEXT_CONTRACTS: dict[
    str, tuple[int, str, str, tuple[tuple[bytes, bytes], ...]]
] = {
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/neotoma.py": (
        17776,
        "d9c37bbcc962063ad4abfc57b34b51cf6f37248dffd32eccc5ed00cec4ebaf73",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    build_source_chronology_atlas_projection,\n"
                    b")\n"
                    b"\n"
                    b"from .constants import _UNAVAILABLE_CLASSIFICATION, _UNAVAILABLE_RELATION\n"
                    b"from .io import (\n"
                    b"    _decode_json_object,\n"
                    b"    _mapping,\n"
                ),
                (
                    b"    build_source_chronology_atlas_projection,\n"
                    b")\n"
                    b"\n"
                    b"from .constants import (\n"
                    b"    _UNAVAILABLE_CLASSIFICATION,\n"
                    b"    _UNAVAILABLE_RELATION,\n"
                    b"    PROJECTION_SCHEMA_VERSION,\n"
                    b")\n"
                    b"from .io import (\n"
                    b"    _decode_json_object,\n"
                    b"    _mapping,\n"
                ),
            ),
            (
                (
                    b"    _required_text,\n"
                    b"    _safe_relative_path,\n"
                    b")\n"
                    b"from .records import (\n"
                    b"    _compact_rows_by_site,\n"
                    b"    _features,\n"
                ),
                (
                    b"    _required_text,\n"
                    b"    _safe_relative_path,\n"
                    b")\n"
                    b"from .neotoma_chronology import chronology_model_tables, chronology_tab\n"
                    b"from .records import (\n"
                    b"    _compact_rows_by_site,\n"
                    b"    _features,\n"
                ),
            ),
            (
                (
                    b'            "observations",\n'
                    b"        )\n"
                    b"    }\n"
                    b"    surfaces = {name: loaded[0] for name, loaded in loaded_surfaces.items()}\n"
                    b"    sites = _unique_rows(\n"
                    b'        surfaces["sites"],\n'
                ),
                (
                    b'            "observations",\n'
                    b"        )\n"
                    b"    }\n"
                    b'    manifest_surfaces = _mapping(manifest.get("surfaces"), "Neotoma surfaces")\n'
                    b'    for name in ("chronologies", "chronology_controls"):\n'
                    b"        if name in manifest_surfaces:\n"
                    b"            loaded_surfaces[name] = _load_neotoma_surface(\n"
                    b"                relational_root, manifest, name\n"
                    b"            )\n"
                    b"    surfaces = {name: loaded[0] for name, loaded in loaded_surfaces.items()}\n"
                    b"    sites = _unique_rows(\n"
                    b'        surfaces["sites"],\n'
                ),
            ),
            (
                (
                    b'        "Neotoma sites",\n'
                    b"    )\n"
                    b"    governed_sites = _governed_neotoma_sites(sites)\n"
                    b"    collection_rows = _compact_rows_by_site(\n"
                    b'        surfaces["collection_units"],\n'
                    b'        fields=("collection_unit_id", "source_collection_unit_id", "source_payload"),\n'
                ),
                (
                    b'        "Neotoma sites",\n'
                    b"    )\n"
                    b"    governed_sites = _governed_neotoma_sites(sites)\n"
                    b"    model_tables = chronology_model_tables(loaded_surfaces, set(sites))\n"
                    b"    collection_rows = _compact_rows_by_site(\n"
                    b'        surfaces["collection_units"],\n'
                    b'        fields=("collection_unit_id", "source_collection_unit_id", "source_payload"),\n'
                ),
            ),
            (
                (
                    b"                            sample_rows[site_id],\n"
                    b"                        ),\n"
                    b"                    },\n"
                    b'                    "chronology": (\n'
                    b"                        {\n"
                    b"                            **_row_table(\n"
                    b"                                age_fields,\n"
                    b"                                site_age_rows,\n"
                    b"                                identifier_prefixes={\n"
                    b'                                    "chronology_claim_id": "neotoma:age-claim:",\n'
                    b'                                    "subject_id": "neotoma:sample:",\n'
                    b'                                    "source_record_id": "neotoma:sample:",\n'
                    b'                                    "chronology_id": "neotoma:chronology:",\n'
                    b'                                    "collection_unit_id": "neotoma:collection-unit:",\n'
                    b'                                    "dataset_id": "neotoma:dataset:",\n'
                    b"                                },\n"
                    b"                            ),\n"
                    b'                            "interval_semantics": "[younger_bp, older_bp]",\n'
                    b'                            "null_semantics": "source null remains null",\n'
                    b'                            "selection_posture": "all source age assignments retained",\n'
                    b"                        }\n"
                    b"                        if site_age_rows\n"
                    b'                        else _unavailable("neotoma_site_age_claims_not_available")\n'
                    b"                    ),\n"
                    b'                    "pollen_composition": (\n'
                    b"                        {\n"
                ),
                (
                    b"                            sample_rows[site_id],\n"
                    b"                        ),\n"
                    b"                    },\n"
                    b'                    "chronology": chronology_tab(\n'
                    b"                        age_fields, site_age_rows, model_tables[site_id]\n"
                    b"                    ),\n"
                    b'                    "pollen_composition": (\n'
                    b"                        {\n"
                ),
            ),
            (
                (
                    b'                    "relation": dict(_UNAVAILABLE_RELATION),\n'
                    b'                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),\n'
                    b'                    "provenance": {\n'
                    b'                        "source_snapshot_id": source_snapshot_id,\n'
                    b'                        "build_id": build_id,\n'
                    b'                        "materialization_sha256": materialization_sha256,\n'
                ),
                (
                    b'                    "relation": dict(_UNAVAILABLE_RELATION),\n'
                    b'                    "classification": dict(_UNAVAILABLE_CLASSIFICATION),\n'
                    b'                    "provenance": {\n'
                    b'                        "projection_schema_version": PROJECTION_SCHEMA_VERSION,\n'
                    b"                        **{\n"
                    b"                            target: manifest[source]\n"
                    b"                            for source, target in (\n"
                    b'                                ("schema_version", "materialization_schema_version"),\n'
                    b"                                (\n"
                    b'                                    "relational_snapshot_schema_version",\n'
                    b'                                    "relational_snapshot_schema_version",\n'
                    b"                                ),\n"
                    b"                            )\n"
                    b"                            if source in manifest\n"
                    b"                        },\n"
                    b'                        "source_snapshot_id": source_snapshot_id,\n'
                    b'                        "build_id": build_id,\n'
                    b'                        "materialization_sha256": materialization_sha256,\n'
                ),
            ),
            (
                (
                    b'        "observations": sum(len(rows) for rows in observation_rows.values()),\n'
                    b'        "variables": len(variables),\n'
                    b"    }\n"
                    b"    source_node_result = derive_neotoma_source_chronology_nodes(\n"
                    b'        observations=surfaces["observations"],\n'
                    b'        samples=surfaces["samples"],\n'
                ),
                (
                    b'        "observations": sum(len(rows) for rows in observation_rows.values()),\n'
                    b'        "variables": len(variables),\n'
                    b"    }\n"
                    b'    for name in ("chronologies", "chronology_controls"):\n'
                    b"        if name in surfaces:\n"
                    b"            detail_row_counts[name] = len(surfaces[name])\n"
                    b"    source_node_result = derive_neotoma_source_chronology_nodes(\n"
                    b'        observations=surfaces["observations"],\n'
                    b'        samples=surfaces["samples"],\n'
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/evidence_projection/service.py": (
        4520,
        "cd11e76268f0abcb2a541136da6112a6e5a5ab9e23c8e3ad1365c7cc5b1b94b0",
        "ordinary_original_bytes",
        (
            (
                (
                    b"from .io import _regular_absolute_directory, _required_text\n"
                    b"from .models import MapEvidenceProjection\n"
                    b"from .neotoma import _project_neotoma\n"
                    b"from .records import _features, _is_unavailable, _tabs\n"
                    b"from .sead import _project_sead\n"
                    b"\n"
                ),
                (
                    b"from .io import _regular_absolute_directory, _required_text\n"
                    b"from .models import MapEvidenceProjection\n"
                    b"from .neotoma import _project_neotoma\n"
                    b"from .neotoma_publications import attach_publication_capture\n"
                    b"from .records import _features, _is_unavailable, _tabs\n"
                    b"from .sead import _project_sead\n"
                    b"\n"
                ),
            ),
            (
                (
                    b"def build_map_evidence_projection(\n"
                    b"    context_root: Path,\n"
                    b"    point_layers: Sequence[MutableMapping[str, object]],\n"
                    b") -> MapEvidenceProjection:\n"
                    b'    """Bind governed source evidence to map features through stable record IDs.\n'
                    b"\n"
                ),
                (
                    b"def build_map_evidence_projection(\n"
                    b"    context_root: Path,\n"
                    b"    point_layers: Sequence[MutableMapping[str, object]],\n"
                    b"    *,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> MapEvidenceProjection:\n"
                    b'    """Bind governed source evidence to map features through stable record IDs.\n'
                    b"\n"
                ),
            ),
            (
                (
                    b"            neotoma_accounting,\n"
                    b"            neotoma_source_layers,\n"
                    b"        ) = _project_neotoma(root, neotoma_layer)\n"
                    b"        records.extend(neotoma_records)\n"
                    b'        source_accounting["neotoma"] = neotoma_accounting\n'
                    b"        projected_point_layers.extend(neotoma_source_layers)\n"
                ),
                (
                    b"            neotoma_accounting,\n"
                    b"            neotoma_source_layers,\n"
                    b"        ) = _project_neotoma(root, neotoma_layer)\n"
                    b"        if publication_capture_root is not None:\n"
                    b"            attach_publication_capture(neotoma_records, publication_capture_root)\n"
                    b"        # Source-site links belong to the map publication, not node identity.\n"
                    b"        source_site_urls: dict[str, str] = {}\n"
                    b"        for feature in _features(neotoma_layer):\n"
                    b'            url = feature.get("source_url")\n'
                    b"            if isinstance(url, str) and url.strip():\n"
                    b"                source_site_urls[\n"
                    b'                    _required_text(feature.get("record_id"), "Neotoma site record ID")\n'
                    b"                ] = url\n"
                    b"        for layer in neotoma_source_layers:\n"
                    b"            for feature in _features(layer):\n"
                    b"                url = source_site_urls.get(\n"
                    b'                    _required_text(feature.get("record_id"), "Neotoma source record ID")\n'
                    b"                )\n"
                    b"                if url is not None:\n"
                    b'                    feature["source_url"] = url\n'
                    b"        records.extend(neotoma_records)\n"
                    b'        source_accounting["neotoma"] = neotoma_accounting\n'
                    b"        projected_point_layers.extend(neotoma_source_layers)\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/layers.py": (
        5627,
        "1042f3210ba1b16d7b776370c82470de0d4a320ad99ea7ab1925a4f11a904746",
        "ordinary_original_bytes",
        (
            (
                (
                    b"    atlas_edge_records: Any,\n"
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b") -> tuple[Any, ...]:\n"
                    b"    bundle_paths = build_atlas_bundle_paths_fn(\n"
                    b"        output_dir=staging_output_dir, slug=report.slug, version=version\n"
                    b"    )\n"
                ),
                (
                    b"    atlas_edge_records: Any,\n"
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> tuple[Any, ...]:\n"
                    b'    """Prepare atlas layers and traceable assets with optional publication metadata."""\n'
                    b"    if publication_capture_root is not None and (\n"
                    b"        context_root is None or atlas_detail_records is not None\n"
                    b"    ):\n"
                    b'        raise ValueError("Publication capture requires source-projected atlas details")\n'
                    b"    bundle_paths = build_atlas_bundle_paths_fn(\n"
                    b"        output_dir=staging_output_dir, slug=report.slug, version=version\n"
                    b"    )\n"
                ),
            ),
            (
                (
                    b"    detail_projection_reconciliation = None\n"
                    b"    if context_root is not None and atlas_detail_records is None:\n"
                    b"        detail_projection = surface.build_map_evidence_projection(\n"
                    b"            context_root, point_layers\n"
                    b"        )\n"
                    b"        atlas_detail_records = detail_projection.detail_records\n"
                    b"        detail_projection_reconciliation = detail_projection.reconciliation\n"
                ),
                (
                    b"    detail_projection_reconciliation = None\n"
                    b"    if context_root is not None and atlas_detail_records is None:\n"
                    b"        detail_projection = surface.build_map_evidence_projection(\n"
                    b"            context_root,\n"
                    b"            point_layers,\n"
                    b"            **(\n"
                    b'                {"publication_capture_root": publication_capture_root}\n'
                    b"                if publication_capture_root is not None\n"
                    b"                else {}\n"
                    b"            ),\n"
                    b"        )\n"
                    b"        atlas_detail_records = detail_projection.detail_records\n"
                    b"        detail_projection_reconciliation = detail_projection.reconciliation\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py": (
        4363,
        "1237c261bd34487bbe66efd0fba1f8ea5afa5b0ee81ed91dabe8f033b4b6bce3",
        "runtime_transport_extension",
        (
            (
                (
                    b"    atlas_scientific_signals: Sequence[JsonObject] | None = None,\n"
                    b"    atlas_edge_records: Sequence[JsonObject] | None = None,\n"
                    b"    atlas_sequence_records: Sequence[JsonObject] | None = None,\n"
                    b") -> None:\n"
                    b'    """Write the full atlas bundle into one staging directory."""\n'
                    b"    publish_bundle(\n"
                ),
                (
                    b"    atlas_scientific_signals: Sequence[JsonObject] | None = None,\n"
                    b"    atlas_edge_records: Sequence[JsonObject] | None = None,\n"
                    b"    atlas_sequence_records: Sequence[JsonObject] | None = None,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> None:\n"
                    b'    """Write the full atlas bundle into one staging directory."""\n'
                    b"    publish_bundle(\n"
                ),
            ),
            (
                (
                    b"        atlas_edge_records=atlas_edge_records,\n"
                    b"        atlas_sequence_records=atlas_sequence_records,\n"
                    b"        surface=_surface(),\n"
                    b"    )\n"
                    b"\n"
                    b"\n"
                ),
                (
                    b"        atlas_edge_records=atlas_edge_records,\n"
                    b"        atlas_sequence_records=atlas_sequence_records,\n"
                    b"        surface=_surface(),\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"    )\n"
                    b"\n"
                    b"\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py": (
        4480,
        "ec95b59e5cd910866cc0196d32b983d0e78cc17f22304bf41e84904f58edae2c",
        "runtime_transport_extension",
        (
            (
                (
                    b"    atlas_edge_records: Any,\n"
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b") -> None:\n"
                    b'    """Publish atlas layers, evidence, playback, and inventoried static documents."""\n'
                    b"    (\n"
                ),
                (
                    b"    atlas_edge_records: Any,\n"
                    b"    atlas_sequence_records: Any,\n"
                    b"    surface: Any,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> None:\n"
                    b'    """Publish atlas layers, evidence, playback, and inventoried static documents."""\n'
                    b"    (\n"
                ),
            ),
            (
                (
                    b"        atlas_edge_records=atlas_edge_records,\n"
                    b"        atlas_sequence_records=atlas_sequence_records,\n"
                    b"        surface=surface,\n"
                    b"    )\n"
                    b"    animal_atlas_summary = surface._build_animal_atlas_summary(\n"
                    b"        point_layers,\n"
                ),
                (
                    b"        atlas_edge_records=atlas_edge_records,\n"
                    b"        atlas_sequence_records=atlas_sequence_records,\n"
                    b"        surface=surface,\n"
                    b"        publication_capture_root=publication_capture_root,\n"
                    b"    )\n"
                    b"    animal_atlas_summary = surface._build_animal_atlas_summary(\n"
                    b"        point_layers,\n"
                ),
            ),
        ),
    ),
    "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py": (
        12435,
        "7f44338f73d6efd918f9d82d3e8ba9d686db4cfa92251e3d2446794945a6b6e4",
        "runtime_transport_extension",
        (
            (
                (
                    b"    context_root: Path | None = None,\n"
                    b"    published_output_dir: Path | None = None,\n"
                    b"    geography_scope: GeographicScope | None = None,\n"
                    b") -> MultiCountryMapReport:\n"
                    b'    """Write a shared interactive map for multiple countries with country toggles."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
                (
                    b"    context_root: Path | None = None,\n"
                    b"    published_output_dir: Path | None = None,\n"
                    b"    geography_scope: GeographicScope | None = None,\n"
                    b"    *,\n"
                    b"    publication_capture_root: Path | None = None,\n"
                    b") -> MultiCountryMapReport:\n"
                    b'    """Write a shared interactive map for multiple countries with country toggles."""\n'
                    b"    version_dir = Path(version_dir)\n"
                ),
            ),
            (
                (
                    b"            write_static_map_document_fn=write_static_map_document,\n"
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"        )\n"
                    b"\n"
                    b"    publish_into_staging_dir(output_dir, publish_map_bundle)\n"
                ),
                (
                    b"            write_static_map_document_fn=write_static_map_document,\n"
                    b"            render_multi_country_map_markdown_fn=render_multi_country_map_markdown,\n"
                    b"            write_summary_json_fn=write_summary_json,\n"
                    b"            publication_capture_root=publication_capture_root,\n"
                    b"        )\n"
                    b"\n"
                    b"    publish_into_staging_dir(output_dir, publish_map_bundle)\n"
                ),
            ),
        ),
    ),
}
_RUNTIME_CONTEXT_SOURCES = frozenset(
    (
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/operations_api.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/bundles/atlas_bundle/workflow.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/service.py",
    )
)
ATLAS_CONTEXT_SOURCES = frozenset(_SOURCE_CONTEXT_CONTRACTS)
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


def atlas_context_extension_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Reverse only the named context spans to a complete fixed historical source."""
    contract = _SOURCE_CONTEXT_CONTRACTS.get(name)
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
    if composition == "runtime_transport_extension":
        return (
            name in _RUNTIME_CONTEXT_SOURCES
            and atlas_runtime_transport_extension_matches(name, captured, restored)
        )
    return False


def validated_atlas_context_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate changed source-view semantics without retagging native outputs."""
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    name = historical.get("path")
    contract = _SOURCE_CONTEXT_CONTRACTS.get(name) if isinstance(name, str) else None
    if not isinstance(name, str) or contract is None:
        raise ReportRebuildError("Unknown source-view context source")
    size, digest, composition, _ = contract
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
        raise ReportRebuildError("Source-view context binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    current_path = _regular_confined_file(
        repository,
        name,
        "current source-view context",
    )
    before = current_path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 64 * 1024:
        raise ReportRebuildError("Source-view context source is linked or unbounded")
    current = current_path.read_bytes()
    if not atlas_context_extension_matches(name, captured, current):
        raise ReportRebuildError(
            "Source-view context differs beyond its declared extension"
        )
    source_buffer.fresh()
    again = _regular_confined_file(
        repository,
        name,
        "current source-view context",
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
        raise ReportRebuildError("Source-view context changed during verification")
    return {
        "path": name,
        "classification": "source_view_context_extension",
        "original_member": logical,
        "original_bytes": size,
        "original_sha256": digest,
        "whole_old_module_reconstructed": True,
        "preexisting_source_correspondence": composition,
        "runtime_transport_law_composed": composition == "runtime_transport_extension",
        "historical_native_equal_current_output_claimed": False,
        "historical_browser_equal_current_browser_claimed": False,
        "current_runtime_transport_byte_equal_claimed": False,
        "all_other_old_source_bytes_exact": True,
        "current_regular_single_link_and_stable": True,
        "source_projection_metadata_and_refusals_intentionally_extended": True,
        "all_current_source_projection_outputs_equal_claimed": False,
        "optional_publication_input_default": None,
        "publication_capture_epoch": "neotoma/publication-links/2026-09-29",
        "publication_capture_is_original_pollen_epoch_claimed": False,
        "historical_outputs_revalidated_under_current_contract_claimed": False,
        "old_native_equal_current_admission_claimed": False,
        "new_native_or_scientific_execution_claimed": False,
    }
