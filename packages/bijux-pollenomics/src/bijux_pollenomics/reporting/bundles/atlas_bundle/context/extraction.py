"""Context-point extraction and animal atlas summary accounting."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .....adna.domain.locality import mapping_sample_chronologies
from .....collection.contracts.cardinality import resolve_declared_count
from .....collection.contracts.occurrence_chronology import ContextOccurrenceSupport
from ....context.time import feature_time_payload
from ....map_document.temporal_admission import feature_temporal_admission
from ..layers import is_animal_chronology_context


def extract_context_points(
    point_layers: list[dict[str, object]], *, surface: Any
) -> tuple[Any, ...]:
    records = []
    for layer in point_layers:
        if is_animal_chronology_context(layer):
            continue
        if str(layer.get("group", "")).strip() == "primary-evidence":
            continue
        raw_points = layer.get("features")
        if not isinstance(raw_points, list):
            continue
        for raw_point in raw_points:
            if not isinstance(raw_point, dict):
                continue
            latitude = raw_point.get("latitude")
            longitude = raw_point.get("longitude")
            if (
                isinstance(latitude, bool)
                or not isinstance(latitude, (int, float))
                or isinstance(longitude, bool)
                or not isinstance(longitude, (int, float))
            ):
                continue
            time_payload = feature_time_payload(raw_point)
            temporal_semantics = time_payload.get("temporal_semantics")
            source_record = raw_point.get(
                "source_record", time_payload.get("source_record")
            )
            occurrence_supports: tuple[ContextOccurrenceSupport, ...] | None = None
            if "sample_chronologies" in raw_point:
                occurrence_supports = ()
            if (
                "sample_chronologies" in raw_point
                and feature_temporal_admission(raw_point)[0] == "admitted"
            ):
                occurrence_supports = tuple(
                    ContextOccurrenceSupport(
                        support_id=support.sample_id,
                        time_start_bp=support.chronology.time_start_bp,
                        time_end_bp=support.chronology.time_end_bp,
                        temporal_semantics={
                            **support.chronology.as_temporal_semantics(
                                source_family=str(raw_point.get("source_family", "")),
                                provenance_path=support.provenance_path,
                                provenance_locator=support.provenance_locator,
                                provenance_excerpt=support.provenance_excerpt,
                            ),
                            **{
                                key: support.as_dict()[key]
                                for key in (
                                    "reference_epoch",
                                    "age_type",
                                    "calibration_status",
                                    "model",
                                )
                            },
                        },
                    )
                    for support in mapping_sample_chronologies(raw_point)
                )
            native_record_id = raw_point.get("evidence_row_id")
            record_id = str(raw_point.get("title", ""))
            if (
                raw_point.get("schema_version")
                in ("adna-sample-record-export.v2", "adna-locality-summary-export.v2")
                and isinstance(native_record_id, str)
                and native_record_id.strip()
            ):
                record_id = native_record_id
            records.append(
                surface.ContextPointRecord(
                    source=str(layer.get("source_name", "")),
                    layer_key=str(layer.get("key", "")),
                    layer_label=str(layer.get("label", "")),
                    category=str(raw_point.get("subtitle", "")),
                    country=str(raw_point.get("country", "")),
                    record_id=record_id,
                    name=str(raw_point.get("title", "")),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    geometry_type="Point",
                    subtitle=str(raw_point.get("subtitle", "")),
                    description=str(layer.get("description", "")),
                    source_url=str(raw_point.get("source_url", "")),
                    record_count=resolve_declared_count(
                        raw_point,
                        "record_count",
                        field=(
                            "atlas context feature "
                            f"{str(raw_point.get('title', '')).strip() or '<unknown>'} "
                            "record_count"
                        ),
                        absent_default=1,
                    ),
                    popup_rows=(),
                    time_start_bp=time_payload["time_start_bp"],
                    time_end_bp=time_payload["time_end_bp"],
                    time_mean_bp=time_payload["time_mean_bp"],
                    time_label=str(time_payload["time_label"]),
                    temporal_semantics=(
                        temporal_semantics
                        if isinstance(temporal_semantics, dict)
                        else None
                    ),
                    occurrence_supports=occurrence_supports,
                    source_record=deepcopy(source_record)
                    if isinstance(source_record, dict)
                    else None,
                    site_uuid=(
                        str(raw_point["site_uuid"]).strip()
                        if isinstance(raw_point.get("site_uuid"), str)
                        and str(raw_point["site_uuid"]).strip()
                        else None
                    ),
                )
            )
    return tuple(records)


def as_optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
