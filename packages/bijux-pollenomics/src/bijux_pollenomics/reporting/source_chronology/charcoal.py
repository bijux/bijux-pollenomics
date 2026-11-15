"""Literal native CHAR observations as independently selectable display context.

The source ecological code identifies this surface. Material fractions, units,
values and detection states remain separate; no fire event or pollen evidence is
derived. One observation identity produces at most one map feature, irrespective
of the number of retained source ages.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Collection, Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
import json

from bijux_pollenomics.analysis.propagation.source_chronology.admission import (
    canonical_claim_interval,
    source_chronology_refusal_reason,
    source_coordinate,
)
from bijux_pollenomics.analysis.propagation.source_chronology.indexing import (
    select_source_chronology,
)
from bijux_pollenomics.collection.sources.neotoma.relational.identifiers import (
    source_reference_matches,
)
from bijux_pollenomics.core.geospatial.geojson import JsonObject

from .facets import COUNTRY_NAMES
from .features import canonical_neotoma_site_record_id

Row = Mapping[str, object]
LoadedSurface = tuple[Sequence[Row], Sequence[int]]
_LAYER_KEY = "neotoma-native-charcoal-context"
_ROLE = "native_charcoal_source_context"
_REFUSAL = "literal_source_observation_not_scientific_event"
_DISPLAY_POSTURE: JsonObject = {
    "key": _LAYER_KEY,
    "source_name": "Neotoma",
    "group": "environmental-context",
    "semantic_role": _ROLE,
    "node_level": "native_charcoal_observation",
    "contribution_role": "display_only",
    "default_enabled": False,
    "candidate_ranking_eligible": False,
    "scientific_classification_eligible": False,
    "scientific_selection_enabled": False,
    "propagation_status": "refused",
    "propagation_reason_code": _REFUSAL,
    "edge_count": 0,
}
_NATIVE_FIELDS = (
    "observation_id",
    "sample_id",
    "variable_id",
    "source_taxon_id",
    "source_reported_name",
    "source_ecological_group",
    "source_element",
    "source_element_type",
    "source_unit",
    "source_value",
    "source_denominator",
    "denominator_status",
    "detection_status",
    "unit_family",
    "source_context",
)


@dataclass(frozen=True)
class NativeCharcoalAtlasProjection:
    """A display-only observation layer and complete source-scope accounting."""

    point_layers: tuple[JsonObject, ...]
    reconciliation: JsonObject


def is_native_charcoal_context(layer: Mapping[str, object]) -> bool:
    """Identify this display surface and refuse contradictory analytical claims."""
    features = layer.get("features")
    identified = (
        layer.get("key") == _LAYER_KEY
        or layer.get("semantic_role") == _ROLE
        or layer.get("node_level") == "native_charcoal_observation"
        or (
            isinstance(features, list)
            and any(
                isinstance(feature, Mapping) and feature.get("semantic_role") == _ROLE
                for feature in features
            )
        )
    )
    if not identified:
        return False
    if any(
        type(layer.get(field)) is not type(expected) or layer.get(field) != expected
        for field, expected in _DISPLAY_POSTURE.items()
    ):
        raise ValueError("native charcoal display context posture differs")
    count = layer.get("count")
    if (
        not isinstance(features, list)
        or type(count) is not int
        or count != len(features)
    ):
        raise ValueError("native charcoal observation count differs")
    identities: set[str] = set()
    for feature in features:
        if not isinstance(feature, Mapping):
            raise ValueError("native charcoal feature is invalid")
        identity = _text(feature.get("observation_id"))
        if (
            identity is None
            or identity in identities
            or feature.get("node_id") != f"neotoma:native-charcoal:{identity}"
        ):
            raise ValueError("native charcoal observation identity differs")
        identities.add(identity)
        if any(
            (
                feature.get("semantic_role") != _ROLE,
                feature.get("node_level") != "native_charcoal_observation",
                feature.get("source_family") != "neotoma",
                feature.get("source_snapshot_id") != layer.get("source_snapshot_id"),
                feature.get("build_id") != layer.get("build_id"),
                feature.get("candidate_generation_status") != "refused",
                feature.get("candidate_refusal_reason") != _REFUSAL,
                feature.get("propagation_eligible") is not False,
                any(
                    type(feature.get(field)) is not int or feature[field] != 1
                    for field in ("record_count", "observation_denominator")
                ),
                bool(
                    {
                        "edge_id",
                        "target_record_id",
                        "direction",
                        "event_id",
                        "scientific_signal_ids",
                        "scientific_event_ids",
                    }
                    & feature.keys()
                ),
            )
        ):
            raise ValueError("native charcoal feature analytical posture differs")
    return True


def _text(value: object) -> str | None:
    return (
        value if isinstance(value, str) and value and value.strip() == value else None
    )


def _index(rows: Sequence[Row], field: str) -> dict[str, Row]:
    result = {}
    for row in rows:
        identity = _text(row.get(field))
        if identity is None or identity in result:
            raise ValueError(f"native charcoal requires unique {field}")
        result[identity] = row
    return result


def _same_fields(left: Row, right: Row, fields: Sequence[str]) -> bool:
    return all(left.get(field) == right.get(field) for field in fields)


def _sample_join(
    observation: Row, sample: Row | None, indexes: Mapping[str, Mapping[str, Row]]
) -> str | None:
    if sample is None:
        return "missing_source_sample"
    fields = ("site_id", "country_code", "source_snapshot_id", "build_id")
    if not _same_fields(
        observation, sample, (*fields, "dataset_id", "collection_unit_id")
    ):
        return "sample_source_relation_mismatch"
    for surface, identity_field, extra in (
        ("datasets", "dataset_id", ("collection_unit_id",)),
        ("collection_units", "collection_unit_id", ()),
    ):
        identity = _text(observation.get(identity_field))
        parent = indexes[surface].get(identity) if identity is not None else None
        if parent is None or not _same_fields(observation, parent, (*fields, *extra)):
            return "sample_source_parent_unavailable"
    variable_id = _text(observation.get("variable_id"))
    variable = (
        indexes["variables"].get(variable_id) if variable_id is not None else None
    )
    if variable is None or not _same_fields(
        observation, variable, ("source_snapshot_id", "build_id", "source_taxon_id")
    ):
        return "source_variable_identity_mismatch"
    return None


def _selected_age(
    observation: Row,
    sample: Row,
    site: Row,
    claims: Sequence[Row],
    models: Mapping[str, Row],
) -> tuple[Row | None, str]:
    selection = select_source_chronology(claims)
    claim = selection.claim
    if claim is None:
        return None, selection.selection_posture
    reason, _ = source_chronology_refusal_reason(observation, sample, site, claim)
    if reason is not None:
        return None, f"refused_{reason}"
    if (
        claim.get("subject_type") != "sample"
        or claim.get("subject_id") != sample["sample_id"]
        or not _same_fields(sample, claim, ("dataset_id", "collection_unit_id"))
    ):
        return None, "refused_source_age_parent_mismatch"
    identity = _text(claim.get("chronology_id"))
    model = models.get(identity) if identity is not None else None
    if model is None or not source_reference_matches(
        model.get("source_chronology_id"), model.get("source_chronology_id")
    ):
        return None, "refused_unidentified_source_chronology"
    if not _same_fields(
        observation,
        model,
        (
            "site_id",
            "country_code",
            "collection_unit_id",
            "source_snapshot_id",
            "build_id",
        ),
    ):
        return None, "refused_source_chronology_parent_mismatch"
    return claim, selection.selection_posture


def _time_label(interval: tuple[float | int, float | int] | None, posture: str) -> str:
    if interval is None:
        return f"Untimed source context: {posture}"
    younger, older = interval
    label = f"{younger} BP" if younger == older else f"{younger}–{older} BP"
    return f"{label} · selected source sample age; display only"


def build_native_charcoal_atlas_projection(
    loaded_surfaces: Mapping[str, LoadedSurface],
    *,
    projected_site_ids: Collection[str],
    source_snapshot_id: str,
    build_id: str,
) -> NativeCharcoalAtlasProjection:
    """Project authenticated original-epoch rows without scientific admission."""
    if _text(source_snapshot_id) is None or _text(build_id) is None:
        raise ValueError("native charcoal requires a bound source epoch")
    indexes = {
        surface: _index(loaded_surfaces.get(surface, ((), ()))[0], identity)
        for surface, identity in (
            ("sites", "site_id"),
            ("samples", "sample_id"),
            ("datasets", "dataset_id"),
            ("collection_units", "collection_unit_id"),
            ("variables", "variable_id"),
            ("chronologies", "chronology_id"),
        )
    }
    if not set(projected_site_ids) <= indexes["sites"].keys():
        raise ValueError("native charcoal projected sites are unknown")
    age_rows = loaded_surfaces.get("age_claims", ((), ()))[0]
    _index(age_rows, "chronology_claim_id")
    by_sample: dict[str, list[Row]] = defaultdict(list)
    for age_claim in age_rows:
        identities = {
            _text(age_claim.get(field)) for field in ("source_record_id", "subject_id")
        }
        for identity in identities - {None}:
            assert identity is not None
            by_sample[identity].append(age_claim)
    observations, parts = loaded_surfaces.get("observations", ((), ()))
    if len(observations) != len(parts) or any(
        type(part) is not int or part < 1 for part in parts
    ):
        raise ValueError("native charcoal observation part locators differ")
    charcoal = [
        (row, part)
        for row, part in zip(observations, parts, strict=True)
        if row.get("source_ecological_group") == "CHAR"
    ]
    _index([row for row, _ in charcoal], "observation_id")
    features: list[JsonObject] = []
    exclusions: list[JsonObject] = []
    source_countries: Counter[str] = Counter()
    material_types: Counter[str] = Counter()
    for observation, part in sorted(
        charcoal, key=lambda pair: str(pair[0]["observation_id"])
    ):
        site_id = _text(observation.get("site_id"))
        site = indexes["sites"].get(site_id) if site_id is not None else None
        country = _text(observation.get("country_code")) or "unassigned"
        source_countries[country] += 1
        material_types[
            json.dumps(
                [
                    observation.get("source_element"),
                    observation.get("source_element_type"),
                ],
                ensure_ascii=False,
            )
        ] += 1
        coordinates = source_coordinate(site) if site is not None else None
        reason = (
            "site_outside_projection"
            if site_id not in projected_site_ids
            else "ungoverned_country"
            if country not in COUNTRY_NAMES
            else "observation_source_lineage_mismatch"
            if site is None
            or not _same_fields(
                observation,
                site,
                ("site_id", "country_code", "source_snapshot_id", "build_id"),
            )
            or observation.get("source_snapshot_id") != source_snapshot_id
            or observation.get("build_id") != build_id
            else "missing_or_invalid_coordinates"
            if coordinates is None
            else None
        )
        if reason is not None:
            exclusions.append(
                {"observation_id": observation["observation_id"], "reason_code": reason}
            )
            continue
        assert site is not None and site_id is not None and coordinates is not None
        sample_id = _text(observation.get("sample_id"))
        sample = indexes["samples"].get(sample_id) if sample_id is not None else None
        join_reason = _sample_join(observation, sample, indexes)
        claims = sorted(
            by_sample.get(sample_id or "", ()),
            key=lambda row: str(row["chronology_claim_id"]),
        )
        claim, posture = (
            (None, f"refused_{join_reason}")
            if join_reason is not None or sample is None
            else _selected_age(
                observation, sample, site, claims, indexes["chronologies"]
            )
        )
        interval = canonical_claim_interval(claim) if claim is not None else None
        longitude, latitude, coordinate_quality = coordinates
        feature: JsonObject = {
            **{field: deepcopy(observation.get(field)) for field in _NATIVE_FIELDS},
            "record_id": canonical_neotoma_site_record_id(site_id),
            "node_id": f"neotoma:native-charcoal:{observation['observation_id']}",
            "node_level": "native_charcoal_observation",
            "semantic_role": _ROLE,
            "source_family": "neotoma",
            "source_snapshot_id": source_snapshot_id,
            "build_id": build_id,
            "site_id": site_id,
            "country": COUNTRY_NAMES[country],
            "latitude": latitude,
            "longitude": longitude,
            "coordinate_quality": coordinate_quality,
            "title": observation.get("source_reported_name")
            or "Literal CHAR observation",
            "subtitle": "Native charcoal observation; no fire inference",
            "source_record_id": sample_id,
            "collection_unit_id": observation.get("collection_unit_id"),
            "dataset_id": observation.get("dataset_id"),
            "record_count": 1,
            "observation_denominator": 1,
            "source_join_status": "retained" if join_reason is None else "refused",
            "source_join_refusal_reason": join_reason,
            "source_depth": deepcopy(sample.get("source_depth"))
            if sample is not None and join_reason is None
            else None,
            "source_depth_unit": None,
            "source_part_number": part,
            "source_observation_locator": f"surfaces/observations/part-{part:05d}.json#observation_id={observation['observation_id']}",
            "source_age_claim_ids": [row["chronology_claim_id"] for row in claims],
            "chronology_claim_id": claim.get("chronology_claim_id") if claim else None,
            "chronology_id": claim.get("chronology_id") if claim else None,
            "chronology_name": claim.get("chronology_name") if claim else None,
            "is_default_chronology": claim.get("is_default_chronology")
            if claim
            else None,
            "chronology_selection_posture": posture,
            "time_start_bp": interval[0] if interval else None,
            "time_end_bp": interval[1] if interval else None,
            "time_label": _time_label(interval, posture),
            "temporal_semantics": {
                "schema_version": "temporal-semantics.v1",
                "comparability_posture": "numeric_interval_with_caveat"
                if interval
                else "contextual_label_only",
                "evidence_class": "source_selected_sample_chronology"
                if interval
                else "literal_source_observation",
                "precision_posture": "source_reported_interval"
                if interval
                else "source_chronology_not_selected",
                "time_start_bp": interval[0] if interval else None,
                "time_end_bp": interval[1] if interval else None,
                "comparison_note": "Native observation context only; no fire, vegetation, cultivation or propagation event is inferred.",
            },
            "candidate_generation_status": "refused",
            "candidate_refusal_reason": _REFUSAL,
            "propagation_eligible": False,
        }
        features.append(feature)
    published_countries = Counter(str(feature["country"]) for feature in features)
    timed = sum(feature["time_start_bp"] is not None for feature in features)
    layer: JsonObject = {
        **_DISPLAY_POSTURE,
        "label": "Neotoma literal charcoal observations (CHAR)",
        "applies_country_filter": True,
        "applies_time_filter": True,
        "circle_enabled": True,
        "count": len(features),
        "features": features,
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "description": "Literal CHAR source observations, with native material/type, unit, denominator and detection states kept separate. No fire history, vegetation classification, pollen corroboration or propagation admission.",
        "coverage_label": "Original captured source scope only; zero is not national absence.",
        "traceability_artifact": "neotoma-relational/manifest.json",
        "style": {
            "fill": "#475569",
            "stroke": "#0f172a",
            "circleStroke": "#64748b",
            "circleFill": "rgba(100,116,139,0.10)",
        },
    }
    account: JsonObject = {
        "schema_version": "neotoma-native-charcoal-context.v1",
        "source_snapshot_id": source_snapshot_id,
        "build_id": build_id,
        "source_observation_denominator": len(observations),
        "native_charcoal_observation_count": len(charcoal),
        "published_observation_count": len(features),
        "excluded_observation_count": len(exclusions),
        "excluded_reason_counts": dict(
            sorted(Counter(str(row["reason_code"]) for row in exclusions).items())
        ),
        "excluded_observations": exclusions,
        "source_country_counts": {
            code: source_countries[code]
            for code in sorted(set(COUNTRY_NAMES) | set(source_countries))
        },
        "published_country_counts": {
            code: published_countries[COUNTRY_NAMES[code]]
            for code in sorted(COUNTRY_NAMES)
        },
        "published_site_count": len({feature["site_id"] for feature in features}),
        "timed_observation_count": timed,
        "untimed_observation_count": len(features) - timed,
        "chronology_selection_posture_counts": dict(
            sorted(
                Counter(
                    str(feature["chronology_selection_posture"]) for feature in features
                ).items()
            )
        ),
        "native_material_type_counts": [
            {
                "source_element": json.loads(key)[0],
                "source_element_type": json.loads(key)[1],
                "observation_count": count,
            }
            for key, count in sorted(material_types.items())
        ],
        "scientific_event_count": 0,
        "propagation_eligible_event_count": 0,
        "zero_count_semantics": "Zero describes this captured source scope, not a national absence or source availability decision.",
    }
    is_native_charcoal_context(layer)
    return NativeCharcoalAtlasProjection(point_layers=(layer,), reconciliation=account)


__all__ = [
    "NativeCharcoalAtlasProjection",
    "build_native_charcoal_atlas_projection",
    "is_native_charcoal_context",
]
