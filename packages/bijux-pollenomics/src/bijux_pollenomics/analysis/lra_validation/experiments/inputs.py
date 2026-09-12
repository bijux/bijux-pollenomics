"""Read only admitted per-fold observations and distinct target geometry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ..contracts import Fold, ValidationRefusal, canonical_json, finite_number
from .configuration import (
    ExperimentSite,
    ExperimentSpec,
    InputReference,
    identity,
    object_list,
    object_mapping,
)

SAMPLE_FIELDS = {
    "site_id",
    "sample_id",
    "coordinate",
    "bin_id",
    "age_type",
    "age_support_bp",
    "chronology_evidence_id",
}


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field: {key}")
        result[key] = value
    return result


def read_reference(root: Path, reference: InputReference) -> dict[str, object]:
    """Verify finite JSON bytes inside a real, nonsymlink input root."""
    root = root.absolute()
    target = root / reference.path
    try:
        if root.is_symlink() or any(
            path.is_symlink()
            for path in (target, *target.parents)
            if path == root or root in path.parents
        ):
            raise ValueError("Symbolic links are not admitted")
        target.resolve(strict=True).relative_to(root.resolve(strict=True))
        if not target.is_file():
            raise ValueError("Input must be a regular file")
        content = target.read_bytes()
        if hashlib.sha256(content).hexdigest() != reference.sha256:
            raise ValueError("Input bytes differ from the frozen reference")
        value = json.loads(content, object_pairs_hook=_unique_pairs)
        canonical_json(value)
        return object_mapping(value, reference.path)
    except (OSError, ValueError, TypeError) as exc:
        raise ValidationRefusal(
            "invalid_experiment_input", f"{reference.path}: {exc}"
        ) from exc


def read_geometry(
    root: Path, site: ExperimentSite, spec: ExperimentSpec
) -> dict[str, object]:
    """Geometry has a closed metadata schema with no pollen fields."""
    data = read_reference(root, site.geometry)
    if set(data) != {
        "basin",
        "inversion_rings",
        "forward_rings",
        "sample_metadata",
        "longitude",
        "latitude",
    }:
        raise ValidationRefusal(
            "invalid_target_geometry", "Unexpected or missing geometry fields"
        )
    metadata = object_mapping(data["sample_metadata"], "sample_metadata")
    if set(metadata) != SAMPLE_FIELDS or metadata["site_id"] != site.record.site_id:
        raise ValidationRefusal(
            "invalid_target_geometry",
            "Sample support must be outcome-free and site-aligned",
        )
    for field in (
        "site_id",
        "sample_id",
        "bin_id",
        "age_type",
        "chronology_evidence_id",
    ):
        identity(metadata[field])
    chronology_ids = {
        identity(row["evidence_id"])
        for value in object_list(spec.template()["evidence"], "evidence")
        if (row := object_mapping(value, "evidence"))["role"] == "chronology"
    }
    if metadata["chronology_evidence_id"] not in chronology_ids:
        raise ValidationRefusal(
            "invalid_target_chronology",
            "Support must bind an admitted chronology reference",
        )
    basin = object_mapping(data["basin"], "basin")
    if set(basin) != {"diameter_m", "site_type"}:
        raise ValidationRefusal(
            "invalid_target_geometry", "Basin type and measured diameter are required"
        )
    inversion = object_list(data["inversion_rings"], "inversion_rings")
    forward = object_list(data["forward_rings"], "forward_rings")
    if len(inversion) < spec.local_ring_count or len(forward) <= spec.local_ring_count:
        raise ValidationRefusal(
            "invalid_target_geometry", "Declared inversion/forward support is missing"
        )
    for ring in (*inversion, *forward):
        if set(object_mapping(ring, "ring")) != {
            "inner_m",
            "outer_m",
            "mean_m",
            "ring_area_m2",
            "terrestrial_area_m2",
        }:
            raise ValidationRefusal(
                "invalid_target_geometry",
                "Ring fields must declare metres and square metres",
            )
    for rows in (inversion, forward):
        if (
            finite_number(
                object_mapping(rows[spec.local_ring_count - 1], "ring")["outer_m"]
            )
            != spec.local_support_radius_m
        ):
            raise ValidationRefusal(
                "incompatible_spatial_support",
                "Selected outer radius must equal the common declared support",
            )
    if (
        finite_number(object_mapping(inversion[0], "ring")["inner_m"])
        <= finite_number(basin["diameter_m"]) / 2
    ):
        raise ValidationRefusal(
            "invalid_inversion_geometry",
            "Analytical eligibility radii must be beyond the physical shore",
        )
    longitude, latitude = (
        finite_number(data["longitude"]),
        finite_number(data["latitude"]),
    )
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValidationRefusal(
            "invalid_target_geometry", "Coordinates must be WGS84 degrees"
        )
    return data


def read_training_observation(
    root: Path, site: ExperimentSite, fold: Fold, spec: ExperimentSpec
) -> dict[str, object]:
    """Reject withheld membership before opening or hashing observation bytes."""
    if (
        site.record.record_id not in fold.train_record_ids
        or site.record.record_id in fold.test_record_ids
    ):
        raise ValidationRefusal("withheld_input_leakage", site.record.record_id)
    data = read_reference(root, site.raw)
    if set(data) != {"data_kind", "taxa", "sample"} or data["data_kind"] != "synthetic":
        raise ValidationRefusal(
            "unsupported_experiment_profile",
            "Initial observations must explicitly be synthetic",
        )
    if data["taxa"] != spec.template().get("taxa"):
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "Observation taxon order differs from the template",
        )
    sample = object_mapping(data["sample"], "sample")
    geometry = read_geometry(root, site, spec)
    if (
        set(sample) != SAMPLE_FIELDS | {"counts"}
        or {key: sample[key] for key in SAMPLE_FIELDS} != geometry["sample_metadata"]
    ):
        raise ValidationRefusal("observation_geometry_mismatch", site.record.record_id)
    return sample


def raw_identity(site: ExperimentSite) -> str:
    """Use a stable role identity, separately bound to actual input hashes."""
    return "raw:" + site.record.record_id


def geometry_identity(site: ExperimentSite) -> str:
    return "geometry:" + site.record.record_id


def make_request(
    spec: ExperimentSpec,
    local: ExperimentSite,
    anchor: ExperimentSite,
    fold: Fold,
    root: Path,
) -> dict[str, object]:
    """Materialize one actual local/regional observation pair, without pooling."""
    request = spec.template()
    evidence = object_list(request["evidence"], "evidence")
    for role, site in (("local", local), ("regional", anchor)):
        sample = read_training_observation(root, site, fold, spec)
        geometry = read_geometry(root, site, spec)
        sample["raw_evidence_id"] = raw_identity(site)
        basin = object_mapping(geometry["basin"], "basin")
        basin["geometry_evidence_id"] = geometry_identity(site)
        request[role] = {"basin": basin, "samples": [sample]}
        evidence.extend(
            [
                {
                    "evidence_id": raw_identity(site),
                    "role": "raw_snapshot",
                    "path": site.raw.path,
                    "sha256": site.raw.sha256,
                },
                {
                    "evidence_id": geometry_identity(site),
                    "role": "geometry",
                    "path": site.geometry.path,
                    "sha256": site.geometry.sha256,
                },
            ]
        )
        if role == "local":
            request["rings"] = [
                dict(
                    object_mapping(row, "ring"),
                    geometry_evidence_id=geometry_identity(site),
                )
                for row in object_list(geometry["inversion_rings"], "inversion_rings")
            ]
    request["evidence"] = evidence
    configuration = object_mapping(request["configuration"], "configuration")
    love = object_mapping(configuration["love"], "love")
    love["max_ring"] = spec.local_ring_count
    configuration["love"] = love
    request["configuration"] = configuration
    return request
