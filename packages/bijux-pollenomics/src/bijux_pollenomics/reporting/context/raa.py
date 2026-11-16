"""Capture RAÄ Atlas status and normalized display bytes from one input epoch."""

from __future__ import annotations

from contextlib import ExitStack
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path

from ...collection.sources.raa.authority import (
    RaaDensityAuthorityDecision,
    capture_raa_authority_snapshot,
)
from ...collection.sources.raa.authority_inputs import INPUT_PATHS
from ...collection.sources.raa.inventory import decode_source_object, non_negative_count
from ...core.filesystem import BoundedInputTree
from ...core.geospatial.geojson import as_mapping

RAA_ATLAS_INPUT_STATUS_FILENAME = "raa_atlas_input_status.json"
RAA_ATLAS_INPUT_STATUS_LABEL = "RAÄ atlas input status"
RAA_V018_COMMIT = "f5ab77edcd3affee65723074d21b83161b4bf542"
RAA_V018_DENSITY_SHA256 = (
    "acac7a952dc31be8b988ecb35386c877628e2580fae427f32281310635489d20"
)
RAA_V018_METADATA_SHA256 = (
    "baa5f7ec34e290d5b52ad93afb8a05e77830bd2b2672a15a579e571f5f6d91d8"
)

RAA_CONTEXT_RELATIVE_DIRECTORY = Path("context/raa")
_AUTHORITY_INPUTS = INPUT_PATHS


@dataclass(frozen=True)
class RaaAtlasInputSnapshot:
    """Immutable public buffers and status for one captured input epoch."""

    status_bytes: bytes
    metadata_bytes: bytes | None
    density_bytes: bytes | None

    def __post_init__(self) -> None:
        """Keep each public buffer within the explicit publication byte ceiling."""
        for raw in (self.status_bytes, self.metadata_bytes, self.density_bytes):
            if raw is not None and (type(raw) is not bytes or len(raw) > 1024 * 1024):
                raise ValueError("RAÄ public snapshot requires bounded immutable bytes")

    def status(self) -> dict[str, object]:
        """Decode a fresh status view without reopening source paths."""
        return decode_source_object(self.status_bytes.decode("utf-8"))


def build_raa_atlas_input_status(context_root: Path) -> dict[str, object]:
    """Describe a captured input epoch, not the future state of its source paths."""
    return capture_raa_atlas_input_snapshot(context_root).status()


def capture_raa_atlas_input_snapshot(context_root: Path) -> RaaAtlasInputSnapshot:
    """Capture authority payloads or a separate bounded historical display pair."""
    context_root = Path(context_root).absolute()
    captured = capture_raa_authority_snapshot(context_root)
    authority = captured.decision
    receipts = {record.role: record.payload() for record in captured.input_receipts}
    metadata_bytes, density_bytes = captured.metadata_bytes, captured.density_bytes
    if metadata_bytes is None or density_bytes is None:
        metadata_bytes, density_bytes, pair_receipts = _capture_normalized_pair(
            context_root
        )
        receipts.update(pair_receipts)
    inputs = {
        name: {
            "path": relative,
            "present": name in receipts or (context_root / relative).is_file(),
            "sha256": receipts[name]["sha256"] if name in receipts else None,
            "byte_count": receipts[name]["byte_count"] if name in receipts else None,
            "receipt_status": "captured_bytes" if name in receipts else "presence_only",
        }
        for name, relative in _AUTHORITY_INPUTS.items()
    }
    status = _build_status(authority, inputs, metadata_bytes, density_bytes)
    return RaaAtlasInputSnapshot(
        json.dumps(status, indent=2, ensure_ascii=False).encode("utf-8"),
        metadata_bytes,
        density_bytes,
    )


def _capture_normalized_pair(
    root: Path,
) -> tuple[bytes | None, bytes | None, dict[str, dict[str, object]]]:
    roles = ("normalized_metadata", "normalized_density")
    try:
        with ExitStack() as stack:
            trees = {}
            for role in roles:
                path = root / _AUTHORITY_INPUTS[role]
                trees[role] = stack.enter_context(
                    BoundedInputTree(
                        path.parent,
                        max_bytes=1024 * 1024,
                        max_files=1,
                        selected=path.name,
                    )
                )
            buffers = {
                role: tree.read(root / _AUTHORITY_INPUTS[role], max_bytes=1024 * 1024)
                for role, tree in trees.items()
            }
            for tree in trees.values():
                tree.validate()
            for tree in trees.values():
                tree.check()
            receipts = {
                role: {
                    "path": _AUTHORITY_INPUTS[role],
                    "sha256": sha256(raw).hexdigest(),
                    "byte_count": len(raw),
                }
                for role, raw in buffers.items()
            }
            return buffers[roles[0]], buffers[roles[1]], receipts
    except (OSError, ValueError):
        return None, None, {}


def _build_status(
    authority: RaaDensityAuthorityDecision,
    inputs: dict[str, dict[str, object]],
    metadata_bytes: bytes | None,
    density_bytes: bytes | None,
) -> dict[str, object]:
    retained_normalized_input = bool(
        inputs["normalized_metadata"]["present"]
        or inputs["normalized_density"]["present"]
    )
    retained_density_pair = bool(
        inputs["normalized_metadata"]["present"]
        and inputs["normalized_density"]["present"]
    )
    retained_v018_surface = bool(
        retained_density_pair
        and inputs["normalized_metadata"]["sha256"] == RAA_V018_METADATA_SHA256
        and inputs["normalized_density"]["sha256"] == RAA_V018_DENSITY_SHA256
    )
    density_count_accounting = (
        _density_count_accounting(metadata_bytes, density_bytes, authority)
        if retained_density_pair
        else None
    )
    display_warning_codes: list[str] = []
    if retained_density_pair and not authority.admitted and not retained_v018_surface:
        display_warning_codes.append("retained_context_identity_mismatch")
    if (
        density_count_accounting is not None
        and density_count_accounting["reconciled"] is False
    ):
        display_warning_codes.append("retained_density_metadata_count_mismatch")
    degraded_context_enabled = retained_v018_surface and not authority.admitted
    atlas_input_status = (
        "admitted"
        if authority.admitted
        else "degraded"
        if retained_normalized_input
        else "refused"
    )
    sweden_availability_status = (
        "available_collected"
        if inputs["normalized_metadata"]["present"]
        and inputs["normalized_density"]["present"]
        else "available_partial"
        if retained_normalized_input
        else "unknown"
    )
    review_only_reason_codes = {
        "missing_scientific_review",
        "scientific_review_not_accepted",
    }
    lifecycle_status = (
        "admitted"
        if authority.admitted
        else "review_required"
        if authority.reason_codes
        and set(authority.reason_codes).issubset(review_only_reason_codes)
        else "refused"
    )
    return {
        "schema_version": "raa-atlas-input-status.v1",
        "status_namespace": "raa_atlas_input_availability",
        "input_epoch": "captured_buffers; source paths may subsequently change",
        "status_namespace_note": (
            "Atlas-input rendering state only; not country/source availability, "
            "external-intake lifecycle, backlog status, or release state."
        ),
        "atlas_input_status": atlas_input_status,
        "reason_codes": list(authority.reason_codes),
        "source_authority": "Riksantikvarieämbetet",
        "source_family": "raa",
        "evidence_role": "archaeology_context_only",
        "country_scope": {
            "Sweden": "source_coverage",
            "Denmark": "outside_source_scope",
            "Finland": "outside_source_scope",
            "Norway": "outside_source_scope",
        },
        "country_source_coverage": {
            "Sweden": {
                "availability_status": sweden_availability_status,
                "lifecycle_status": lifecycle_status,
                "fact_basis": "governed_assignment",
            },
            "Denmark": {
                "availability_status": "not_applicable",
                "lifecycle_status": "not_required",
                "fact_basis": "governed_assignment",
            },
            "Finland": {
                "availability_status": "not_applicable",
                "lifecycle_status": "not_required",
                "fact_basis": "governed_assignment",
            },
            "Norway": {
                "availability_status": "not_applicable",
                "lifecycle_status": "not_required",
                "fact_basis": "governed_assignment",
            },
        },
        "chronology_posture": "no_repository_owned_time_windows",
        "propagation_eligible": False,
        "geometry_publication": {
            "status": (
                "published"
                if authority.admitted
                else "retained_context"
                if degraded_context_enabled
                else "withheld"
            ),
            "default_map_state": (
                "enabled"
                if authority.admitted
                else "enabled_degraded_context"
                if degraded_context_enabled
                else "unavailable"
            ),
            "default_enabled": authority.admitted or degraded_context_enabled,
            "display_role": "archaeology_context_only",
            "retained_density_is_authoritative": authority.admitted,
            "warning_codes": display_warning_codes,
        },
        "retained_context_identity": {
            "status": (
                "exact_v0.1.8"
                if retained_v018_surface
                else "substituted"
                if retained_density_pair
                else "absent"
            ),
            "tag": "v0.1.8" if retained_v018_surface else None,
            "commit": RAA_V018_COMMIT if retained_v018_surface else None,
        },
        "density_count_accounting": density_count_accounting,
        "authority_counts": {
            "archived_feature_count": authority.archived_feature_count,
            "heritage_site_count": authority.heritage_site_count,
            "density_site_count": authority.density_site_count,
            "density_feature_count": authority.density_feature_count,
        },
        "review": {
            "accepted": authority.admitted,
            "reviewer_id": authority.reviewer_id,
        },
        "inputs": inputs,
    }


def _density_count_accounting(
    metadata_bytes: bytes | None,
    density_bytes: bytes | None,
    authority: RaaDensityAuthorityDecision,
) -> dict[str, object]:
    try:
        if metadata_bytes is None or density_bytes is None:
            raise ValueError("Normalized buffers unavailable")
        metadata = decode_source_object(metadata_bytes.decode("utf-8"))
        density = decode_source_object(density_bytes.decode("utf-8"))
        metadata_count = non_negative_count(
            (as_mapping(metadata["counts"]) or {}).get("fornlamning")
        )
        features = density["features"]
        if not isinstance(features, list):
            raise TypeError("Density feature list is unavailable")
        cell_counts: list[int] = []
        for feature in features:
            properties = as_mapping((as_mapping(feature) or {}).get("properties")) or {}
            count = non_negative_count(properties.get("count"))
            if count is None:
                raise ValueError("RAÄ cell count must be a nonnegative integer")
            cell_counts.append(count)
        if metadata_count is None:
            raise ValueError("RAÄ metadata count must be a nonnegative integer")
    except (KeyError, TypeError, ValueError, OSError, json.JSONDecodeError):
        return {
            "status": "unavailable",
            "density_feature_count": None,
            "density_cell_count_sum": None,
            "metadata_fornlamning_count": None,
            "difference": None,
            "reconciled": False,
        }
    density_sum = sum(cell_counts)
    expected_count = (
        authority.density_site_count if authority.admitted else metadata_count
    )
    if expected_count is None:
        raise ValueError("Admitted RAÄ density lacks its included numerator")
    result: dict[str, object] = {
        "status": "observed_modern_membership"
        if authority.admitted
        else "observed_retained_normalized_pair",
        "density_feature_count": len(features),
        "density_cell_count_sum": density_sum,
        "metadata_fornlamning_count": metadata_count,
        "difference": density_sum - expected_count,
        "reconciled": density_sum == expected_count,
    }
    if authority.admitted:
        result["expected_included_count"] = expected_count
    return result


__all__ = [
    "RAA_ATLAS_INPUT_STATUS_FILENAME",
    "RAA_ATLAS_INPUT_STATUS_LABEL",
    "RAA_CONTEXT_RELATIVE_DIRECTORY",
    "RAA_V018_COMMIT",
    "RAA_V018_DENSITY_SHA256",
    "RAA_V018_METADATA_SHA256",
    "RaaAtlasInputSnapshot",
    "build_raa_atlas_input_status",
    "capture_raa_atlas_input_snapshot",
]
