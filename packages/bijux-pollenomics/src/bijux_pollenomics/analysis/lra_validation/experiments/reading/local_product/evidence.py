"""Metadata, source and numerical evidence for grouped-local predictions."""

from __future__ import annotations

import re
from copy import deepcopy

from .....lra.batches.models import LRABatchItem
from ....contracts import ValidationRefusal, canonical_json, finite_number
from ....metrics import closed_composition
from ...configuration import LocalPollenSpec, identity, object_list, object_mapping
from ...inputs import channel_catalogue
from ..provenance import _validate_request

_METADATA_FIELDS = set(
    "profile method request_template regional_priority local_ring_count "
    "local_support_radius_m support_profile observation_channels "
    "source_catalogue".split()
)
_NUMERICAL_FIELDS = set(
    "scientific_content_sha256 scientific_identity_sha256 source_radius_label_m "
    "local_support_radius_m support_profile composition".split()
)
_ROW_FIELDS = set(
    "profile fold_id record_id group_id bin_id method method_kind evaluation_roles "
    "pollen_eligible_for_heldout_acceptance vegetation_fraction pollen_fraction "
    "observed_pollen_count observed_pollen_unit channel_admission outer_fold "
    "observed_local_pollen_source regional_pollen_source unused_training_record_ids "
    "request_sha256 numerical_product target_geometry_sha256 support_profile "
    "local_support_radius_m preparation_profile forward_method_profile engine_build "
    "declared_inversion_rings declared_forward_rings regional_cover full_k "
    "full_terrestrial_fraction ring_bounds_m uncertainty_status "
    "prediction_manifest_sha256".split()
)
_FORBIDDEN_OUTCOME_FIELDS = set(
    "observed_vegetation target_vegetation observed_cover vegetation_outcome "
    "vegetation_outcome_reference outcome score threshold release_admission".split()
)


def digest(value: object, label: str) -> str:
    """Require one canonical SHA-256 identity."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationRefusal("invalid_local_prediction_inventory", label)
    return value


def _refuse_outcomes(value: object) -> None:
    if isinstance(value, dict):
        if _FORBIDDEN_OUTCOME_FIELDS & set(value):
            raise ValidationRefusal(
                "local_prediction_outcome_leakage", "Outcome-bearing input field"
            )
        for child in value.values():
            _refuse_outcomes(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            _refuse_outcomes(child)


def specification(
    metadata: dict[str, object], *, profile: str, method: str
) -> tuple[LocalPollenSpec, dict[str, dict[str, object]]]:
    """Rebuild the exact normalized producer declaration from retained metadata."""
    if (
        set(metadata) != _METADATA_FIELDS
        or metadata["profile"] != profile
        or metadata["method"] != method
    ):
        raise ValidationRefusal(
            "invalid_local_prediction_metadata", "Closed local metadata required"
        )
    catalogue: dict[str, dict[str, object]] = {}
    sites = []
    for value in object_list(metadata["source_catalogue"], "source_catalogue"):
        row = object_mapping(value, "source")
        if set(row) != {
            "record_id",
            "site_id",
            "identity_keys",
            "raw_path",
            "raw_sha256",
            "geometry_path",
            "geometry_sha256",
        }:
            raise ValidationRefusal(
                "invalid_local_prediction_metadata", "Closed source catalogue required"
            )
        record = identity(row["record_id"])
        if record in catalogue:
            raise ValidationRefusal(
                "invalid_local_prediction_metadata", "Duplicate source record"
            )
        catalogue[record] = row
        sites.append(
            {
                "record_id": record,
                "site_id": row["site_id"],
                "identity_keys": row["identity_keys"],
                "raw": {"path": row["raw_path"], "sha256": row["raw_sha256"]},
                "geometry": {
                    "path": row["geometry_path"],
                    "sha256": row["geometry_sha256"],
                },
            }
        )
    spec = LocalPollenSpec(
        {
            "schema_version": "lra-experiment.v1",
            "profile": profile,
            "sites": sites,
            "regional_priority": metadata["regional_priority"],
            "method": method,
            "local_ring_count": metadata["local_ring_count"],
            "local_support_radius_m": metadata["local_support_radius_m"],
            "support_profile": metadata["support_profile"],
            "request_template": metadata["request_template"],
        }
    )
    if canonical_json(metadata["observation_channels"]) != canonical_json(
        channel_catalogue(spec)
    ):
        raise ValidationRefusal(
            "invalid_local_prediction_metadata", "Observation ownership differs"
        )
    return spec, catalogue


def validate_prediction_evidence(
    row: dict[str, object],
    *,
    spec: LocalPollenSpec,
    catalogue: dict[str, dict[str, object]],
    fold: dict[str, object],
    request: dict[str, object],
    operation: dict[str, object],
) -> None:
    """Bind one prediction to exact batch, source and numerical identities."""
    _refuse_outcomes(row)
    record = identity(row["record_id"])
    training = tuple(
        identity(value)
        for value in object_list(fold["train_record_ids"], "train_record_ids")
    )
    eligible = [key for key in spec.regional_priority if key in training]
    if not eligible:
        raise ValidationRefusal("invalid_local_prediction_source", record)
    anchor = eligible[0]
    local_source = object_mapping(row["observed_local_pollen_source"], "local_source")
    regional_source = object_mapping(row["regional_pollen_source"], "regional_source")
    target_source, anchor_source = catalogue[record], catalogue[anchor]
    _validate_request(
        {"local_ring_count": spec.local_ring_count},
        spec.template(),
        catalogue,
        record,
        anchor,
        deepcopy(request),
    )
    template = spec.template()
    taxa = tuple(identity(value) for value in object_list(template["taxa"], "taxa"))
    local = object_mapping(request["local"], "local")
    regional = object_mapping(request["regional"], "regional")
    local_rows = object_list(local["samples"], "local_samples")
    regional_rows = object_list(regional["samples"], "regional_samples")
    if len(local_rows) != 1 or len(regional_rows) != 1:
        raise ValidationRefusal(
            "invalid_local_prediction_request", "Require one local/regional sample"
        )
    local_sample = object_mapping(local_rows[0], "local_sample")
    regional_sample = object_mapping(regional_rows[0], "regional_sample")
    counts = object_mapping(row["observed_pollen_count"], "counts")
    vegetation = closed_composition(
        {
            identity(key): finite_number(value)
            for key, value in object_mapping(
                row["vegetation_fraction"], "vegetation"
            ).items()
        }
    )
    pollen = closed_composition(
        {
            identity(key): finite_number(value)
            for key, value in object_mapping(row["pollen_fraction"], "pollen").items()
        }
    )
    numerical = object_mapping(row["numerical_product"], "numerical_product")
    rings = [
        object_mapping(value, "ring")
        for value in object_list(request["rings"], "rings")
    ]
    source_ring = rings[spec.local_ring_count - 1]
    product = object_mapping(operation.get("product"), "operation_product")
    expected_local = {
        "record_id": record,
        "group_id": row["group_id"],
        "path": target_source["raw_path"],
        "sha256": target_source["raw_sha256"],
        "role": "observed_local_pollen",
    }
    expected_regional = {
        "record_id": anchor,
        "path": anchor_source["raw_path"],
        "sha256": anchor_source["raw_sha256"],
        "role": "training_regional_pollen",
    }
    checks = (
        set(row) == _ROW_FIELDS,
        row.get("uncertainty_status")
        == "point_predictions_only_intervals_not_implemented",
        bool(identity(row.get("preparation_profile"))),
        bool(identity(row.get("forward_method_profile"))),
        set(object_mapping(row.get("engine_build"), "engine_build"))
        == {
            "distribution",
            "version",
            "numerical_backend",
            "python_api",
            "extension_group",
            "extension_name",
            "extension_target",
        },
        operation.get("item_status") == "completed",
        product.get("scientific_content_sha256")
        == numerical.get("scientific_content_sha256"),
        digest(numerical.get("scientific_content_sha256"), "Invalid content digest")
        == product.get("scientific_content_sha256"),
        bool(digest(numerical.get("scientific_identity_sha256"), "Invalid identity")),
        set(numerical) == _NUMERICAL_FIELDS,
        numerical.get("composition") == vegetation,
        finite_number(numerical["source_radius_label_m"])
        == finite_number(source_ring["mean_m"]),
        finite_number(numerical["local_support_radius_m"])
        == finite_number(source_ring["outer_m"])
        == spec.local_support_radius_m,
        numerical.get("support_profile") == spec.support_profile,
        row.get("request_sha256") == LRABatchItem(record, request).request_sha256,
        local_source == expected_local,
        regional_source == expected_regional,
        row.get("target_geometry_sha256") == target_source["geometry_sha256"],
        row.get("support_profile") == spec.support_profile,
        finite_number(row["local_support_radius_m"]) == spec.local_support_radius_m,
        row.get("unused_training_record_ids")
        == [key for key in training if key != anchor],
        request.get("pollen_unit") == row.get("observed_pollen_unit") == "count",
        set(counts) == set(taxa) == set(vegetation) == set(pollen),
        all(type(value) is int and value >= 0 for value in counts.values()),
        [counts[taxon] for taxon in taxa]
        == object_list(local_sample.get("counts"), "counts"),
        local_sample.get("bin_id")
        == regional_sample.get("bin_id")
        == row.get("bin_id"),
        all(
            local_sample.get(key) == regional_sample.get(key)
            for key in ("coordinate", "age_type")
        ),
        [
            {key: value for key, value in ring.items() if key != "geometry_evidence_id"}
            for ring in rings
        ]
        == row.get("declared_inversion_rings"),
    )
    if not all(checks):
        raise ValidationRefusal(
            "invalid_local_prediction_evidence", "Request or numerical source differs"
        )
