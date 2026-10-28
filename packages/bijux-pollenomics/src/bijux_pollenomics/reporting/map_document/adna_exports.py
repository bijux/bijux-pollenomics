"""Read advertised aDNA exports without promoting their flat display projections."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from math import isfinite
from typing import cast

from ...adna.domain.models.localities import AdnaSampleChronologySupport
from ...core.temporal_semantics import admit_bp_interval

SAMPLE_SCHEMA = "adna-sample-record-export.v2"
LOCALITY_SCHEMA = "adna-locality-summary-export.v2"
EXPORT_PREFIXES = (
    "adna-sample-record-export.",
    "adna-locality-summary-export.",
    "adna-sample-geojson.",
    "adna-sample-geojson-collection.",
)
NUMERIC_POSTURES = frozenset(
    {"numeric_interval", "numeric_interval_with_caveat", "mixed_interval_and_context"}
)


def is_public_chronology_export(feature: Mapping[str, object]) -> bool:
    schema = feature.get("schema_version")
    return isinstance(schema, str) and schema.startswith(EXPORT_PREFIXES)


def _unavailable(reason: str, *, refused: bool) -> dict[str, object]:
    return {
        "schema_version": "temporal-semantics.v1",
        "comparability_posture": "refused" if refused else "contextual_label_only",
        "refusal_reason_code": reason if refused else "",
        "precision_posture": "not_carried_in_legacy_projection"
        if not refused
        else "unresolved",
        "comparison_note": reason,
    }


def _safe_source_integer(value: object) -> int | None:
    """Validate a JSON integer number without altering its retained source spelling."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("Owned sample bounds must be integer BP or null")
    if isinstance(value, float) and (not isfinite(value) or not value.is_integer()):
        raise ValueError("Owned sample bounds must be integer BP or null")
    if abs(value) > 2**53 - 1:
        raise ValueError("Owned sample bounds exceed the exact browser integer domain")
    return int(value)


def exported_record_semantics(
    feature: Mapping[str, object],
) -> dict[str, object] | None:
    """Derive supported sample semantics; legacy projections cannot recover omission.

    Locality v2 is handled by its independently validated owned components. Its
    coverage hull never becomes a singular sample chronology here.
    """
    schema = feature.get("schema_version")
    if schema == LOCALITY_SCHEMA:
        return None
    if isinstance(schema, str) and schema in {
        "adna-sample-record-export.v1",
        "adna-locality-summary-export.v1",
    }:
        return _unavailable(
            "Owned chronology metadata was not carried in this legacy projection; use the complete source export or a source-bound reconstruction.",
            refused=False,
        )
    if schema != SAMPLE_SCHEMA:
        return (
            _unavailable("unsupported_adna_export_schema", refused=True)
            if is_public_chronology_export(feature)
            else None
        )
    try:
        raw = feature.get("sample_chronology")
        identity = feature.get("sample_identity")
        if not isinstance(raw, Mapping) or not isinstance(identity, Mapping):
            raise ValueError(
                "Preferred sample export requires source chronology and identity"
            )
        chronology = raw.get("chronology")
        if not isinstance(chronology, Mapping):
            raise ValueError(
                "Preferred sample export requires source chronology fields"
            )
        required = {
            "original_text",
            "time_start_bp",
            "time_end_bp",
            "time_mean_bp",
            "date_stddev_bp",
            "source_mean_bp_text",
            "dating_basis",
            "evidence_class",
            "precision_posture",
            "refusal_reason_code",
        }
        if not required <= chronology.keys():
            raise ValueError("Preferred sample export chronology is incomplete")
        identifier = feature.get("genetic_id")
        namespace = feature.get("sample_namespace")
        if (
            not isinstance(identifier, str)
            or not identifier.strip()
            or not isinstance(namespace, str)
            or not namespace.strip()
        ):
            raise ValueError(
                "Preferred sample export requires explicit source identities"
            )
        if (
            raw.get("sample_id") != identifier
            or identity.get("stable_token") != identifier
            or identity.get("namespace") != namespace
        ):
            raise ValueError(
                "Preferred sample export identity disagrees with owned chronology"
            )
        if "sample_id" in feature and feature["sample_id"] != identifier:
            raise ValueError("Preferred sample export sample identity disagrees")
        for key in ("master_id", "group_id", "accession_lineage"):
            if (
                key not in feature
                or key not in identity
                or feature[key] != identity[key]
            ):
                raise ValueError("Preferred sample native identity disagrees")
        if any(not isinstance(feature[key], str) for key in ("master_id", "group_id")):
            raise ValueError(
                "Preferred sample native identifiers must remain source strings"
            )
        for key, value in identity.items():
            if (
                key not in {"namespace", "stable_token", "accession_lineage"}
                and key in feature
                and (type(feature[key]) is not type(value) or feature[key] != value)
            ):
                raise ValueError(
                    "Duplicated native identity disagrees with its source payload"
                )
        lineage = identity["accession_lineage"]
        if not isinstance(lineage, list) or not all(
            isinstance(item, str) for item in lineage
        ):
            raise ValueError("Preferred sample lineage must retain its source strings")
        numeric = {
            key: _safe_source_integer(chronology[key])
            for key in ("time_start_bp", "time_end_bp", "time_mean_bp")
        }
        for key, value in numeric.items():
            if key not in feature or _safe_source_integer(feature[key]) != value:
                raise ValueError(
                    "Flat projection disagrees with owned source chronology"
                )
        # JSON integer numbers may arrive as integral Python floats. The strict
        # internal model receives a validated copy; source assertions remain exact.
        support_payload = dict(raw)
        support_payload["chronology"] = {**chronology, **numeric}
        support = AdnaSampleChronologySupport.from_dict(support_payload)
        if not support.chronology.refusal_reason_code:
            admission = admit_bp_interval(
                support.chronology.time_start_bp, support.chronology.time_end_bp
            )
            if admission.refusal_reason_code:
                return _unavailable(admission.refusal_reason_code, refused=True)
            if (
                support.chronology.time_mean_bp is not None
                and support.chronology.time_mean_bp < 0
            ):
                return _unavailable("negative_bp", refused=True)
        source_family = feature.get("source_family")
        if not isinstance(source_family, str):
            raise ValueError("Preferred sample export requires its source family")
        semantics = support.chronology.as_temporal_semantics(
            source_family=source_family,
            provenance_path=support.provenance_path,
            provenance_locator=support.provenance_locator,
            provenance_excerpt=support.provenance_excerpt,
        )
        for key in ("reference_epoch", "age_type", "calibration_status", "model"):
            if key in raw:
                semantics[key] = deepcopy(raw[key])
        return semantics
    except (TypeError, ValueError, OverflowError):
        return _unavailable("malformed_or_conflicting_sample_export", refused=True)


def validate_locality_export_identity(feature: Mapping[str, object]) -> None:
    """Validate supplied native locality identity without inferring omitted fields."""
    identities = [
        feature[key] for key in ("identity", "locality_identity") if key in feature
    ]
    for identity in identities:
        if not isinstance(identity, Mapping):
            raise ValueError("Locality identity must retain its source object")
        if any(
            not isinstance(identity.get(key), str) or not str(identity[key]).strip()
            for key in ("namespace", "stable_token")
        ):
            raise ValueError("Locality identity requires native namespace and token")
        if not isinstance(identity.get("locality_text"), str):
            raise ValueError("Native locality text must remain a string")
        political = identity.get("political_entity")
        if political is not None and not isinstance(political, str):
            raise ValueError("Native locality geography must remain text or null")
        anchors = identity.get("source_anchor_tokens")
        if not isinstance(anchors, list) or any(
            not isinstance(value, str) for value in anchors
        ):
            raise ValueError("Native locality anchors must remain source strings")
        for outer, inner in (
            ("locality_namespace", "namespace"),
            ("locality_token", "stable_token"),
            ("political_entity", "political_entity"),
        ):
            # CSV has a declared one-way null-to-empty text projection. The
            # nested source identity retains null; no null is inferred from text.
            csv_empty_geography = (
                outer == "political_entity"
                and feature.get(outer) == ""
                and identity.get(inner) is None
            )
            if (
                outer in feature
                and feature[outer] != identity.get(inner)
                and not csv_empty_geography
            ):
                raise ValueError("Duplicated locality identity or geography disagrees")
    if len(identities) == 2 and identities[0] != identities[1]:
        raise ValueError("Locality identity payloads disagree")
    if (
        "political_entity" in feature
        and feature["political_entity"] is not None
        and not isinstance(feature["political_entity"], str)
    ):
        raise ValueError("Locality geography must remain text or null")


def validate_public_geojson_schemas(
    collection: Mapping[str, object], features: list[Mapping[str, object]]
) -> None:
    """Check declared collection/feature/property versions before stripping envelopes."""
    collection_schema = collection.get("schema_version")
    if "schema_version" in collection and not isinstance(collection_schema, str):
        raise ValueError("Malformed GeoJSON collection schema")
    versions = {
        "adna-sample-geojson-collection.v1": "v1",
        "adna-sample-geojson-collection.v2": "v2",
    }
    version = (
        versions.get(collection_schema) if isinstance(collection_schema, str) else None
    )
    sample_properties = any(
        isinstance(feature.get("properties"), Mapping)
        and str(
            cast(Mapping[str, object], feature["properties"]).get("schema_version", "")
        ).startswith("adna-sample-record-export.")
        for feature in features
    )
    if (
        (sample_properties or is_public_chronology_export(collection))
        and "schema_version" in collection
        and version is None
    ):
        raise ValueError("Unsupported sample GeoJSON collection schema")
    if (
        isinstance(collection_schema, str)
        and collection_schema.startswith("adna-sample-geojson-collection.")
        and version is None
    ):
        raise ValueError("Unsupported sample GeoJSON collection schema")
    for feature in features:
        feature_schema = feature.get("schema_version")
        if "schema_version" in feature and not isinstance(feature_schema, str):
            raise ValueError("Malformed GeoJSON feature schema")
        feature_versions = {
            "adna-sample-geojson.v1": "v1",
            "adna-sample-geojson.v2": "v2",
        }
        declared = (
            feature_versions.get(feature_schema)
            if isinstance(feature_schema, str)
            else None
        )
        properties = feature.get("properties")
        sample_property = isinstance(properties, Mapping) and str(
            properties.get("schema_version", "")
        ).startswith("adna-sample-record-export.")
        if (
            "schema_version" in feature
            and (sample_property or is_public_chronology_export(feature))
            and declared is None
        ):
            raise ValueError("Unsupported sample GeoJSON feature schema")
        if (
            isinstance(feature_schema, str)
            and feature_schema.startswith("adna-sample-geojson.")
            and declared is None
        ):
            raise ValueError("Unsupported sample GeoJSON feature schema")
        if version is not None and declared != version:
            raise ValueError("Sample GeoJSON collection and feature schemas disagree")
        if declared is not None:
            properties = feature.get("properties")
            if (
                not isinstance(properties, Mapping)
                or properties.get("schema_version")
                != "adna-sample-record-export." + declared
            ):
                raise ValueError("Sample GeoJSON feature and property schemas disagree")


def locality_export_records(
    payload: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    """Read a named locality wrapper into component-preserving record views."""
    schema = payload.get("schema_version")
    if not isinstance(schema, str) or schema not in {
        LOCALITY_SCHEMA,
        "adna-locality-summary-export.v1",
    }:
        raise ValueError("Unsupported locality export schema")
    rows = payload.get("localities")
    if not isinstance(rows, list) or not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("Locality export wrapper requires locality records")
    result: list[dict[str, object]] = []
    for row in rows:
        if "schema_version" in row and row["schema_version"] != schema:
            raise ValueError("Locality wrapper and record schemas disagree")
        view = {**deepcopy(dict(row)), "schema_version": schema}
        chronology = row.get("chronology")
        if isinstance(chronology, Mapping):
            for key in ("time_start_bp", "time_end_bp", "time_mean_bp"):
                if key in view and view[key] != chronology.get(key):
                    raise ValueError(
                        "Locality display projection disagrees with its source hull"
                    )
                view[key] = deepcopy(chronology.get(key))
            view.setdefault("time_label", chronology.get("original_text", ""))
        result.append(view)
    return tuple(result)
