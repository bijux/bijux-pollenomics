"""Target-specific forward preparation after actual training reconstructions."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import Protocol, cast

from ....core.geospatial.distance import wgs84_inverse_geodesic
from ...lra.engine.discovery import load_engine
from ..contracts import Fold, ValidationRefusal, finite_number, manifest_sha256
from ..prediction import ForwardInputs, ForwardModel, predict_withheld_site
from .configuration import (
    ExperimentSite,
    ExperimentSpec,
    identity,
    object_list,
    object_mapping,
)
from .inputs import read_geometry
from .reconstruction import FoldFits


class PreparedGeometry(Protocol):
    """Only the public prepared-input fields consumed by this host adapter."""

    taxa: tuple[str, ...]
    local_k: Iterable[Iterable[float]]
    terrestrial_fraction: Iterable[float]
    ppe: Iterable[float]
    regional_deposition: Iterable[float]
    full_k: Iterable[Iterable[float]]
    full_terrestrial_fraction: Iterable[float]
    ring_bounds_m: Iterable[Iterable[float]]
    regional_cover: Iterable[float]
    method_profile: str
    preparation_profile: str
    geometry_profile: str
    regional_cutoff_m: float
    deposition_units: str


def _support(
    spec: ExperimentSpec,
    geometry: dict[str, object],
    anchor_geometry: dict[str, object],
) -> str:
    metadata = object_mapping(geometry["sample_metadata"], "sample_metadata")
    anchor = object_mapping(anchor_geometry["sample_metadata"], "anchor_metadata")
    for field in ("bin_id", "coordinate", "age_type"):
        if metadata[field] != anchor[field]:
            raise ValidationRefusal("incompatible_target_time", field)
    coordinate = metadata["coordinate"]
    finite_number(coordinate)
    if isinstance(coordinate, int) and int(float(coordinate)) != coordinate:
        raise ValidationRefusal(
            "inexact_pairing_coordinate", "Target coordinate loses precision"
        )
    matching = object_mapping(spec.template()["temporal_matching"], "temporal_matching")
    bins = object_list(matching["bins"], "bins")
    if len(bins) != 1:
        raise ValidationRefusal(
            "unsupported_experiment_time", "Initial profile requires one declared bin"
        )
    bounds = object_mapping(bins[0], "bin")
    if bounds["bin_id"] != metadata["bin_id"] or metadata["age_type"] not in {
        "calendar_bp",
        "radiocarbon_bp",
    }:
        raise ValidationRefusal(
            "incompatible_target_time", "Target bin or chronology unit differs"
        )
    intervals = object_list(metadata["age_support_bp"], "age_support_bp")
    if not intervals:
        raise ValidationRefusal("incompatible_target_time", "Target support is empty")
    for value in intervals:
        pair = object_list(value, "age_interval")
        if len(pair) != 2:
            raise ValidationRefusal(
                "incompatible_target_time", "Expected younger/older BP bounds"
            )
        younger, older = map(finite_number, pair)
        if (
            not finite_number(bounds["younger_bp"])
            <= younger
            <= older
            <= finite_number(bounds["older_bp"])
        ):
            raise ValidationRefusal(
                "incompatible_target_time", "Target support is outside the declared bin"
            )
    return identity(metadata["bin_id"])


def predict_fold(
    spec: ExperimentSpec,
    fold: Fold,
    target: ExperimentSite,
    fits: FoldFits,
    group_by_record: dict[str, str],
    *,
    input_root: Path,
) -> tuple[list[dict[str, object]], dict[str, object]]:
    """Use existing baseline and forward APIs; target pollen is never opened."""
    import pandas as pd

    geometry = read_geometry(input_root, target, spec)
    anchor_geometry = read_geometry(input_root, fits.anchor, spec)
    bin_id = _support(spec, geometry, anchor_geometry)
    template = spec.template()
    parameters = [
        object_mapping(row, "parameter")
        for row in object_list(template["parameters"], "parameters")
    ]
    # Explicit host→engine field/unit map; neither aliases nor units are guessed.
    params = pd.DataFrame(
        {
            "Taxon": [row["taxon"] for row in parameters],
            "fallspeed": [row["fallspeed_m_s"] for row in parameters],
            "ppe": [row["ppe"] for row in parameters],
            "ppe.error": [row["ppe_sd"] for row in parameters],
        }
    )
    ring_rows = [
        object_mapping(row, "ring")
        for row in object_list(geometry["forward_rings"], "forward_rings")
    ]
    rings = pd.DataFrame(
        {
            key: [row[source] for row in ring_rows]
            for key, source in (
                ("inner", "inner_m"),
                ("outer", "outer_m"),
                ("mean", "mean_m"),
                ("ring", "ring_area_m2"),
                ("terrestrial", "terrestrial_area_m2"),
            )
        }
    )
    basin = object_mapping(geometry["basin"], "basin")
    if basin["site_type"] != "lake":
        raise ValidationRefusal(
            "unsupported_target_basin", "Initial local profile requires a lake"
        )
    love = object_mapping(
        object_mapping(template["configuration"], "configuration")["love"], "love"
    )
    binding = load_engine()
    for name in ("ForwardConfig", "prepare_forward_inputs", "forward_deposition"):
        if not callable(getattr(binding.api, name, None)):
            raise ValidationRefusal("forward_preparation_unavailable", name)
    config = binding.api.ForwardConfig(
        local_ring_count=spec.local_ring_count,
        local_basin_diameter_m=basin["diameter_m"],
        distance_weighting=love.get("distance_weighting", "lsm unstable"),
        regional_cover_profile="disqover-rounded-fractions",
    )
    prepared = cast(
        PreparedGeometry,
        binding.api.prepare_forward_inputs(params, rings, fits.regional_cover, config),
    )
    taxa = tuple(str(value) for value in object_list(template["taxa"], "taxa"))
    if prepared.taxa != taxa:
        raise ValidationRefusal(
            "taxon_denominator_mismatch",
            "Prepared target and reconstruction order differ",
        )
    predictor_groups = tuple(
        group_by_record[site.record.record_id] for site in fits.predictors
    )
    distances = {}
    for site in fits.predictors:
        other = read_geometry(input_root, site, spec)
        distance = wgs84_inverse_geodesic(
            longitude_a=finite_number(geometry["longitude"]),
            latitude_a=finite_number(geometry["latitude"]),
            longitude_b=finite_number(other["longitude"]),
            latitude_b=finite_number(other["latitude"]),
        )
        distances[group_by_record[site.record.record_id]] = (
            distance.distance_km_unrounded
        )
    regional_id = "experiment-regional:" + manifest_sha256(
        {"anchor": fits.anchor.record.record_id, "fits": fits.fit_identities}
    )
    params_id = "experiment-parameters:" + manifest_sha256(
        {"parameters": template["parameters"], "evidence": template["evidence"]}
    )
    geometry_id = "experiment-geometry:" + target.geometry.sha256
    time_id = "experiment-time:" + manifest_sha256(
        {
            "metadata": geometry["sample_metadata"],
            "matching": template["temporal_matching"],
        }
    )
    graph: dict[str, tuple[str, ...]] = dict.fromkeys(fold.train_record_ids, ())
    derived = {
        regional_id: fold.train_record_ids,
        params_id: (),
        geometry_id: (),
        time_id: (),
    }
    if set(graph) & set(derived) or len(derived) != 4:
        raise ValidationRefusal("experiment_identity_collision", fold.fold_id)
    graph.update(derived)
    context = ForwardInputs(
        taxa=taxa,
        regional_deposition=tuple(prepared.regional_deposition),
        local_k=tuple(tuple(row) for row in prepared.local_k),
        terrestrial_fraction=tuple(prepared.terrestrial_fraction),
        ppe=tuple(prepared.ppe),
        regional_input_ids=(regional_id,),
        parameter_input_ids=(params_id,),
        geometry_input_ids=(geometry_id,),
        temporal_support_id=time_id,
        method_profile=prepared.method_profile,
        engine_build_id=manifest_sha256(binding.as_dict()),
    )
    rows: list[dict[str, object]] = []
    for method in spec.baselines:
        prediction = predict_withheld_site(
            fold,
            group_by_record[target.record.record_id],
            fits.compositions,
            context,
            cast(ForwardModel, binding.api.forward_deposition),
            spatial_method=method,
            training_input_ids=fold.train_record_ids,
            dependency_graph=graph,
            admitted_external_ids=tuple(derived),
            distances_km=distances,
            predictor_group_ids=predictor_groups,
        )
        rows.append(
            {
                "fold_id": fold.fold_id,
                "record_id": target.record.record_id,
                "bin_id": bin_id,
                "baseline": method,
                "vegetation_fraction": dict(prediction.vegetation_fraction),
                "pollen_fraction": dict(prediction.pollen_fraction),
                "prediction_manifest_sha256": prediction.prediction_manifest_sha256,
                "prediction_manifest": object_mapping(
                    json.loads(prediction.input_manifest_json), "prediction_manifest"
                ),
            }
        )
    details: dict[str, object] = {
        "preparation_profile": prepared.preparation_profile,
        "forward_method_profile": prepared.method_profile,
        "geometry_profile": prepared.geometry_profile,
        "deposition_units": prepared.deposition_units,
        "full_k": [list(row) for row in prepared.full_k],
        "full_terrestrial_fraction": list(prepared.full_terrestrial_fraction),
        "ring_bounds_m": [list(row) for row in prepared.ring_bounds_m],
        "regional_cutoff_m": prepared.regional_cutoff_m,
        "regional_cover": list(prepared.regional_cover),
        "forward_inputs": context.as_dict(),
        "distances_km": distances,
        "target_geometry_sha256": target.geometry.sha256,
        "regional_anchor_record_id": fits.anchor.record.record_id,
        "regional_value_source_record_ids": [fits.anchor.record.record_id],
        "regional_identity_source_record_ids": fold.train_record_ids,
        "regional_identity_policy": "conservative_all_training_fit_receipts",
        "regional_anchor_group_id": group_by_record[fits.anchor.record.record_id],
        "predictor_group_ids": predictor_groups,
        "outer_fold": fold.as_dict(),
        "support_profile": spec.support_profile,
        "local_support_radius_m": spec.local_support_radius_m,
        "declared_target_inversion_rings": geometry["inversion_rings"],
        "declared_target_forward_rings": geometry["forward_rings"],
    }
    return rows, details
