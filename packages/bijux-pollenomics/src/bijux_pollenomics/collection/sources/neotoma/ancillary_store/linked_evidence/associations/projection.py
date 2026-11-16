"""Join complete later source occurrences to unchanged legacy global observations."""

from __future__ import annotations

from typing import Any

from ....capture.linked_resources.evidence import read_neotoma_linked_evidence_metadata
from ....capture.linked_resources.models import LINKED_SCHEMA, NeotomaLinkedEvidence
from ....capture.receipts import _object, _safe_root
from ....resource_catalogue.source_projection import _same
from ...selection.access import _observation, _prepare, _response, _source
from ...selection.metadata import SelectedMetadata, pinned
from ...selection.scope import CurrentScope
from ..sources import read_scoped_target
from .models import MAX_TARGETS, SCHEMA, NeotomaLinkedAssociationInputs


def prepare(
    evidence: NeotomaLinkedEvidence, inputs: NeotomaLinkedAssociationInputs
) -> tuple[SelectedMetadata, CurrentScope, dict[str, Any], dict[str, Any]]:
    """Bind dated evidence owners to independently fresh complete root metadata."""
    metadata, scope = _prepare(inputs.federation_directory, inputs.selection_kwargs())
    header = read_neotoma_linked_evidence_metadata(
        evidence.directory, expected_manifest_sha256=evidence.manifest_sha256
    )
    current = scope.linked_metadata()
    if header["authority"]["roster_sha256"] != scope.roster_pin:
        raise ValueError("Association evidence current roster differs")
    roots = header["authority"]["root_identities"]
    fields = ("dataset_id", "site_id", "collection_unit_id", "dataset_type", "database")
    if set(roots) != {str(key) for key in current["roots"]} or any(
        not _same(
            {field: original[field] for field in fields},
            {field: current["roots"][int(key)][field] for field in fields},
        )
        for key, original in roots.items()
    ):
        raise ValueError("Association evidence complete native root population differs")
    return metadata, scope, header, current


def project_target(
    observation: dict[str, Any],
    evidence: NeotomaLinkedEvidence,
    metadata: SelectedMetadata,
    scope: CurrentScope,
    header: dict[str, Any],
    current: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Derive one exact target; no global entity or native witness body is opened."""
    from ....capture.linked_resources.protocol import request_for

    capture, entry = _source(metadata, observation, "linked")
    if capture["document"]["schema_version"] != LINKED_SCHEMA:
        raise ValueError("Later association requires an unchanged legacy capture")
    original = entry["identity"]
    key = f"{original['kind']}-{original['native_id']}"
    target = header["targets"].get(key)
    if target is None:
        raise ValueError("Retained global entity has no current evidence target")
    identity = {
        "target_key": key,
        "kind": target["kind"],
        "native_id": target["native_id"],
        "exposure_role": target["exposure_role"],
        "source_proof_reference": {
            "target_key": key,
            "occurrence_count": target["occurrence_count"],
            "proof_ranges": target["proof_ranges"],
        },
        "metadata_dependency_count": len(target["metadata_dependencies"]),
    }
    selected = read_scoped_target(evidence, identity, current, attempted=False)
    # The dated inline obligations still apply even if later source occurrence sets differ.
    old_proofs = original["source_proofs"]
    all_proofs = [*old_proofs, *selected["source_proofs"]]
    from ....capture.linked_resources.protocol import _RANK

    for proof in all_proofs:
        root = proof["root_dataset_id"]
        if (
            root not in current["roots"]
            or root not in current["roles"]
            or not _same(proof["root_identity"], current["roots"][root])
        ):
            raise ValueError("Retained association current root differs")
    roles = [current["roles"][proof["root_dataset_id"]] for proof in all_proofs]
    role = max([selected["current_use_role"], *roles], key=_RANK.__getitem__)
    attempt = entry["attempts"][-1] if entry["attempts"] else None
    retained = None
    if attempt is not None and "body_file" in attempt:
        receipt, _ = _response(
            metadata,
            capture,
            entry,
            request_for(original, len(entry["attempts"])),
            observation,
        )
        retained = {
            "observation_id": observation["observation_id"],
            "capsule_manifest_sha256": observation["capsule_manifest_sha256"],
            "capture_manifest_sha256": observation["source_capture_manifest_sha256"],
            "resource_key": key,
            "receipt_file": attempt["receipt_file"],
            "receipt_sha256": attempt["receipt_sha256"],
            "body_file": attempt["body_file"],
            "body_sha256": receipt["retained_body_sha256"],
            "body_bytes": receipt["retained_body_bytes"],
            "utc_start": receipt["utc_start"],
            "utc_end": receipt["utc_end"],
            "http_status": receipt["http_status"],
            "body_complete": receipt["body_complete"],
        }
    overlaps = [
        any(_same(proof, old) for old in old_proofs)
        for proof in selected["source_proofs"]
    ]
    row = {
        "target_key": key,
        "kind": original["kind"],
        "native_id": original["native_id"],
        "retained_entity": retained,
        "observation_id": observation["observation_id"],
        "source_proof_reference": identity["source_proof_reference"],
        "current_use_role": role,
        "old_inline_occurrences": len(old_proofs),
        "exact_old_current_overlaps": sum(overlaps),
        "later_associations": len(overlaps) - sum(overlaps),
        "later_example_locator": next(
            (
                locator
                for locator, overlap in zip(
                    selected["proof_locators"], overlaps, strict=True
                )
                if not overlap
            ),
            None,
        ),
        "capture_preget_scope": "not_recorded_legacy_capture",
        "original_source_scope_verification": observation[
            "capture_parent_scope_verification"
        ],
        "association_scope": "later_source_occurrences_current_use",
        "native_field_value_verified": False,
        "native_entity_owner_verified": False,
        "original_preget_scope_reconstructed": False,
        "scientific_admission": "not_asserted",
    }
    return row, selected


def build_neotoma_linked_associations(
    evidence: NeotomaLinkedEvidence, *, inputs: NeotomaLinkedAssociationInputs
) -> dict[str, Any]:
    """Reconcile every legacy global observation against the complete anchored state."""
    metadata, scope, header, current = prepare(evidence, inputs)
    observations = []
    for capsule_pin, captures in metadata.manifest["capsule_captures"].items():
        if capsule_pin not in inputs.capsule_sources:
            raise ValueError("Association capsule resolver is missing")
        root = _safe_root(inputs.capsule_sources[capsule_pin])
        capsule = _object(pinned(root / "manifest.json", capsule_pin))
        declarations = capsule.get("captures")
        if not isinstance(declarations, dict) or set(declarations) != set(captures):
            raise ValueError("Association complete capsule capture inventory differs")
        for digest, descriptor in declarations.items():
            if not isinstance(descriptor, dict) or descriptor.get("kind") not in {
                "facet",
                "linked",
            }:
                raise ValueError("Association capture kind is malformed")
            if descriptor["kind"] != "linked":
                continue
            capture = metadata.capture(digest, "linked")
            if capture["document"]["schema_version"] != LINKED_SCHEMA:
                continue
            for offset in range(len(capture["document"]["resources"])):
                observations.append(
                    _observation(metadata, f"{digest}:/resources/{offset}", "linked")
                )
                if len(observations) > MAX_TARGETS:
                    raise ValueError(
                        "Retained association target population exceeds bound"
                    )
    rows: list[dict[str, Any]] = []
    seen = set()
    for observation in observations:
        capture, _ = _source(metadata, observation, "linked")
        if capture["document"]["schema_version"] != LINKED_SCHEMA:
            continue
        row, _ = project_target(observation, evidence, metadata, scope, header, current)
        if row["target_key"] in seen or len(rows) >= MAX_TARGETS:
            raise ValueError(
                "Retained association target population is ambiguous or excessive"
            )
        seen.add(row["target_key"])
        rows.append(row)
    rows.sort(key=lambda row: row["target_key"])
    summary = {
        "targets": len(rows),
        "current_occurrences": sum(
            row["source_proof_reference"]["occurrence_count"] for row in rows
        ),
    }
    for field in (
        "old_inline_occurrences",
        "exact_old_current_overlaps",
        "later_associations",
    ):
        summary[field] = sum(row[field] for row in rows)
    return {
        "schema_version": SCHEMA,
        "anchors": inputs.anchors(evidence.manifest_sha256),
        "targets": rows,
        "summary": summary,
        "integrity_scope": "complete_legacy_target_metadata_and_current_evidence_occurrences",
        "entity_bodies_verified": False,
        "native_field_values_verified": False,
        "original_preget_scope_reconstructed": False,
        "scientific_admission": "not_asserted",
    }
