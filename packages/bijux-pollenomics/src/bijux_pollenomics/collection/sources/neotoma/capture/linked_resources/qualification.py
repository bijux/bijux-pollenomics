"""Derive native detail qualifications beside immutable source capture ledgers."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..facets.models import NeotomaFacetScopeInputs
from ..resources.models import (
    DEFAULT_RESOURCE_LIMITS,
    DEVELOPMENT_ROLES,
    NeotomaResourceLimits,
)
from . import replay as replay_owner
from .models import SCOPED_LINKED_SCHEMA, NeotomaLinkedEvidence
from .profiles import (
    _UnavailableLinkedSource,
    parse_neotoma_linked_source,
    summarize_linked_source,
)
from .replay import _control, _read_linked_entry_body


def qualify_neotoma_linked_capture(
    directory: Path,
    *,
    expected_manifest_sha256: str,
    source_facets: Mapping[str, Path],
    limits: NeotomaResourceLimits = DEFAULT_RESOURCE_LIMITS,
    scope_inputs: Mapping[str, NeotomaFacetScopeInputs] | None = None,
    evidence: NeotomaLinkedEvidence | None = None,
    legacy_rosters: Mapping[str, Path] | None = None,
) -> dict[str, Any]:
    """Authenticate exact returned buffers and every root occurrence before parsing."""
    captured = replay_owner.replay_neotoma_linked_resources(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        source_facets=source_facets,
        scope_inputs=scope_inputs,
        limits=limits,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
    )
    manifest, _, _, _, _ = _control(directory, expected_manifest_sha256)
    scoped = manifest["schema_version"] == SCOPED_LINKED_SCHEMA
    rows = []
    for entry in captured.resources:
        identity = entry["identity"]
        row: dict[str, Any] = {
            "target_key": entry["target_key"],
            "source_terminal_status": entry["terminal_status"],
            "scientific_admission": "not_asserted",
        }
        if scoped:
            row["source_proof_reference"] = identity["source_proof_reference"]
            row["source_evidence"] = manifest["source_evidence"]
        else:
            row["source_proofs"] = identity["source_proofs"]
        rows.append(row)
        if identity["exposure_role"] not in DEVELOPMENT_ROLES:
            row["qualification_status"] = "not_qualified_exposure_role"
            continue
        if entry["terminal_status"] != "received_complete_unqualified_linked_resource":
            row["qualification_status"] = "not_qualified_source_result"
            continue
        body = _read_linked_entry_body(directory, entry, limits, evidence=evidence)
        if not scoped:
            row["source_proofs"] = list(body.source_proofs)
        reference = entry["attempts"][-1]
        row["source"] = {
            "capture_manifest_sha256": captured.manifest_sha256,
            "target_key": body.target_key,
            "content_version": "current",
            "api_version": "v2.0",
            "receipt_file": reference["receipt_file"],
            "receipt_sha256": body.receipt_sha256,
            "body_file": reference["body_file"],
            "body_sha256": body.body_sha256,
        }
        try:
            parsed = parse_neotoma_linked_source(
                identity, body.body, expected_body_sha256=body.body_sha256
            )
            row.update(
                qualification_status="parsed_linked_source",
                summary=summarize_linked_source(
                    parsed, source_proofs=list(body.source_proofs)
                ),
            )
        except _UnavailableLinkedSource as error:
            row.update(
                qualification_status="unavailable_linked_api_empty",
                reason=str(error),
                absence_certified=False,
            )
        except ValueError as error:
            row.update(qualification_status="refused_linked_source", reason=str(error))
    replay_owner.replay_neotoma_linked_resources(
        directory,
        expected_manifest_sha256=expected_manifest_sha256,
        source_facets=source_facets,
        scope_inputs=scope_inputs,
        limits=limits,
        evidence=evidence,
        legacy_rosters=legacy_rosters,
    )
    return {
        "schema_version": "neotoma-scoped-linked-source-qualification.v1"
        if scoped
        else "neotoma-linked-source-qualification.v1",
        "source_capture_manifest_sha256": captured.manifest_sha256,
        "source_capture_relabelled": False,
        "resources": rows,
        "partitions": dict(
            sorted(Counter(row["qualification_status"] for row in rows).items())
        ),
        "scope": "selected native detail targets; no complete people/publication/taxonomy population claim",
        "HTTP_requests": 0,
        "scientific_admission": "not_asserted",
    }
