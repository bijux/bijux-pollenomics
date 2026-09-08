"""Atomic materialization of source-native chronology nodes."""

from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics.analysis.propagation.outputs.codec import (
    _canonical_json_bytes,
)
from bijux_pollenomics.analysis.propagation.outputs.publication import (
    _publish_atomically,
    _validate_output_location,
)

from .constants import source_node_config_payload
from .models import SourceNodeDerivationResult, SourceNodeMaterializationResult


def _payloads(result: SourceNodeDerivationResult) -> dict[str, bytes]:
    identity = {
        "source_snapshot_id": result.context.source_snapshot_id,
        "build_id": result.context.build_id,
        "config_digest": result.context.config_digest,
        "config": source_node_config_payload(),
        "producer_version": result.context.producer_version,
        "result_digest": result.result_digest,
    }
    payloads: dict[str, dict[str, object]] = {
        "chronology_nodes.json": {
            "schema_version": "neotoma-source-chronology-nodes-artifact.v2",
            **identity,
            "record_count": len(result.nodes),
            "records": [node.as_dict() for node in result.nodes],
        },
        "admission_refusals.json": {
            "schema_version": "neotoma-source-node-admission-refusals.v1",
            **identity,
            "record_count": len(result.admission_refusals),
            "records": [row.as_dict() for row in result.admission_refusals],
        },
        "facet_refusals.json": {
            "schema_version": "neotoma-source-node-facet-refusals.v1",
            **identity,
            "record_count": len(result.facet_refusals),
            "records": [row.as_dict() for row in result.facet_refusals],
        },
        "reconciliation.json": {
            "schema_version": "neotoma-source-node-reconciliation.v2",
            **identity,
            "record_count": 1,
            "context": result.context.as_dict(),
            "derivation_status": result.derivation_status,
            "result_digest": result.result_digest,
            "candidate_generation_status": "refused",
            "propagation_eligible_event_count": 0,
            "reconciliation": result.reconciliation.as_dict(),
        },
    }
    return {name: _canonical_json_bytes(payload) for name, payload in payloads.items()}


def materialize_source_chronology_nodes(
    result: SourceNodeDerivationResult,
    *,
    output_root: Path,
    allowed_output_parent: Path,
) -> SourceNodeMaterializationResult:
    """Atomically publish nodes and exact refusal/accounting partitions."""
    output_root = Path(output_root)
    allowed_output_parent = Path(allowed_output_parent)
    _validate_output_location(output_root, allowed_output_parent)
    payloads = _payloads(result)
    manifest = {
        "schema_version": "neotoma-source-chronology-node-manifest.v2",
        "source_snapshot_id": result.context.source_snapshot_id,
        "build_id": result.context.build_id,
        "config_digest": result.context.config_digest,
        "config": source_node_config_payload(),
        "producer_version": result.context.producer_version,
        "result_digest": result.result_digest,
        "chronology_node_count": len(result.nodes),
        "propagation_eligible_event_count": 0,
        "payload_file_count": len(payloads),
        "files": [
            {
                "path": name,
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
            for name, payload in sorted(payloads.items())
        ],
    }
    manifest_bytes = _canonical_json_bytes(manifest)
    expected_files = {**payloads, "manifest.json": manifest_bytes}
    disposition = _publish_atomically(
        output_root=output_root,
        allowed_output_parent=allowed_output_parent,
        expected_files=expected_files,
    )
    return SourceNodeMaterializationResult(
        output_root=str(output_root),
        disposition=disposition,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        file_count=len(expected_files),
        chronology_node_count=len(result.nodes),
    )


__all__ = ["materialize_source_chronology_nodes"]
