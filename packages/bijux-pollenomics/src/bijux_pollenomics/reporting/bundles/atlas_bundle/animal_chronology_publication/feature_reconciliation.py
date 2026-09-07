"""Projected feature reconciliation for chronology publication."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from .contract_values import mapping_rows, nonblank_text, nonnegative_integer


def validate_projected_features(
    accountability: Mapping[str, object],
    refusals: list[dict[str, object]],
    layers: list[dict[str, object]],
    artifact_name: str,
) -> None:
    """Validate traceability, feature identity, facets, and temporal bounds."""
    features = [
        feature
        for layer in layers
        for feature in mapping_rows(layer.get("features"), "layer features")
    ]
    feature_ids: set[str] = set()
    sample_ids: set[tuple[str, str]] = set()
    refusal_ids = {
        (
            nonblank_text(row.get("project_accession"), "refusal project"),
            nonblank_text(row.get("repo_stable_sample_id"), "refusal sample"),
        )
        for row in refusals
    }
    species: Counter[str] = Counter()
    projects: Counter[str] = Counter()
    precision: Counter[str] = Counter()
    coordinate_basis: Counter[str] = Counter()
    coordinate_confidence: Counter[str] = Counter()
    native_taxonomy: Counter[str] = Counter()
    for layer in layers:
        if layer.get("traceability_artifact") != artifact_name:
            raise ValueError("animal chronology layer traceability artifact differs")
        layer_species = nonblank_text(
            layer.get("project_species_latin_name"), "layer project species"
        )
        for feature in mapping_rows(layer.get("features"), "layer features"):
            feature_id = nonblank_text(feature.get("feature_id"), "feature id")
            identity = (
                nonblank_text(feature.get("project_accession"), "feature project"),
                nonblank_text(feature.get("repo_stable_sample_id"), "feature sample"),
            )
            if feature_id in feature_ids or identity in sample_ids:
                raise ValueError("animal chronology projected identity is duplicated")
            if feature_id != f"animal-source-chronology:{identity[0]}:{identity[1]}":
                raise ValueError("animal chronology feature identity format differs")
            if identity in refusal_ids:
                raise ValueError(
                    "animal chronology identity is both admitted and refused"
                )
            feature_ids.add(feature_id)
            sample_ids.add(identity)
            feature_species = nonblank_text(
                feature.get("project_species_latin_name"), "feature project species"
            )
            if feature_species != layer_species:
                raise ValueError("animal chronology feature species differs from layer")
            species[feature_species] += 1
            projects[identity[0]] += 1
            precision[
                nonblank_text(feature.get("chronology_precision_posture"), "precision")
            ] += 1
            coordinate_basis[
                nonblank_text(feature.get("coordinate_basis"), "coordinate basis")
            ] += 1
            coordinate_confidence[
                nonblank_text(
                    feature.get("coordinate_confidence"), "coordinate confidence"
                )
            ] += 1
            native_taxonomy[
                nonblank_text(
                    feature.get("source_native_taxonomy_status"), "taxonomy status"
                )
            ] += 1
    for field, observed in (
        ("species_counts", species),
        ("project_counts", projects),
        ("precision_counts", precision),
        ("coordinate_basis_counts", coordinate_basis),
        ("coordinate_confidence_counts", coordinate_confidence),
    ):
        if accountability.get(field) != dict(sorted(observed.items())):
            raise ValueError(f"animal chronology {field} differs from features")
    projected_count = len(features)
    expected_taxonomy = {
        "available_count": native_taxonomy["available"],
        "unavailable_count": native_taxonomy["unavailable"],
        "denominator": projected_count,
    }
    if set(native_taxonomy) - {"available", "unavailable"}:
        raise ValueError("animal chronology source-native taxonomy status differs")
    if accountability.get("source_native_taxonomy") != expected_taxonomy:
        raise ValueError("animal chronology source-native taxonomy counts differ")
    starts = [
        nonnegative_integer(feature.get("time_start_bp"), "feature time start")
        for feature in features
    ]
    ends = [
        nonnegative_integer(feature.get("time_end_bp"), "feature time end")
        for feature in features
    ]
    if accountability.get("time_min_bp") != (min(starts) if starts else None):
        raise ValueError("animal chronology projected minimum time differs")
    if accountability.get("time_max_bp") != (max(ends) if ends else None):
        raise ValueError("animal chronology projected maximum time differs")
