"""Bind retained block results to the complete declared experiment and fitted state."""

from __future__ import annotations

import json

from ...contracts import (
    Fold,
    TrainingAdmission,
    ValidationRefusal,
    canonical_json,
    finite_number,
    manifest_sha256,
)
from ...metrics import closed_composition
from ...spatial import FittedSpatialModel, SiteCoordinate, SpatialConfig
from ...splits import (
    assert_training_inputs,
    grouped_block_holdouts,
    grouped_leave_one_out,
)
from ..configuration import (
    BLOCK_PROFILE,
    SpatialBlockExperimentSpec,
    identity,
    object_list,
    object_mapping,
)
from .admission import retained_training_admission
from .model import fitted_support


def _same(left: object, right: object, label: str) -> None:
    if canonical_json(left) != canonical_json(right):
        raise ValidationRefusal("block_metadata_identity_mismatch", label)


def validate_block_metadata(
    experiment: object,
    scientific: dict[str, object],
    folds: dict[str, dict[str, object]],
    rows: dict[tuple[str, str, str], dict[str, object]],
    models: object,
) -> None:
    """Reopen declared metadata without source/outcome access or an installed engine."""
    declared = object_mapping(experiment, "experiment")
    if (
        set(declared) != {"schema_version", "request"}
        or declared["schema_version"] != "lra-spatial-block-experiment.v1"
    ):
        raise ValidationRefusal(
            "invalid_block_experiment", "Complete normalized request required"
        )
    spec = SpatialBlockExperimentSpec(object_mapping(declared["request"], "request"))
    _same(spec.request(), declared["request"], "normalized request")
    records = [site.record for site in spec.sites]
    expected = grouped_block_holdouts(records)
    _same(
        [fold.as_dict() for fold in expected],
        scientific["folds"],
        "complete original block inventory",
    )
    _same({fold.fold_id: fold.as_dict() for fold in expected}, folds, "original folds")
    ownership = {
        record: fold.test_group_ids[0]
        for fold in grouped_leave_one_out(records)
        for record in fold.test_record_ids
    }
    _same(ownership, scientific["record_groups"], "complete site ownership")
    if (
        scientific["profile"] != BLOCK_PROFILE
        or scientific["experiment"] != "all_target_pollen_withheld_spatial_blocks"
        or scientific["uncertainty_status"]
        != "point_predictions_only_intervals_not_implemented"
        or scientific["scientific_acceptance"] != "not_evaluated"
        or type(scientific["interrupted"]) is not bool
    ):
        raise ValidationRefusal(
            "invalid_block_scientific_posture", "Exploratory point predictions required"
        )
    failures = [
        object_mapping(value, "failure")
        for value in object_list(scientific["failures"], "failures")
    ]
    not_run = [row for row in failures if row["status"] == "not_run"]
    if scientific["interrupted"] is not bool(not_run) or any(
        (row["status"] == "not_run") != (row["reason_code"] == "experiment_interrupted")
        for row in failures
    ):
        raise ValidationRefusal(
            "invalid_block_interruption", "Interruption and target accounting differ"
        )
    admissions = object_mapping(scientific["block_admissions"], "block_admissions")
    retained = object_mapping(scientific["block_fit_records"], "block_fit_records")
    hashes = object_mapping(scientific["block_model_sha256"], "block_model_sha256")
    _same(models, retained, "models file")
    if set(retained) != set(hashes) or not set(retained).issubset(admissions):
        raise ValidationRefusal(
            "invalid_block_model_inventory", "Every completed fit must retain its state"
        )
    for fold in expected:
        if fold.fold_id not in admissions:
            continue
        admission = retained_training_admission(admissions[fold.fold_id], fold)
        _validate_support_catalogue(spec, admission)
        if fold.fold_id not in retained:
            continue
        state = object_mapping(retained[fold.fold_id], "block_fit")
        _validate_state(spec, fold, admission, state)
        _same(state["model_sha256"], hashes[fold.fold_id], "block model digest")
    for (fold_id, record, _), row in rows.items():
        state = object_mapping(retained[fold_id], "block_fit")
        _same({key: row[key] for key in state}, state, "target shares actual block fit")
        site = next(site for site in spec.sites if site.record.record_id == record)
        _same(
            row["target_geometry_sha256"],
            site.geometry.sha256,
            "target geometry reference",
        )
        _same(row["support"], fitted_support(spec), "target support")


def _validate_support_catalogue(
    spec: SpatialBlockExperimentSpec, admission: TrainingAdmission
) -> None:
    criterion = object_mapping(json.loads(admission.criterion_json), "criterion")
    _same(criterion["minimum_buffer_m"], spec.minimum_buffer_m, "declared buffer")
    supports = object_mapping(criterion["supports"], "supports")
    references = dict(spec.support_references)
    reveals = object_mapping(
        object_mapping(spec.template()["configuration"], "configuration")["reveals"],
        "reveals",
    )
    for site in spec.sites:
        record = site.record.record_id
        support = object_mapping(supports[record], "support")
        _same(support["support_sha256"], references[record].sha256, "support reference")
        _same(support["geometry_sha256"], site.geometry.sha256, "geometry reference")
        _same(
            object_mapping(support["target"], "target")["radius_m"],
            spec.local_support_radius_m,
            "target radius",
        )
        if finite_number(support["source_integration_cutoff_m"]) < finite_number(
            reveals["region_cutoff_m"]
        ):
            raise ValidationRefusal("incompatible_block_support", record)


def _validate_state(
    spec: SpatialBlockExperimentSpec,
    fold: Fold,
    admission: TrainingAdmission,
    state: dict[str, object],
) -> None:
    expected_fields = {
        "model_sha256",
        "fit_manifest",
        "training_products",
        "training_dependency_graph",
        "training_input_ids",
        "training_external_ids",
        "regional_anchor_record_id",
        "regional_anchor_group_id",
        "regional_value_source_record_ids",
        "regional_identity_source_record_ids",
        "support",
        "training_admission",
    }
    if set(state) != expected_fields:
        raise ValidationRefusal(
            "invalid_block_model_inventory", "Complete fitted state required"
        )
    _same(state["training_admission"], admission.as_dict(), "fit admission")
    _same(state["support"], fitted_support(spec), "fit support")
    anchor = next(
        (
            record
            for record in spec.regional_priority
            if record in admission.admitted_record_ids
        ),
        None,
    )
    if anchor is None or len(admission.admitted_group_ids) < 3:
        raise ValidationRefusal(
            "invalid_block_model_inventory",
            "Regional source and two local groups required",
        )
    ownership = dict(admission.record_groups)
    _same(state["regional_anchor_record_id"], anchor, "regional priority")
    _same(state["regional_anchor_group_id"], ownership[anchor], "regional group")
    _same(
        state["regional_value_source_record_ids"], [anchor], "regional value ancestry"
    )
    _same(
        state["regional_identity_source_record_ids"],
        admission.admitted_record_ids,
        "regional identity ancestry",
    )
    fit = object_mapping(state["fit_manifest"], "fit_manifest")
    products = [
        object_mapping(value, "product")
        for value in object_list(state["training_products"], "training_products")
    ]
    local_records = set(admission.admitted_record_ids) - {anchor}
    if (
        len(products) != len(local_records)
        or {identity(value["record_id"]) for value in products} != local_records
    ):
        raise ValidationRefusal("invalid_block_training_products", fold.fold_id)
    sites = {site.record.record_id: site for site in spec.sites}
    compositions: dict[str, object] = {}
    for product in products:
        record = identity(product["record_id"])
        _same(product["group_id"], ownership[record], "training group")
        _same(
            product["request_template_sha256"],
            manifest_sha256(spec.template()),
            "request template",
        )
        references = {}
        for role, site in (("local", sites[record]), ("regional", sites[anchor])):
            for field in ("raw", "geometry"):
                reference = site.raw if field == "raw" else site.geometry
                references[role + "_" + field] = {
                    "path": reference.path,
                    "sha256": reference.sha256,
                }
        _same(product["source_references"], references, "consumed source references")
        _same(
            product["local_support_radius_m"],
            spec.local_support_radius_m,
            "training output radius",
        )
        _same(
            product["support_profile"], spec.support_profile, "training output profile"
        )
        values = {
            key: finite_number(value)
            for key, value in object_mapping(
                product["composition"], "composition"
            ).items()
        }
        closed_composition(values)
        if set(values) != set(object_list(spec.template()["taxa"], "taxa")) or any(
            value <= 0 for value in values.values()
        ):
            raise ValidationRefusal("invalid_block_training_composition", record)
        compositions[ownership[record]] = values
    _same(fit["training_compositions"], compositions, "fitted responses")
    groups = tuple(
        identity(value)
        for value in object_list(fit["predictor_group_ids"], "predictor_group_ids")
    )
    if groups != tuple(sorted(compositions)):
        raise ValidationRefusal(
            "invalid_block_training_products", "Fitted predictor order differs"
        )
    support_id = "experiment-support:" + manifest_sha256(state["support"])
    fit_ids = tuple("experiment-fit:" + manifest_sha256(value) for value in products)
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(admission.admitted_record_ids, ())
    graph.update(
        {
            key: (identity(product["record_id"]), anchor)
            for key, product in zip(fit_ids, products, strict=True)
        }
    )
    graph[support_id] = ()
    _same(state["training_dependency_graph"], graph, "fit lineage")
    _same(
        state["training_input_ids"],
        (*admission.admitted_record_ids, *fit_ids, support_id),
        "fit input order",
    )
    _same(state["training_external_ids"], (*fit_ids, support_id), "fit external order")
    closure = assert_training_inputs(
        fold,
        (*admission.admitted_record_ids, *fit_ids, support_id),
        graph,
        training_admission=admission,
        admitted_external_ids=(*fit_ids, support_id),
    )
    _same(fit["allowed_input_closure"], closure, "fit closure")
    _same(
        fit["input_lineage"],
        {key: sorted(set(graph[key])) for key in closure},
        "canonical fit lineage",
    )
    _same(
        fit["admitted_external_ids"],
        sorted((*fit_ids, support_id)),
        "fit external declarations",
    )
    config = SpatialConfig(spec.length_scale_km, spec.ridge_penalty, support_id)
    coordinates = object_mapping(fit["training_coordinates"], "training_coordinates")
    supports = object_mapping(
        object_mapping(json.loads(admission.criterion_json), "criterion")["supports"],
        "supports",
    )
    for record in local_records:
        source = object_mapping(
            object_mapping(supports[record], "support")["source"], "source"
        )
        _same(
            coordinates[ownership[record]],
            {key: source[key] for key in ("latitude", "longitude")},
            "fit coordinates",
        )
    taxa = tuple(identity(value) for value in object_list(fit["taxa"], "taxa"))
    if taxa != tuple(
        sorted(
            identity(value) for value in object_list(spec.template()["taxa"], "taxa")
        )
    ):
        raise ValidationRefusal(
            "invalid_block_training_composition", "Fitted taxa differ"
        )
    centres = tuple(
        SiteCoordinate(
            **{
                key: finite_number(value)
                for key, value in object_mapping(
                    coordinates[group], "coordinate"
                ).items()
            }
        )
        for group in groups
    )
    features = tuple(
        finite_number(value)
        for value in object_list(fit["feature_mean"], "feature_mean")
    )
    means = tuple(
        finite_number(value) for value in object_list(fit["clr_mean"], "clr_mean")
    )
    coefficients = tuple(
        tuple(finite_number(value) for value in object_list(row, "coefficient row"))
        for row in object_list(fit["coefficients"], "coefficients")
    )
    if (
        len(features) != len(groups)
        or len(means) != len(taxa)
        or len(coefficients) != len(groups)
        or any(len(row) != len(taxa) for row in coefficients)
    ):
        raise ValidationRefusal("invalid_block_model_shape", fold.fold_id)
    FittedSpatialModel(
        fold,
        config,
        groups,
        taxa,
        centres,
        features,
        means,
        coefficients,
        canonical_json(fit),
        identity(state["model_sha256"]),
        admission,
    )
