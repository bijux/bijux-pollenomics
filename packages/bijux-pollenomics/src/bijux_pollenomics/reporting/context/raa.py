from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path

from ...collection.contracts.artifacts import RAA_DENSITY_GEOJSON, RAA_LAYER_METADATA
from ...collection.sources.raa import assess_raa_density_authority

RAA_ATLAS_INPUT_STATUS_FILENAME = "raa_atlas_input_status.json"
RAA_ATLAS_INPUT_STATUS_LABEL = "RAÄ atlas input status"
RAA_V018_COMMIT = "f5ab77edcd3affee65723074d21b83161b4bf542"
RAA_V018_DENSITY_SHA256 = (
    "acac7a952dc31be8b988ecb35386c877628e2580fae427f32281310635489d20"
)
RAA_V018_METADATA_SHA256 = (
    "baa5f7ec34e290d5b52ad93afb8a05e77830bd2b2672a15a579e571f5f6d91d8"
)

_AUTHORITY_INPUTS = {
    "raw_inventory": "raa/raw/publicerade_lamningar_centrumpunkt.geojson",
    "raw_summary": "raa/raw/publicerade_lamningar_centrumpunkt_summary.json",
    "normalized_metadata": "/".join(
        (RAA_LAYER_METADATA.source, *RAA_LAYER_METADATA.relative_parts)
    ),
    "normalized_density": "/".join(
        (RAA_DENSITY_GEOJSON.source, *RAA_DENSITY_GEOJSON.relative_parts)
    ),
    "scientific_review": "raa/review/spatiotemporal_review.json",
}


def build_raa_atlas_input_status(context_root: Path) -> dict[str, object]:
    """Describe whether the Sweden-only RAÄ context may enter an atlas bundle."""
    context_root = Path(context_root)
    authority = assess_raa_density_authority(context_root)
    inputs = {
        name: _input_receipt(context_root, relative_path)
        for name, relative_path in _AUTHORITY_INPUTS.items()
    }
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
        _density_count_accounting(context_root) if retained_density_pair else None
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
            "accepted": (
                authority.reviewer_id is not None
                and "scientific_review_not_accepted" not in authority.reason_codes
            ),
            "reviewer_id": authority.reviewer_id,
        },
        "inputs": inputs,
    }


def _input_receipt(context_root: Path, relative_path: str) -> dict[str, object]:
    path = context_root / relative_path
    present = path.is_file()
    return {
        "path": relative_path,
        "present": present,
        "sha256": _file_sha256(path) if present else None,
    }


def _file_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _density_count_accounting(context_root: Path) -> dict[str, object]:
    metadata_path = context_root / _AUTHORITY_INPUTS["normalized_metadata"]
    density_path = context_root / _AUTHORITY_INPUTS["normalized_density"]
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        density = json.loads(density_path.read_text(encoding="utf-8"))
        metadata_counts = metadata["counts"]
        metadata_count = metadata_counts["fornlamning"]
        features = density["features"]
        cell_counts = [feature["properties"]["count"] for feature in features]
        if (
            type(metadata_count) is not int
            or metadata_count < 0
            or any(type(count) is not int or count < 0 for count in cell_counts)
        ):
            raise ValueError("RAÄ density counts must be nonnegative integers")
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
    return {
        "status": "observed_retained_normalized_pair",
        "density_feature_count": len(features),
        "density_cell_count_sum": density_sum,
        "metadata_fornlamning_count": metadata_count,
        "difference": density_sum - metadata_count,
        "reconciled": density_sum == metadata_count,
    }


__all__ = [
    "RAA_ATLAS_INPUT_STATUS_FILENAME",
    "RAA_ATLAS_INPUT_STATUS_LABEL",
    "RAA_V018_COMMIT",
    "RAA_V018_DENSITY_SHA256",
    "RAA_V018_METADATA_SHA256",
    "build_raa_atlas_input_status",
]
