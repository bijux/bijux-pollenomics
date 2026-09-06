"""Deterministic materialization of static atlas manifests and chunks."""

from __future__ import annotations

import base64
from collections.abc import Sequence
import hashlib
from pathlib import Path

from ....core.geospatial.geojson import JsonObject
from ..evidence import normalize_atlas_evidence, validate_feature_signal_references
from .asset_inventory import encode_asset_inventory
from .budgets import (
    ATLAS_BOOTSTRAP_MAX_BYTES,
    ATLAS_CHUNK_MAX_BYTES,
    ATLAS_DETAIL_CHUNK_TARGET_BYTES,
    ATLAS_DOCUMENT_MAX_BYTES,
    ATLAS_FILTER_MAIN_THREAD_MAX_MS,
    ATLAS_INITIAL_MAX_BYTES,
    ATLAS_INITIAL_MAX_REQUESTS,
    ATLAS_INTERACTION_MAX_BYTES,
    ATLAS_INTERACTION_MAX_REQUESTS,
    ATLAS_STATIC_ASSETS_MAX_BYTES,
    ATLAS_STATIC_ASSETS_MAX_FILES,
)
from .index_bundles import INDEX_BUNDLE_SCHEMA, build_index_bundle
from .indexes import build_indexes, index_reference_count
from .models import StaticAtlasAssets, validate_atlas_release_id
from .nodes import (
    build_node_payloads,
    node_asset_selection,
    node_payload_record_count,
    partition_features,
)
from .serialization import (
    canonical_json,
    chunk_script_bytes,
    validate_decoded_payload_size,
    write_immutable,
)
from .validation import validate_static_atlas_assets


def write_static_atlas_assets(
    output_dir: Path,
    *,
    slug: str,
    version: str,
    point_layers: Sequence[JsonObject],
    polygon_layers: Sequence[JsonObject],
    detail_records: Sequence[JsonObject] | None = None,
    scientific_signals: Sequence[JsonObject] | None = None,
    edge_records: Sequence[JsonObject] | None = None,
    sequence_records: Sequence[JsonObject] | None = None,
) -> StaticAtlasAssets:
    """Write deterministic hashed map chunks and their small bootstrap manifest."""
    output_dir = Path(output_dir)
    if not output_dir.is_dir() or output_dir.is_symlink():
        raise ValueError("static atlas output directory must be an existing directory")
    if not slug or Path(slug).name != slug or not slug.replace("-", "").isalnum():
        raise ValueError("static atlas slug must be a safe filename component")
    validate_atlas_release_id(version)

    evidence = normalize_atlas_evidence(
        detail_records=detail_records,
        scientific_signals=scientific_signals,
        edge_records=edge_records,
        sequence_records=sequence_records,
    )
    validate_feature_signal_references(point_layers, evidence.scientific_signals)

    layer_metadata, node_payloads = build_node_payloads(
        slug=slug,
        version=version,
        point_layers=point_layers,
        polygon_layers=polygon_layers,
    )
    detail_partitions = partition_features(
        [dict(record) for record in evidence.detail_records],
        target_bytes=ATLAS_DETAIL_CHUNK_TARGET_BYTES,
    )
    first_detail_sequence = 1 + len(node_payloads)
    detail_asset_keys = [
        f"details:{first_detail_sequence + index}"
        for index in range(len(detail_partitions))
    ]
    indexes = {
        **build_indexes(point_layers),
        "detail_record_asset_keys": {
            str(record["record_id"]): asset_key
            for asset_key, partition in zip(
                detail_asset_keys, detail_partitions, strict=True
            )
            for record in partition
        },
    }
    build_id = (
        "atlas-"
        + hashlib.sha256(
            canonical_json(
                {
                    "scope_slug": slug,
                    "version": version,
                    "layer_metadata": layer_metadata,
                    "node_payloads": node_payloads,
                    "indexes": indexes,
                    "detail_records": evidence.detail_records,
                    "scientific_signals": evidence.scientific_signals,
                    "edge_records": evidence.edge_records,
                    "sequence_records": evidence.sequence_records,
                }
            ).encode("utf-8")
        ).hexdigest()
    )
    payloads: list[tuple[str, int, dict[str, object]]] = [
        (
            "provenance",
            len(layer_metadata),
            {
                "schema_version": "atlas-provenance-chunk.v3",
                "scope_slug": slug,
                "version": version,
                "build_id": build_id,
                "status": (
                    "record_level_available"
                    if evidence.detail_records
                    else "layer_metadata_only"
                ),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_provenance_model_not_available"
                ),
                "layers": layer_metadata,
                "scientific_signals": list(evidence.scientific_signals),
                "details_status": (
                    "available" if evidence.detail_records else "unavailable"
                ),
                "details_reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_evidence_not_available"
                ),
                "classifications_status": (
                    "available" if evidence.scientific_signals else "unavailable"
                ),
                "classifications_reason_code": (
                    None
                    if evidence.scientific_signals
                    else "accepted_scientific_classifications_not_available"
                ),
            },
        )
    ]
    payloads.extend(
        ("nodes", node_payload_record_count(payload), payload)
        for payload in node_payloads
    )
    payloads.extend(
        (
            "details",
            len(partition),
            {
                "schema_version": "atlas-details-chunk.v1",
                "scope_slug": slug,
                "version": version,
                "build_id": build_id,
                "records": partition,
            },
        )
        for partition in detail_partitions
    )
    for domain, records, reason_code in (
        ("edges", evidence.edge_records, "governed_map_edge_model_not_available"),
        (
            "sequences",
            evidence.sequence_records,
            "governed_sequence_detail_model_not_available",
        ),
    ):
        payloads.append(
            (
                domain,
                len(records),
                {
                    "schema_version": f"atlas-{domain}-chunk.v1",
                    "scope_slug": slug,
                    "version": version,
                    "build_id": build_id,
                    "status": "available" if records else "unavailable",
                    "reason_code": None if records else reason_code,
                    "records": list(records),
                },
            )
        )
    logical_indexes = {
        **indexes,
        "scope_slug": slug,
        "version": version,
        "build_id": build_id,
    }
    payloads.append(
        (
            "indexes",
            index_reference_count(logical_indexes),
            build_index_bundle(logical_indexes),
        )
    )

    assets: list[dict[str, object]] = []
    asset_paths: list[Path] = []
    for sequence, (domain, record_count, source_payload) in enumerate(payloads):
        asset_key = f"{domain}:{sequence}"
        payload = {**source_payload, "build_id": build_id, "asset_key": asset_key}
        payload_json = canonical_json(payload)
        validate_decoded_payload_size(payload_json, asset_key=asset_key)
        payload_sha256 = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        payload_encoding = (
            "gzip_base64" if domain in {"nodes", "details", "provenance"} else "json"
        )
        script_bytes = chunk_script_bytes(
            asset_key=asset_key,
            payload_sha256=payload_sha256,
            payload_json=payload_json,
            payload_encoding=payload_encoding,
        )
        digest = hashlib.sha256(script_bytes).hexdigest()
        filename = f"{slug}.atlas-{domain}.{sequence:04d}.{digest[:16]}.js"
        path = output_dir / filename
        write_immutable(path, script_bytes)
        row: dict[str, object] = {
            "asset_key": asset_key,
            "domain": domain,
            "sequence": sequence,
            "path": filename,
            "sha256": digest,
            "integrity": "sha256-"
            + base64.b64encode(hashlib.sha256(script_bytes).digest()).decode("ascii"),
            "payload_sha256": payload_sha256,
            "payload_encoding": payload_encoding,
            "decoded_byte_count": len(payload_json.encode("utf-8")),
            "byte_count": len(script_bytes),
            "record_count": record_count,
            "initial_load": domain not in {"nodes", "details", "indexes"},
        }
        if domain == "nodes":
            row.update(node_asset_selection(payload))
        assets.append(row)
        asset_paths.append(path)

    manifest: dict[str, object] = {
        "schema_version": "atlas-static-bootstrap.v2",
        "scope_slug": slug,
        "version": version,
        "build_id": build_id,
        "load_strategy": "selection_aware_static_scripts",
        "offline_file_compatible": True,
        "transport_integrity": {
            "http_https": "subresource_integrity_plus_payload_sha256",
            "file": "payload_sha256_after_script_registration",
            "file_pre_execution_sri": False,
        },
        "compatibility": {
            "provenance_schema": "atlas-provenance-chunk.v3",
            "node_schema": "atlas-node-chunk.v1",
            "detail_schema": "atlas-details-chunk.v1",
            "edge_schema": "atlas-edges-chunk.v1",
            "sequence_schema": "atlas-sequences-chunk.v1",
            "index_schema": INDEX_BUNDLE_SCHEMA,
        },
        "budgets": {
            "bootstrap_max_bytes": ATLAS_BOOTSTRAP_MAX_BYTES,
            "chunk_max_bytes": ATLAS_CHUNK_MAX_BYTES,
            "document_max_bytes": ATLAS_DOCUMENT_MAX_BYTES,
            "static_assets_max_bytes": ATLAS_STATIC_ASSETS_MAX_BYTES,
            "static_assets_max_files": ATLAS_STATIC_ASSETS_MAX_FILES,
            "initial_max_requests": ATLAS_INITIAL_MAX_REQUESTS,
            "initial_max_bytes": ATLAS_INITIAL_MAX_BYTES,
            "interaction_max_requests": ATLAS_INTERACTION_MAX_REQUESTS,
            "interaction_max_bytes": ATLAS_INTERACTION_MAX_BYTES,
            "filter_main_thread_max_ms": ATLAS_FILTER_MAIN_THREAD_MAX_MS,
        },
        "domains": {
            "nodes": {
                "status": "available",
                "record_count": sum(
                    node_payload_record_count(payload) for payload in node_payloads
                ),
            },
            "edges": {
                "status": "available" if evidence.edge_records else "unavailable",
                "record_count": len(evidence.edge_records),
                "reason_code": (
                    None
                    if evidence.edge_records
                    else "governed_map_edge_model_not_available"
                ),
            },
            "sequences": {
                "status": "available" if evidence.sequence_records else "unavailable",
                "record_count": len(evidence.sequence_records),
                "reason_code": (
                    None
                    if evidence.sequence_records
                    else "governed_sequence_detail_model_not_available"
                ),
            },
            "provenance": {
                "status": (
                    "record_level_available"
                    if evidence.detail_records
                    else "layer_metadata_only"
                ),
                "record_count": (
                    len(evidence.detail_records)
                    if evidence.detail_records
                    else len(layer_metadata)
                ),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_provenance_model_not_available"
                ),
            },
            "details": {
                "status": "available" if evidence.detail_records else "unavailable",
                "record_count": len(evidence.detail_records),
                "reason_code": (
                    None
                    if evidence.detail_records
                    else "record_level_evidence_not_available"
                ),
            },
            "classifications": {
                "status": (
                    "available" if evidence.scientific_signals else "unavailable"
                ),
                "record_count": len(evidence.scientific_signals),
                "reason_code": (
                    None
                    if evidence.scientific_signals
                    else "accepted_scientific_classifications_not_available"
                ),
            },
            "indexes": {
                "status": "available",
                "record_count": index_reference_count(logical_indexes),
            },
        },
        "assets": encode_asset_inventory(assets, scope_slug=slug),
    }
    manifest_bytes = (canonical_json(manifest) + "\n").encode("utf-8")
    if len(manifest_bytes) > ATLAS_BOOTSTRAP_MAX_BYTES:
        raise ValueError("static atlas bootstrap exceeds its byte budget")
    manifest_path = output_dir / f"{slug}_map_assets.json"
    manifest_path.write_bytes(manifest_bytes)
    result = StaticAtlasAssets(
        manifest_path=manifest_path,
        manifest=manifest,
        asset_paths=tuple(asset_paths),
    )
    validate_static_atlas_assets(result)
    return result


__all__ = ["write_static_atlas_assets"]
