"""Read only admitted per-fold observations and distinct target geometry."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from ..channels import (
    ObservationChannels,
    ObservedPollenAdmission,
    PollenChannel,
    assert_channel_inputs,
)
from ..contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ..splits import grouped_leave_one_out
from .configuration import (
    ExperimentScope,
    ExperimentSite,
    InputReference,
    LocalPollenSpec,
    SpatialBlockLocalPollenSpec,
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


def _reference_bytes(root: Path, reference: InputReference) -> bytes:
    """Verify exact bytes inside a real, nonsymlink input root."""
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
        return content
    except (OSError, ValueError, TypeError) as exc:
        raise ValidationRefusal(
            "invalid_experiment_input", f"{reference.path}: {exc}"
        ) from exc


def read_reference(root: Path, reference: InputReference) -> dict[str, object]:
    """Parse finite JSON from a verified raw or geometric source reference."""
    content = _reference_bytes(root, reference)
    try:
        value = json.loads(content, object_pairs_hook=_unique_pairs)
        canonical_json(value)
        return object_mapping(value, reference.path)
    except (ValueError, TypeError) as exc:
        raise ValidationRefusal(
            "invalid_experiment_input", f"{reference.path}: {exc}"
        ) from exc


def verify_consumed_sources(
    spec: ExperimentScope,
    root: Path,
    *,
    pollen_record_ids: set[str],
    geometry_record_ids: set[str],
    template_used: bool,
) -> None:
    """Recheck consumed bytes immediately before publication; never open outcomes."""
    by_record = {site.record.record_id: site for site in spec.sites}
    if not (pollen_record_ids | geometry_record_ids).issubset(by_record):
        raise ValidationRefusal(
            "unknown_consumed_source",
            "Source ownership differs from the frozen catalogue",
        )
    references = [by_record[key].raw for key in sorted(pollen_record_ids)]
    references.extend(by_record[key].geometry for key in sorted(geometry_record_ids))
    if template_used:
        for value in object_list(spec.template()["evidence"], "evidence"):
            row = object_mapping(value, "evidence")
            references.append(
                InputReference.parse(
                    {"path": row["path"], "sha256": row["sha256"]}, "evidence"
                )
            )
    for reference in references:
        _reference_bytes(root, reference)


def read_geometry(
    root: Path,
    site: ExperimentSite,
    spec: ExperimentScope,
    *,
    consumed_geometry: set[str] | None = None,
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
    if consumed_geometry is not None:
        consumed_geometry.add(site.record.record_id)
    return data


def read_training_observation(
    root: Path,
    site: ExperimentSite,
    fold: Fold,
    spec: ExperimentScope,
    *,
    consumed_geometry: set[str] | None = None,
) -> dict[str, object]:
    """Reject withheld membership before opening or hashing observation bytes."""
    if (
        site.record.record_id not in fold.train_record_ids
        or site.record.record_id in fold.test_record_ids
    ):
        raise ValidationRefusal("withheld_input_leakage", site.record.record_id)
    return _read_observation(root, site, spec, consumed_geometry=consumed_geometry)


def _read_observation(
    root: Path,
    site: ExperimentSite,
    spec: ExperimentScope,
    *,
    consumed_geometry: set[str] | None = None,
) -> dict[str, object]:
    """Read an already admitted pollen channel with exact geometry/sample identity."""
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
    geometry = read_geometry(root, site, spec, consumed_geometry=consumed_geometry)
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
    spec: ExperimentScope,
    local: ExperimentSite,
    anchor: ExperimentSite,
    fold: Fold,
    root: Path,
    *,
    training_admission: TrainingAdmission | None = None,
    consumed_pollen: set[str] | None = None,
    consumed_geometry: set[str] | None = None,
) -> dict[str, object]:
    """Materialize one actual local/regional observation pair, without pooling."""
    if isinstance(spec, SpatialBlockLocalPollenSpec):
        if training_admission is None:
            raise ValidationRefusal("missing_training_admission", fold.fold_id)
        block_local_channel_evidence(spec, fold, local, anchor, training_admission)
    elif isinstance(spec, LocalPollenSpec):
        local_channel_evidence(spec, fold, local, anchor)
    request = spec.template()
    evidence = object_list(request["evidence"], "evidence")
    for role, site in (("local", local), ("regional", anchor)):
        sample = (
            _read_observation(root, site, spec, consumed_geometry=consumed_geometry)
            if role == "local" and isinstance(spec, SpatialBlockLocalPollenSpec)
            else read_observed_local_pollen(
                root, site, fold, spec, consumed_geometry=consumed_geometry
            )
            if role == "local" and isinstance(spec, LocalPollenSpec)
            else read_training_observation(
                root, site, fold, spec, consumed_geometry=consumed_geometry
            )
        )
        if consumed_pollen is not None:
            consumed_pollen.add(site.record.record_id)
        geometry = read_geometry(root, site, spec, consumed_geometry=consumed_geometry)
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


def read_observed_local_pollen(
    root: Path,
    site: ExperimentSite,
    fold: Fold,
    spec: LocalPollenSpec,
    *,
    consumed_geometry: set[str] | None = None,
) -> dict[str, object]:
    """Admit the actual held-out record's observed pollen channel, never its vegetation."""
    if (
        not isinstance(spec, LocalPollenSpec)
        or site not in spec.sites
        or fold.test_record_ids != (site.record.record_id,)
        or site.record.record_id in fold.train_record_ids
    ):
        raise ValidationRefusal(
            "unadmitted_local_pollen_channel", site.record.record_id
        )
    local_channel_evidence(spec, fold, site)
    return _read_observation(root, site, spec, consumed_geometry=consumed_geometry)


def admitted_pollen_counts(value: object, taxa: tuple[str, ...]) -> dict[str, int]:
    counts = object_mapping(value, "observed_pollen_count")
    if set(counts) != set(taxa) or any(
        isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in counts.values()
    ):
        raise ValidationRefusal(
            "invalid_assimilated_counts",
            "Require the admitted nonnegative integer pollen denominator",
        )
    return {taxon: cast(int, counts[taxon]) for taxon in taxa}


def observation_channels(spec: LocalPollenSpec) -> tuple[ObservationChannels, ...]:
    """Register ownership independently of direct quantitative raw-file leaves."""
    folds = grouped_leave_one_out([site.record for site in spec.sites])
    groups = {
        record: fold.test_group_ids[0]
        for fold in folds
        for record in fold.test_record_ids
    }
    return tuple(
        ObservationChannels(
            site.record.record_id,
            groups[site.record.record_id],
            (PollenChannel(raw_identity(site), site.raw.sha256),),
            ("vegetation:" + site.record.record_id,),
        )
        for site in spec.sites
    )


def channel_catalogue(spec: LocalPollenSpec) -> list[dict[str, object]]:
    return [
        {
            "record_id": row.record_id,
            "group_id": row.group_id,
            "pollen_channels": [
                {"input_id": source.input_id, "source_sha256": source.source_sha256}
                for source in row.pollen_channels
            ],
            "vegetation_input_ids": row.vegetation_input_ids,
        }
        for row in observation_channels(spec)
    ]


def local_channel_evidence(
    spec: LocalPollenSpec,
    fold: Fold,
    target: ExperimentSite,
    anchor: ExperimentSite | None = None,
) -> dict[str, object]:
    """Validate actual observed-pollen ownership before access; preserve the original Fold."""
    if target not in spec.sites or fold.test_record_ids != (target.record.record_id,):
        raise ValidationRefusal(
            "unadmitted_local_pollen_channel", target.record.record_id
        )
    if anchor is not None and (
        anchor not in spec.sites or anchor.record.record_id not in fold.train_record_ids
    ):
        raise ValidationRefusal(
            "unadmitted_regional_pollen_channel", anchor.record.record_id
        )
    catalogue = observation_channels(spec)
    target_owner = next(
        row for row in catalogue if row.record_id == target.record.record_id
    )
    observed = ObservedPollenAdmission(
        target.record.record_id, target_owner.group_id, target_owner.pollen_channels
    )
    inputs = (
        (raw_identity(target),)
        if anchor is None
        else (raw_identity(target), raw_identity(anchor))
    )
    graph: dict[str, tuple[str, ...]] = {
        source.input_id: () for row in catalogue for source in row.pollen_channels
    }
    closure = assert_channel_inputs(
        fold, inputs, graph, channels=catalogue, observed_pollen=observed
    )
    consumed = [
        {
            "record_id": row.record_id,
            "group_id": row.group_id,
            "input_id": source.input_id,
            "source_sha256": source.source_sha256,
        }
        for row in catalogue
        for source in row.pollen_channels
        if source.input_id in closure
    ]
    return {
        "schema_version": "lra-local-pollen-channel-admission.v1",
        "original_fold_sha256": manifest_sha256(fold.as_dict()),
        "pollen_input_ids": inputs,
        "pollen_channel_closure": closure,
        "quantitative_lineage": {key: graph[key] for key in closure},
        "consumed_pollen_sources": consumed,
        "observed_pollen": {
            "record_id": observed.record_id,
            "group_id": observed.group_id,
            "pollen_channels": [source.__dict__ for source in observed.pollen_channels],
        },
    }


def block_local_channel_evidence(
    spec: SpatialBlockLocalPollenSpec,
    fold: Fold,
    target: ExperimentSite,
    anchor: ExperimentSite,
    admission: TrainingAdmission,
) -> dict[str, object]:
    admission.validate(fold)
    if (
        target not in spec.sites
        or target.record.record_id not in fold.test_record_ids
        or anchor not in spec.sites
        or anchor.record.record_id not in admission.admitted_record_ids
        or anchor.record.record_id in fold.test_record_ids
    ):
        raise ValidationRefusal("invalid_block_local_channel_admission", fold.fold_id)
    catalogue = observation_channels(spec)
    target_owner = next(
        row for row in catalogue if row.record_id == target.record.record_id
    )
    observed = ObservedPollenAdmission(
        target.record.record_id, target_owner.group_id, target_owner.pollen_channels
    )
    inputs = (raw_identity(target), raw_identity(anchor))
    graph = {
        source.input_id: (
            () if row.record_id == target.record.record_id else (row.record_id,)
        )
        for row in catalogue
        for source in row.pollen_channels
    }
    graph.update(dict.fromkeys(fold.train_record_ids, ()))
    closure = assert_channel_inputs(
        fold, inputs, graph, channels=catalogue, observed_pollen=observed
    )
    if set(closure) != {*inputs, anchor.record.record_id}:
        raise ValidationRefusal("invalid_block_local_channel_closure", fold.fold_id)
    consumed = [
        {
            "record_id": row.record_id,
            "group_id": row.group_id,
            "input_id": source.input_id,
            "source_sha256": source.source_sha256,
        }
        for row in catalogue
        for source in row.pollen_channels
        if source.input_id in closure
    ]
    return {
        "schema_version": "lra-block-local-pollen-channel-admission.v1",
        "original_fold_sha256": manifest_sha256(fold.as_dict()),
        "training_admission_sha256": manifest_sha256(admission.as_dict()),
        "pollen_input_ids": inputs,
        "pollen_channel_closure": closure,
        "quantitative_lineage": {key: graph[key] for key in closure},
        "consumed_pollen_sources": consumed,
        "observed_pollen": {
            "record_id": observed.record_id,
            "group_id": observed.group_id,
            "pollen_channels": [source.__dict__ for source in observed.pollen_channels],
        },
        "regional_anchor_record_id": anchor.record.record_id,
    }
