"""Build source-traceable SEAD chronology and bibliography records."""

from __future__ import annotations

from collections.abc import Mapping

from bijux_pollenomics.core.bp_time import normalize_bp_interval
from bijux_pollenomics.core.text import clean_optional_text

from .values import parse_optional_int, parse_required_int
from .temporal import (
    _interval_from_relative_age_label,
    _normalize_optional_interval,
    _normalized_period_label,
    _relative_interval_from_range,
    sead_dating_interval,
)

def _build_relative_period_row(
    relative_date: dict[str, object],
    *,
    site_id: int,
    relative_age: Mapping[str, object],
    method: Mapping[str, object],
    uncertainty: Mapping[str, object],
    relation_identity: dict[str, int | None],
) -> dict[str, object]:
    label = str(relative_age.get("label", "")).strip()
    description = str(relative_age.get("description", "")).strip()
    cal_younger = parse_optional_int(relative_age.get("cal_age_younger"))
    cal_older = parse_optional_int(relative_age.get("cal_age_older"))
    c14_younger = parse_optional_int(relative_age.get("c14_age_younger"))
    c14_older = parse_optional_int(relative_age.get("c14_age_older"))
    interval = _normalize_optional_interval(
        cal_younger if cal_younger is not None else c14_younger,
        cal_older if cal_older is not None else c14_older,
    )
    interval_source = "relative_age_bounds"
    if interval is None:
        interval = _interval_from_relative_age_label(label)
        interval_source = "encoded_relative_age_label" if interval else "unresolved"
    return {
        **relation_identity,
        "site_id": site_id,
        "relative_date_id": parse_required_int(relative_date.get("relative_date_id")),
        "relative_age_id": parse_optional_int(relative_date.get("relative_age_id")),
        "dating_uncertainty_id": parse_optional_int(
            relative_date.get("dating_uncertainty_id")
        ),
        "method_id": parse_optional_int(relative_date.get("method_id")),
        "relative_age_label": label,
        "relative_age_description": description,
        "relative_age_abbreviation": str(relative_age.get("abbreviation", "")).strip(),
        "normalized_period_label": _normalized_period_label(label, description),
        "method_name": str(method.get("name", "")).strip()
        or str(method.get("alternate_name", "")).strip(),
        "uncertainty_label": str(uncertainty.get("label", "")).strip(),
        "uncertainty_description": str(uncertainty.get("description", "")).strip(),
        "notes": clean_optional_text(relative_date.get("notes")),
        "interval_source": interval_source,
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _build_dating_range_row(
    dating_range: dict[str, object],
    *,
    age_type: str,
    age_type_description: str,
    uncertainty: Mapping[str, object],
    relation_identity: dict[str, int | None],
) -> dict[str, object]:
    interval = sead_dating_interval(dating_range, age_type=age_type) or (
        _relative_interval_from_range(dating_range, age_type=age_type)
    )
    return {
        **relation_identity,
        "analysis_dating_range_id": parse_required_int(
            dating_range.get("analysis_dating_range_id")
        ),
        "analysis_value_id": parse_required_int(dating_range.get("analysis_value_id")),
        "age_type_id": parse_optional_int(dating_range.get("age_type_id")),
        "dating_uncertainty_id": parse_optional_int(
            dating_range.get("dating_uncertainty_id")
        ),
        "age_type": age_type,
        "age_type_description": age_type_description,
        "low_value": parse_optional_int(dating_range.get("low_value")),
        "high_value": parse_optional_int(dating_range.get("high_value")),
        "low_qualifier": clean_optional_text(dating_range.get("low_qualifier")),
        "high_qualifier": clean_optional_text(dating_range.get("high_qualifier")),
        "low_is_uncertain": bool(dating_range.get("low_is_uncertain")),
        "high_is_uncertain": bool(dating_range.get("high_is_uncertain")),
        "uncertainty_label": str(uncertainty.get("label", "")).strip(),
        "uncertainty_description": str(uncertainty.get("description", "")).strip(),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _analysis_entity_age_interval(
    entity_age: dict[str, object],
) -> tuple[int, int] | None:
    age = parse_optional_int(entity_age.get("age"))
    younger = parse_optional_int(entity_age.get("age_younger"))
    older = parse_optional_int(entity_age.get("age_older"))
    return _normalize_optional_interval(
        younger if younger is not None else age,
        older if older is not None else age,
    )


def _build_analysis_entity_age_row(
    entity_age: dict[str, object],
    *,
    interval: tuple[int, int] | None,
    relation_identity: dict[str, int | None],
) -> dict[str, object]:
    return {
        **relation_identity,
        "analysis_entity_age_id": parse_required_int(
            entity_age.get("analysis_entity_age_id")
        ),
        "analysis_entity_id": parse_required_int(entity_age.get("analysis_entity_id")),
        "chronology_id": parse_optional_int(entity_age.get("chronology_id")),
        "dating_specifier": clean_optional_text(entity_age.get("dating_specifier")),
        "age": parse_optional_int(entity_age.get("age")),
        "age_older": parse_optional_int(entity_age.get("age_older")),
        "age_younger": parse_optional_int(entity_age.get("age_younger")),
        "age_range": clean_optional_text(entity_age.get("age_range")),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _geochronology_interval(
    geochronology_row: dict[str, object],
) -> tuple[int, int] | None:
    age = parse_optional_int(geochronology_row.get("age"))
    if age is None:
        return None
    error_older = parse_optional_int(geochronology_row.get("error_older")) or 0
    error_younger = parse_optional_int(geochronology_row.get("error_younger")) or 0
    return normalize_bp_interval(max(0, age - error_younger), age + error_older)


def _build_geochronology_row(
    geochronology_row: dict[str, object],
    *,
    interval: tuple[int, int] | None,
    uncertainty: Mapping[str, object],
    relation_identity: dict[str, int | None],
) -> dict[str, object]:
    return {
        **relation_identity,
        "geochron_id": parse_required_int(geochronology_row.get("geochron_id")),
        "analysis_entity_id": parse_required_int(
            geochronology_row.get("analysis_entity_id")
        ),
        "dating_lab_id": parse_optional_int(geochronology_row.get("dating_lab_id")),
        "lab_number": clean_optional_text(geochronology_row.get("lab_number")),
        "age": parse_optional_int(geochronology_row.get("age")),
        "error_older": parse_optional_int(geochronology_row.get("error_older")),
        "error_younger": parse_optional_int(geochronology_row.get("error_younger")),
        "notes": clean_optional_text(geochronology_row.get("notes")),
        "dating_uncertainty_id": parse_optional_int(
            geochronology_row.get("dating_uncertainty_id")
        ),
        "uncertainty_label": clean_optional_text(uncertainty.get("label")),
        "uncertainty_description": clean_optional_text(uncertainty.get("description")),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _dendro_date_interval(
    dendro_date: dict[str, object],
    *,
    age_type: str,
) -> tuple[int, int] | None:
    return sead_dating_interval(
        {
            "low_value": dendro_date.get("age_younger"),
            "high_value": dendro_date.get("age_older"),
        },
        age_type=age_type,
    )


def _build_dendro_date_row(
    dendro_date: dict[str, object],
    *,
    age_type: str,
    interval: tuple[int, int] | None,
    uncertainty: Mapping[str, object],
    relation_identity: dict[str, int | None],
) -> dict[str, object]:
    return {
        **relation_identity,
        "dendro_date_id": parse_required_int(dendro_date.get("dendro_date_id")),
        "analysis_entity_id": parse_required_int(dendro_date.get("analysis_entity_id")),
        "age_type": age_type,
        "age_type_id": parse_optional_int(dendro_date.get("age_type_id")),
        "dating_uncertainty_id": parse_optional_int(
            dendro_date.get("dating_uncertainty_id")
        ),
        "age_older": parse_optional_int(dendro_date.get("age_older")),
        "age_younger": parse_optional_int(dendro_date.get("age_younger")),
        "age_range": clean_optional_text(dendro_date.get("age_range")),
        "dendro_lookup_id": parse_optional_int(dendro_date.get("dendro_lookup_id")),
        "season_id": parse_optional_int(dendro_date.get("season_id")),
        "uncertainty_label": clean_optional_text(uncertainty.get("label")),
        "uncertainty_description": clean_optional_text(uncertainty.get("description")),
        "time_start_bp": interval[0] if interval is not None else None,
        "time_end_bp": interval[1] if interval is not None else None,
    }


def _analysis_entity_relation_identity(
    analysis_entity_id: int,
    *,
    physical_sample_id_by_analysis_entity_id: dict[int, int],
    sample_group_id_by_physical_sample_id: dict[int, int],
    dataset_id_by_analysis_entity_id: dict[int, int | None],
) -> dict[str, int | None]:
    """Preserve the source-key chain that owns an entity chronology claim."""
    physical_sample_id = physical_sample_id_by_analysis_entity_id.get(
        analysis_entity_id
    )
    sample_group_id = (
        sample_group_id_by_physical_sample_id.get(physical_sample_id)
        if physical_sample_id is not None
        else None
    )
    return {
        "analysis_entity_id": analysis_entity_id or None,
        "physical_sample_id": physical_sample_id,
        "sample_group_id": sample_group_id,
        "dataset_id": dataset_id_by_analysis_entity_id.get(analysis_entity_id),
    }


def _build_bibliography_row(
    *,
    biblio_id: int,
    source_kind: str,
    source_record_id: int,
    source_record_label: str,
    biblio: Mapping[str, object],
) -> dict[str, object]:
    return {
        "biblio_id": biblio_id,
        "source_kind": source_kind,
        "source_record_id": source_record_id,
        "source_record_label": source_record_label,
        "title": str(biblio.get("title", "")).strip(),
        "full_reference": str(biblio.get("full_reference", "")).strip(),
        "year": str(biblio.get("year", "")).strip(),
        "doi": str(biblio.get("doi", "")).strip(),
        "url": str(biblio.get("url", "")).strip(),
    }


def _deduplicate_bibliography_rows(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    unique_rows: dict[tuple[int, str, int], dict[str, object]] = {}
    for row in rows:
        key = (
            parse_required_int(row.get("biblio_id")),
            clean_optional_text(row.get("source_kind")),
            parse_required_int(row.get("source_record_id")),
        )
        unique_rows.setdefault(key, row)
    return list(unique_rows.values())
