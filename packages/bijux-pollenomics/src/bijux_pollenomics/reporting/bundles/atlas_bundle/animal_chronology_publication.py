"""Fail-closed publication reconciliation for animal sample chronology."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
import hashlib
import json
from typing import Any

from ...adna.sample_chronology_context.integrity import refusal_rows_sha256

_GOVERNED_COUNTRIES = ("Denmark", "Finland", "Norway", "Sweden")
_REFUSAL_REASONS = (
    "sequencing_experiment_identity",
    "sample_identity_not_final",
    "source_chronology_not_comparable",
    "source_coordinate_not_mappable",
    "sample_provenance_unavailable",
    "chronology_provenance_unavailable",
    "site_provenance_unavailable",
)


def build_animal_chronology_publication(
    projection: Any, *, artifact_name: str
) -> tuple[dict[str, object], dict[str, object]]:
    """Reconcile projected nodes and refusals before emitting their contract."""
    input_identity = dict(_mapping(projection.input_identity.as_dict(), "input identity"))
    accountability = dict(_mapping(projection.accountability, "accountability"))
    corpus_identity = dict(_mapping(projection.corpus_identity, "corpus identity"))
    refusals = [
        dict(_mapping(refusal.as_dict(), "refusal")) for refusal in projection.refusals
    ]
    layers = _mapping_rows(projection.point_layers, "point layers")
    _validate_input_identity(accountability, input_identity)
    _validate_corpus_identity(accountability, input_identity, corpus_identity)
    _validate_refusals(accountability, refusals)
    _validate_counts(accountability, refusals, layers)
    _validate_projected_features(accountability, refusals, layers, artifact_name)
    _validate_country_accountability(accountability, layers)
    content: dict[str, object] = {
        "schema_version": "animal-sample-chronology-context-publication.v1",
        "accountability": accountability,
        "refusals": refusals,
        "input_identity": input_identity,
        "corpus_identity": corpus_identity,
    }
    content_sha256 = _canonical_sha256(content)
    payload = {**content, "content_sha256": content_sha256}
    return payload, {
        "artifact": artifact_name,
        "content_sha256": content_sha256,
        "input_identity_sha256": input_identity["combined_sha256"],
        "corpus_identity_sha256": corpus_identity["content_sha256"],
        "scope": accountability["scope"],
        "global_admitted_node_count": accountability["global_admitted_node_count"],
        "projected_node_count": accountability["projected_node_count"],
        "excluded_by_scope_count": accountability["excluded_by_scope_count"],
        "refusal_count": accountability["refusal_count"],
        "governed_country_rows": accountability["governed_country_rows"],
    }


def _validate_input_identity(
    accountability: Mapping[str, object], input_identity: Mapping[str, object]
) -> None:
    if accountability.get("input_identity") != input_identity:
        raise ValueError("animal chronology accountability input identity differs")
    combined = input_identity.get("combined_sha256")
    if (
        not isinstance(combined, str)
        or len(combined) != 64
        or any(character not in "0123456789abcdef" for character in combined)
    ):
        raise ValueError("animal chronology input identity is invalid")


def _validate_corpus_identity(
    accountability: Mapping[str, object],
    input_identity: Mapping[str, object],
    corpus_identity: Mapping[str, object],
) -> None:
    identity_content = dict(corpus_identity)
    declared_sha256 = identity_content.pop("content_sha256", None)
    if declared_sha256 != _canonical_sha256(identity_content):
        raise ValueError("animal chronology corpus content identity differs")
    if corpus_identity.get("input_identity_sha256") != input_identity.get(
        "combined_sha256"
    ):
        raise ValueError("animal chronology corpus input identity differs")
    for accountability_field, corpus_field in (
        ("source_counts", "source_counts"),
        ("refusal_counts", "refusal_counts"),
        ("refusal_rows_sha256", "refusal_rows_sha256"),
        ("global_admitted_node_count", "global_admitted_node_count"),
        ("country_rows", "country_rows"),
        ("governed_country_rows", "governed_country_rows"),
    ):
        if accountability.get(accountability_field) != corpus_identity.get(corpus_field):
            raise ValueError(
                f"animal chronology {accountability_field} differs from corpus identity"
            )


def _validate_refusals(
    accountability: Mapping[str, object], refusals: list[dict[str, object]]
) -> None:
    identities: set[tuple[str, str]] = set()
    reasons: Counter[str] = Counter()
    for row in refusals:
        if set(row) != {"project_accession", "repo_stable_sample_id", "reason_code"}:
            raise ValueError("animal chronology refusal fields differ")
        identity = (
            _text(row.get("project_accession"), "refusal project"),
            _text(row.get("repo_stable_sample_id"), "refusal sample"),
        )
        reason = _text(row.get("reason_code"), "refusal reason")
        if reason not in _REFUSAL_REASONS:
            raise ValueError("animal chronology refusal reason differs")
        if identity in identities:
            raise ValueError("animal chronology refusal identity is duplicated")
        identities.add(identity)
        reasons[reason] += 1
    expected_counts = {reason: reasons[reason] for reason in _REFUSAL_REASONS}
    if accountability.get("refusal_counts") != expected_counts:
        raise ValueError("animal chronology refusal reason counts differ")
    if accountability.get("refusal_count") != len(refusals):
        raise ValueError("animal chronology accountability refusal count differs")
    if accountability.get("refusal_rows_sha256") != refusal_rows_sha256(refusals):
        raise ValueError("animal chronology refusal content identity differs")


def _validate_counts(
    accountability: Mapping[str, object],
    refusals: list[dict[str, object]],
    layers: list[dict[str, object]],
) -> None:
    source_counts = _mapping(accountability.get("source_counts"), "source counts")
    global_count = _integer(
        accountability.get("global_admitted_node_count"), "global admitted count"
    )
    projected_count = _integer(
        accountability.get("projected_node_count"), "projected count"
    )
    excluded_count = _integer(
        accountability.get("excluded_by_scope_count"), "excluded count"
    )
    if global_count != projected_count + excluded_count:
        raise ValueError("animal chronology projected count does not reconcile")
    if _integer(source_counts.get("admitted_node_count"), "source admitted count") != global_count:
        raise ValueError("animal chronology source admitted count differs")
    if _integer(source_counts.get("refused_master_row_count"), "source refusal count") != len(refusals):
        raise ValueError("animal chronology source refusal count differs")
    master_count = _integer(source_counts.get("sample_master_row_count"), "master count")
    if master_count != global_count + len(refusals):
        raise ValueError("animal chronology master dispositions do not reconcile")
    refusal_counts = _mapping(accountability.get("refusal_counts"), "refusal counts")
    experiment_count = _integer(
        refusal_counts.get("sequencing_experiment_identity"),
        "sequencing experiment refusal count",
    )
    biological_count = master_count - experiment_count
    for field in ("sample_chronology_row_count", "sample_site_row_count"):
        if _integer(source_counts.get(field), field) != biological_count:
            raise ValueError("animal chronology companion row counts do not reconcile")
    project_count = _integer(source_counts.get("project_count"), "source project count")
    input_identity = _mapping(accountability.get("input_identity"), "input identity")
    artifact_count = _integer(input_identity.get("artifact_count"), "input artifact count")
    if artifact_count != 1 + (project_count * 3):
        raise ValueError("animal chronology project input inventory does not reconcile")
    if len(layers) != 6:
        raise ValueError("animal chronology publication requires six species layers")
    layer_keys = {_text(layer.get("key"), "layer key") for layer in layers}
    if len(layer_keys) != len(layers):
        raise ValueError("animal chronology layer identity is duplicated")
    layer_count = 0
    for layer in layers:
        features = _mapping_rows(layer.get("features"), "layer features")
        declared = _integer(layer.get("count"), "layer count")
        if declared != len(features):
            raise ValueError("animal chronology layer count differs from features")
        layer_count += declared
    if layer_count != projected_count:
        raise ValueError("animal chronology layer counts differ from projection")


def _validate_projected_features(
    accountability: Mapping[str, object],
    refusals: list[dict[str, object]],
    layers: list[dict[str, object]],
    artifact_name: str,
) -> None:
    features = [
        feature
        for layer in layers
        for feature in _mapping_rows(layer.get("features"), "layer features")
    ]
    feature_ids: set[str] = set()
    sample_ids: set[tuple[str, str]] = set()
    refusal_ids = {
        (
            _text(row.get("project_accession"), "refusal project"),
            _text(row.get("repo_stable_sample_id"), "refusal sample"),
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
        layer_species = _text(
            layer.get("project_species_latin_name"), "layer project species"
        )
        for feature in _mapping_rows(layer.get("features"), "layer features"):
            feature_id = _text(feature.get("feature_id"), "feature id")
            identity = (
                _text(feature.get("project_accession"), "feature project"),
                _text(feature.get("repo_stable_sample_id"), "feature sample"),
            )
            if feature_id in feature_ids or identity in sample_ids:
                raise ValueError("animal chronology projected identity is duplicated")
            if feature_id != f"animal-source-chronology:{identity[0]}:{identity[1]}":
                raise ValueError("animal chronology feature identity format differs")
            if identity in refusal_ids:
                raise ValueError("animal chronology identity is both admitted and refused")
            feature_ids.add(feature_id)
            sample_ids.add(identity)
            feature_species = _text(
                feature.get("project_species_latin_name"), "feature project species"
            )
            if feature_species != layer_species:
                raise ValueError("animal chronology feature species differs from layer")
            species[feature_species] += 1
            projects[identity[0]] += 1
            precision[_text(feature.get("chronology_precision_posture"), "precision")] += 1
            coordinate_basis[_text(feature.get("coordinate_basis"), "coordinate basis")] += 1
            coordinate_confidence[
                _text(feature.get("coordinate_confidence"), "coordinate confidence")
            ] += 1
            native_taxonomy[
                _text(feature.get("source_native_taxonomy_status"), "taxonomy status")
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
    starts = [_integer(feature.get("time_start_bp"), "feature time start") for feature in features]
    ends = [_integer(feature.get("time_end_bp"), "feature time end") for feature in features]
    if accountability.get("time_min_bp") != (min(starts) if starts else None):
        raise ValueError("animal chronology projected minimum time differs")
    if accountability.get("time_max_bp") != (max(ends) if ends else None):
        raise ValueError("animal chronology projected maximum time differs")


def _validate_country_accountability(
    accountability: Mapping[str, object], layers: list[dict[str, object]]
) -> None:
    country_rows = _mapping_rows(accountability.get("country_rows"), "country rows")
    names = [row.get("country_name") for row in country_rows]
    expected_order = sorted(name for name in names if isinstance(name, str))
    if names != [*expected_order, None] or len(set(names)) != len(names):
        raise ValueError("animal chronology country row identity or order differs")
    global_count = _integer(
        accountability.get("global_admitted_node_count"), "global admitted count"
    )
    if sum(_country_row_count(row) for row in country_rows) != global_count:
        raise ValueError("animal chronology country rows do not reconcile")
    by_country = {row.get("country_name"): row for row in country_rows}
    governed = _mapping_rows(
        accountability.get("governed_country_rows"), "governed country rows"
    )
    if [row.get("country_name") for row in governed] != list(_GOVERNED_COUNTRIES):
        raise ValueError("animal chronology governed country identity differs")
    if any(
        row
        != by_country.get(
            row.get("country_name"),
            {
                "country_name": row.get("country_name"),
                "node_count": 0,
                "time_min_bp": None,
                "time_max_bp": None,
            },
        )
        for row in governed
    ):
        raise ValueError("animal chronology governed country rows differ")
    for row in country_rows:
        _validate_country_row_bounds(row)

    scope = _mapping(accountability.get("scope"), "scope")
    scope_kind = _text(scope.get("kind"), "scope kind")
    scope_countries_value = scope.get("countries")
    if not isinstance(scope_countries_value, list) or any(
        not isinstance(country, str) or not country for country in scope_countries_value
    ):
        raise ValueError("animal chronology scope countries are invalid")
    scope_countries = set(scope_countries_value)
    features = [
        feature
        for layer in layers
        for feature in _mapping_rows(layer.get("features"), "layer features")
    ]
    if scope_kind == "world":
        if scope_countries:
            raise ValueError("animal chronology world scope countries differ")
        observed = _country_rows_from_features(features)
        if observed != country_rows:
            raise ValueError("animal chronology global country rows differ from features")
    elif any(str(feature.get("country") or "") not in scope_countries for feature in features):
        raise ValueError("animal chronology projected feature is outside scope")


def _country_rows_from_features(
    features: list[dict[str, object]],
) -> list[dict[str, object]]:
    countries = sorted({str(feature.get("country")) for feature in features if feature.get("country")})
    rows = [_feature_country_row(country, features) for country in countries]
    rows.append(_feature_country_row(None, features))
    return rows


def _feature_country_row(
    country: str | None, features: list[dict[str, object]]
) -> dict[str, object]:
    selected = [
        feature
        for feature in features
        if (str(feature.get("country")) if feature.get("country") else None) == country
    ]
    return {
        "country_name": country,
        "node_count": len(selected),
        "time_min_bp": min(
            (_integer(feature.get("time_start_bp"), "feature time start") for feature in selected),
            default=None,
        ),
        "time_max_bp": max(
            (_integer(feature.get("time_end_bp"), "feature time end") for feature in selected),
            default=None,
        ),
    }


def _country_row_count(row: Mapping[str, object]) -> int:
    return _integer(row.get("node_count"), "country node count")


def _validate_country_row_bounds(row: Mapping[str, object]) -> None:
    count = _country_row_count(row)
    minimum = row.get("time_min_bp")
    maximum = row.get("time_max_bp")
    if count == 0:
        if minimum is not None or maximum is not None:
            raise ValueError("animal chronology empty country has non-null bounds")
        return
    if _integer(minimum, "country minimum time") > _integer(maximum, "country maximum time"):
        raise ValueError("animal chronology country time bounds are inverted")


def _mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise ValueError(f"animal chronology {label} is invalid")
    return value


def _mapping_rows(value: object, label: str) -> list[dict[str, object]]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"animal chronology {label} are invalid")
    rows: list[dict[str, object]] = []
    for item in value:
        rows.append(dict(_mapping(item, label)))
    return rows


def _integer(value: object, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"animal chronology {label} is invalid")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"animal chronology {label} is invalid")
    return value


def _canonical_sha256(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


__all__ = ["build_animal_chronology_publication"]
