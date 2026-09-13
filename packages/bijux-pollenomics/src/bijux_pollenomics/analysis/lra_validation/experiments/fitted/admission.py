"""Outcome-free support admission for whole original spatial training groups."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from ...contracts import Fold, TrainingAdmission, ValidationRefusal, finite_number
from ...spatial.support import support_separation
from ...splits import admit_training_groups, grouped_leave_one_out
from ..configuration import (
    BLOCK_SPLIT,
    SpatialBlockExperimentSpec,
    object_list,
    object_mapping,
)
from ..inputs import read_geometry, read_reference


@dataclass(frozen=True)
class Footprint:
    """Explicit measured/model-scenario support; no inferred basin-radius substitution."""

    latitude: float
    longitude: float
    radius_m: float
    coordinate_uncertainty_m: float


@dataclass(frozen=True)
class BlockSupport:
    """Both roles for one pinned site declaration and geometry."""

    record_id: str
    source: Footprint
    target: Footprint
    support_sha256: str
    geometry_sha256: str
    source_integration_cutoff_m: float


def read_block_supports(
    spec: SpatialBlockExperimentSpec, input_root: Path
) -> dict[str, BlockSupport]:
    """Inspect geometry only; target observations and excluded pollen remain unopened."""
    references = dict(spec.support_references)
    reveals = object_mapping(
        object_mapping(spec.template()["configuration"], "configuration")["reveals"],
        "reveals",
    )
    regional_cutoff = finite_number(reveals["region_cutoff_m"])
    supports = {}
    for site in spec.sites:
        record = site.record.record_id
        geometry = read_geometry(input_root, site, spec)
        data = read_reference(input_root, references[record])
        if (
            set(data)
            != {
                "schema_version",
                "profile",
                "record_id",
                "geometry_sha256",
                "unit",
                "source_radius_m",
                "target_radius_m",
                "coordinate_uncertainty_m",
            }
            or data["schema_version"] != "lra-block-support.v1"
            or data["profile"] != "declared-finite-cutoff-synthetic-v1"
            or data["record_id"] != record
            or data["geometry_sha256"] != site.geometry.sha256
            or data["unit"] != "m"
        ):
            raise ValidationRefusal("invalid_block_support", record)
        source_radius = finite_number(data["source_radius_m"])
        target_radius = finite_number(data["target_radius_m"])
        uncertainty = finite_number(data["coordinate_uncertainty_m"])
        cutoff = max(
            regional_cutoff,
            *(
                finite_number(object_mapping(ring, "ring")["outer_m"])
                for key in ("inversion_rings", "forward_rings")
                for ring in object_list(geometry[key], key)
            ),
        )
        if (
            source_radius < cutoff
            or target_radius != spec.local_support_radius_m
            or uncertainty < 0
        ):
            raise ValidationRefusal(
                "incompatible_block_support",
                "Source footprint must cover every possible numerical integration cutoff; target footprint must match output support",
            )
        latitude, longitude = (
            finite_number(geometry["latitude"]),
            finite_number(geometry["longitude"]),
        )
        supports[record] = BlockSupport(
            record,
            Footprint(latitude, longitude, source_radius, uncertainty),
            Footprint(latitude, longitude, target_radius, uncertainty),
            references[record].sha256,
            site.geometry.sha256,
            cutoff,
        )
    return supports


def admit_block_training(
    spec: SpatialBlockExperimentSpec,
    fold: Fold,
    groups: dict[str, str],
    supports: dict[str, BlockSupport],
) -> TrainingAdmission:
    """Every observed source, including any regional anchor, faces every block target."""
    expected_groups = {
        record: outer.test_group_ids[0]
        for outer in grouped_leave_one_out([site.record for site in spec.sites])
        for record in outer.test_record_ids
    }
    if groups != expected_groups:
        raise ValidationRefusal("block_group_identity_mismatch", fold.fold_id)
    if set(supports) != {*fold.train_record_ids, *fold.test_record_ids}:
        raise ValidationRefusal("incomplete_block_support", fold.fold_id)
    comparisons = []
    excluded = set()
    for record in fold.train_record_ids:
        for target in fold.test_record_ids:
            distance = support_separation(
                supports[target].target, supports[record].source
            )
            eligible = distance.lower_bound_m >= spec.minimum_buffer_m
            if not eligible:
                excluded.add(groups[record])
            comparisons.append(
                {
                    "source_record_id": record,
                    "target_record_id": target,
                    "source_group_id": groups[record],
                    "target_group_id": groups[target],
                    "distance": asdict(distance),
                    "eligible": eligible,
                }
            )
    criterion: dict[str, object] = {
        "profile": BLOCK_SPLIT,
        "minimum_buffer_m": spec.minimum_buffer_m,
        "comparison": "lower_bound_m >= minimum_buffer_m",
        "support_scope": "declared_finite_cutoff_synthetic_not_empirical_independence",
        "supports": {key: asdict(supports[key]) for key in sorted(supports)},
        "comparisons": comparisons,
    }
    return admit_training_groups(
        fold,
        [site.record for site in spec.sites],
        tuple(group for group in fold.train_group_ids if group not in excluded),
        criterion=criterion,
    )


def verify_block_supports(spec: SpatialBlockExperimentSpec, input_root: Path) -> None:
    """Recheck every consumed support declaration just before phase publication."""
    for _, reference in spec.support_references:
        read_reference(input_root, reference)


def retained_training_admission(value: object, fold: Fold) -> TrainingAdmission:
    """Admit a saved canonical partition and independently recompute its buffer decisions."""
    from ...contracts import canonical_json, manifest_sha256
    from ..configuration import identity

    row = object_mapping(value, "training_admission")
    ownership = object_mapping(row["record_groups"], "record_groups")
    criterion = object_mapping(row["criterion"], "criterion")
    admission = TrainingAdmission(
        fold,
        tuple((record, identity(group)) for record, group in ownership.items()),
        tuple(
            identity(group)
            for group in object_list(
                row["admitted_training_group_ids"], "admitted_training_group_ids"
            )
        ),
        canonical_json(criterion),
    )
    if manifest_sha256(admission.as_dict()) != manifest_sha256(row):
        raise ValidationRefusal("block_admission_identity_mismatch", fold.fold_id)
    if (
        set(criterion)
        != {
            "profile",
            "minimum_buffer_m",
            "comparison",
            "support_scope",
            "supports",
            "comparisons",
        }
        or criterion["profile"] != BLOCK_SPLIT
        or criterion["comparison"] != "lower_bound_m >= minimum_buffer_m"
        or criterion["support_scope"]
        != "declared_finite_cutoff_synthetic_not_empirical_independence"
    ):
        raise ValidationRefusal("invalid_block_criterion", fold.fold_id)
    minimum = finite_number(criterion["minimum_buffer_m"])
    if minimum < 0:
        raise ValidationRefusal("invalid_block_criterion", fold.fold_id)
    supports = object_mapping(criterion["supports"], "supports")
    if set(supports) != set(ownership):
        raise ValidationRefusal("incomplete_block_support", fold.fold_id)
    decoded: dict[str, tuple[Footprint, Footprint]] = {}
    for record, value in supports.items():
        support = object_mapping(value, "support")
        if (
            set(support)
            != {
                "record_id",
                "source",
                "target",
                "support_sha256",
                "geometry_sha256",
                "source_integration_cutoff_m",
            }
            or support["record_id"] != record
        ):
            raise ValidationRefusal("invalid_block_support", record)
        shapes = []
        for role in ("source", "target"):
            shape = object_mapping(support[role], role)
            if set(shape) != {
                "latitude",
                "longitude",
                "radius_m",
                "coordinate_uncertainty_m",
            }:
                raise ValidationRefusal("invalid_block_support", record)
            shape_values = {key: finite_number(number) for key, number in shape.items()}
            if (
                min(shape_values["radius_m"], shape_values["coordinate_uncertainty_m"])
                < 0
            ):
                raise ValidationRefusal("invalid_block_support", record)
            shapes.append(Footprint(**shape_values))
        source_shape, target_shape = shapes
        if (
            source_shape.latitude,
            source_shape.longitude,
            source_shape.coordinate_uncertainty_m,
        ) != (
            target_shape.latitude,
            target_shape.longitude,
            target_shape.coordinate_uncertainty_m,
        ) or source_shape.radius_m < finite_number(
            support["source_integration_cutoff_m"]
        ):
            raise ValidationRefusal("incompatible_block_support", record)
        if finite_number(support["source_integration_cutoff_m"]) <= 0 or any(
            re.fullmatch(r"[0-9a-f]{64}", identity(support[field])) is None
            for field in ("support_sha256", "geometry_sha256")
        ):
            raise ValidationRefusal("invalid_block_support", record)
        decoded[record] = (source_shape, target_shape)
    excluded, comparisons = set(), []
    for record in fold.train_record_ids:
        for target in fold.test_record_ids:
            distance = support_separation(decoded[target][1], decoded[record][0])
            eligible = distance.lower_bound_m >= minimum
            if not eligible:
                excluded.add(ownership[record])
            comparisons.append(
                {
                    "source_record_id": record,
                    "target_record_id": target,
                    "source_group_id": ownership[record],
                    "target_group_id": ownership[target],
                    "distance": asdict(distance),
                    "eligible": eligible,
                }
            )
    if (
        set(admission.excluded_group_ids) != excluded
        or criterion["comparisons"] != comparisons
    ):
        raise ValidationRefusal("block_buffer_decision_mismatch", fold.fold_id)
    return admission


def validate_prediction_support(
    row: dict[str, object],
    fit: dict[str, object],
    spatial: dict[str, object],
    admission: TrainingAdmission,
) -> None:
    """Join retained buffer geometry to the same fitted/target coordinate and output support."""
    import json

    from ..configuration import identity

    supports = object_mapping(
        object_mapping(json.loads(admission.criterion_json), "criterion")["supports"],
        "supports",
    )
    ownership = dict(admission.record_groups)
    target = object_mapping(supports[identity(row["record_id"])], "target_support")
    footprint = object_mapping(target["target"], "target")
    coordinate = {key: footprint[key] for key in ("latitude", "longitude")}
    declared_support = object_mapping(row["support"], "support")
    preparation = object_mapping(row["forward_preparation"], "forward_preparation")
    if (
        target["geometry_sha256"] != row["target_geometry_sha256"]
        or spatial["coordinate"] != coordinate
        or footprint["radius_m"] != declared_support["local_support_radius_m"]
        or finite_number(preparation["regional_cutoff_m"])
        > finite_number(target["source_integration_cutoff_m"])
    ):
        raise ValidationRefusal(
            "block_prediction_support_mismatch",
            "Target geometry or output support differs",
        )
    coordinates = object_mapping(fit["training_coordinates"], "training_coordinates")
    for value in object_list(row["training_products"], "training_products"):
        product = object_mapping(value, "training_product")
        record = identity(product["record_id"])
        source = object_mapping(
            object_mapping(supports[record], "support")["source"], "source"
        )
        if coordinates[ownership[record]] != {
            key: source[key] for key in ("latitude", "longitude")
        }:
            raise ValidationRefusal(
                "block_prediction_support_mismatch",
                "Training model coordinates differ from buffered source",
            )
