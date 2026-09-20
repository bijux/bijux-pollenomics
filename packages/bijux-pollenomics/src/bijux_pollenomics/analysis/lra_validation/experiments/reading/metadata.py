"""Complete singleton catalogue, template and scientific accounting on reopening."""

from __future__ import annotations

from ...contracts import (
    SiteRecord,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...splits import grouped_leave_one_out
from ..configuration import (
    FITTED_METHOD,
    FITTED_PROFILE,
    PROFILE,
    InputReference,
    identity,
    object_list,
    object_mapping,
    validate_template,
)


def _same(left: object, right: object, label: str) -> None:
    if canonical_json(left) != canonical_json(right):
        raise ValidationRefusal("singleton_metadata_identity_mismatch", label)


def validate_singleton_metadata(
    value: object,
    scientific: dict[str, object],
    folds: dict[str, dict[str, object]],
    predictions: dict[tuple[str, str], dict[str, object]],
    methods: tuple[str, ...],
) -> None:
    """Check recorded facts only; historical omitted fitted ring count is not inferred."""
    metadata = object_mapping(value, "experiment")
    fitted = scientific["profile"] == FITTED_PROFILE
    paired = (
        fitted
        and scientific.get("schema_version")
        == "lra-grouped-outer-paired-predictions.v1"
    )
    profile = FITTED_PROFILE if fitted else PROFILE
    common = {"profile", "request_template", "regional_priority", "source_catalogue"}
    expected = common | (
        {"support", "method"}
        if fitted
        else {"local_ring_count", "local_support_radius_m", "support_profile"}
    )
    if (
        set(metadata) != expected
        or metadata["profile"] != profile
        or scientific["profile"] != profile
    ):
        raise ValidationRefusal(
            "invalid_singleton_metadata", "Closed profile metadata required"
        )
    template = validate_template(metadata["request_template"])
    catalogue = [
        object_mapping(row, "source")
        for row in object_list(metadata["source_catalogue"], "source_catalogue")
    ]
    records = []
    for row in catalogue:
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
                "invalid_singleton_catalogue", "Closed source reference fields required"
            )
        for role in ("raw", "geometry"):
            InputReference.parse(
                {"path": row[role + "_path"], "sha256": row[role + "_sha256"]}, role
            )
        records.append(
            SiteRecord(
                identity(row["record_id"]),
                identity(row["site_id"]),
                tuple(
                    identity(key)
                    for key in object_list(row["identity_keys"], "identity_keys")
                ),
            )
        )
    record_ids = {record.record_id for record in records}
    if not 3 <= len(records) <= 128 or len(record_ids) != len(records):
        raise ValidationRefusal(
            "invalid_singleton_catalogue", "Unique complete record inventory required"
        )
    originals = grouped_leave_one_out(records)
    _same(
        [fold.as_dict() for fold in originals],
        scientific["folds"],
        "complete original site folds",
    )
    _same(
        {fold.fold_id: fold.as_dict() for fold in originals},
        folds,
        "original fold identities",
    )
    _same(
        manifest_sha256(scientific["folds"]),
        scientific["split_manifest_sha256"],
        "split hash",
    )
    priority = tuple(
        identity(key)
        for key in object_list(metadata["regional_priority"], "regional_priority")
    )
    if (
        not priority
        or len(set(priority)) != len(priority)
        or not set(priority).issubset(record_ids)
    ):
        raise ValidationRefusal(
            "invalid_singleton_catalogue", "Regional priority differs from catalogue"
        )
    if (
        scientific["experiment"]
        != (
            "all_target_pollen_withheld_fitted_spatial"
            if fitted
            else "all_target_pollen_withheld"
        )
        or scientific["uncertainty_status"]
        != "point_predictions_only_intervals_not_implemented"
        or scientific.get("scientific_acceptance", "not_evaluated") != "not_evaluated"
        or type(scientific["interrupted"]) is not bool
    ):
        raise ValidationRefusal(
            "invalid_singleton_scientific_posture",
            "Exploratory point predictions required",
        )
    failures = [
        object_mapping(row, "failure")
        for row in object_list(scientific["failures"], "failures")
    ]
    for row in failures:
        outer = folds[identity(row["fold_id"])]
        if paired:
            _same(
                row["record_ids"],
                outer["test_record_ids"],
                "paired refusal target accounting",
            )
            if row["method"] not in methods:
                raise ValidationRefusal(
                    "invalid_singleton_interruption", "Unknown paired method"
                )
        else:
            _same(
                row["record_ids"],
                outer["test_record_ids"],
                "refusal target accounting",
            )
        if row["status"] not in {"not_run", "refused"} or (
            (row["status"] == "not_run")
            != (row["reason_code"] == "experiment_interrupted")
        ):
            raise ValidationRefusal(
                "invalid_singleton_interruption", "Refusal role or reason differs"
            )
    if scientific["interrupted"] is not any(
        row["status"] == "not_run" for row in failures
    ):
        raise ValidationRefusal(
            "invalid_singleton_interruption", "Interrupted posture differs"
        )
    counts = {
        "requested_folds": len(originals),
        "requested_predictions": len(originals) * len(methods),
        "generated_predictions": len(predictions),
        "failed_folds": len({identity(row["fold_id"]) for row in failures}),
    }
    if paired:
        counts.update(
            failed_predictions=len(failures),
            refused_predictions=sum(row["status"] == "refused" for row in failures),
            not_run_predictions=sum(row["status"] == "not_run" for row in failures),
        )
    if any(
        type(scientific[key]) is not int or scientific[key] != value
        for key, value in counts.items()
    ) or scientific["all_predictions_generated"] is not (not failures):
        raise ValidationRefusal(
            "invalid_singleton_accounting", "Complete counts required"
        )
    if fitted:
        support = object_mapping(metadata["support"], "support")
        if set(support) != {
            "support_profile",
            "local_support_radius_m",
            "taxa",
            "temporal_matching",
            "versions",
        }:
            raise ValidationRefusal(
                "invalid_singleton_support", "Closed fitted support required"
            )
        for field in ("taxa", "temporal_matching", "versions"):
            _same(support[field], template[field], "template support")
        method = object_mapping(metadata["method"], "method")
        if (
            set(method) != {"profile", "length_scale_km", "ridge_penalty"}
            or method["profile"] != methods[0]
            or min(
                finite_number(method[key])
                for key in ("length_scale_km", "ridge_penalty")
            )
            <= 0
        ):
            raise ValidationRefusal(
                "invalid_singleton_method",
                "Fixed positive model configuration required",
            )
    else:
        support = {
            key: metadata[key] for key in ("support_profile", "local_support_radius_m")
        }
        count = metadata["local_ring_count"]
        if type(count) is not int or count < 1:
            raise ValidationRefusal(
                "invalid_singleton_support",
                "Explicit positive local ring count required",
            )
    if (
        support["support_profile"] != "same-outer-radius-homogeneous-v1"
        or finite_number(support["local_support_radius_m"]) <= 0
    ):
        raise ValidationRefusal(
            "invalid_singleton_support", "Positive homogeneous output support required"
        )
    bins = {
        identity(object_mapping(row, "bin")["bin_id"])
        for row in object_list(
            object_mapping(template["temporal_matching"], "temporal_matching")["bins"],
            "bins",
        )
    }
    for (fold_id, _), row in predictions.items():
        if row["bin_id"] not in bins:
            raise ValidationRefusal(
                "invalid_singleton_support", "Target bin absent from declared template"
            )
        if set(
            object_mapping(row["vegetation_fraction"], "vegetation_fraction")
        ) != set(object_list(template["taxa"], "taxa")):
            raise ValidationRefusal(
                "invalid_singleton_support", "Target taxa differ from declared template"
            )
        if fitted:
            _same(row["support"], support, "fitted output support")
            anchor = next(
                (
                    record
                    for record in priority
                    if record
                    in object_list(
                        folds[fold_id]["train_record_ids"], "train_record_ids"
                    )
                ),
                None,
            )
            source = (
                row
                if row["method"] == FITTED_METHOD
                else object_mapping(
                    row["baseline_model_manifest"], "baseline_model_manifest"
                )
            )
            _same(source["regional_anchor_record_id"], anchor, "regional priority")
            if row["method"] == FITTED_METHOD:
                fit = object_mapping(row["fit_manifest"], "fit_manifest")
                config = object_mapping(fit["configuration"], "configuration")
                _same(
                    {key: config[key] for key in method},
                    method,
                    "fitted method parameters",
                )
