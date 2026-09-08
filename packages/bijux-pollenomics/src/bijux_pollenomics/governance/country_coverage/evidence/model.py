"""Coverage-cell lifecycle and source identity derivation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from ..constants import (
    _AUTHORITY_STATUS_VALUES,
    _STAGE_STATUS_VALUES,
    BOUNDARY_METHOD,
    PRODUCER_VERSION,
    PUBLICATION_METHOD,
    CountryCoverageError,
)
from ..decoding import (
    _required_text,
    _text_list,
)
from .partitions import _empty_counts


@dataclass(slots=True)
class _CellState:
    counts: dict[str, int | None]
    availability: str
    lifecycle: str
    reasons: list[str]


def _validate_stage_rows(rows: list[Mapping[str, object]]) -> None:
    for row in rows:
        source = _required_text(row, "source_key")
        for field in (
            "raw_status",
            "normalized_status",
            "reviewed_status",
            "published_status",
        ):
            if row.get(field) not in _STAGE_STATUS_VALUES:
                raise CountryCoverageError(
                    f"{source} source stage has unsupported {field}"
                )
        if row.get("authority_status") not in _AUTHORITY_STATUS_VALUES:
            raise CountryCoverageError(
                f"{source} source stage has unsupported authority_status"
            )
        _text_list(row.get("blocking_reasons"), f"{source} blocking reasons")
        _text_list(row.get("authority_reasons"), f"{source} authority reasons")


def _cell(
    *,
    source_family: str,
    dimension: str,
    country_code: str,
    evidence: Mapping[tuple[str, str, str], dict[str, int | None]],
    stage: Mapping[str, object],
    snapshot_id: str,
    boundary_digest: str,
    config_digest: str,
    build_id: str,
) -> dict[str, object]:
    counts = evidence.get((source_family, dimension, country_code))
    assignment_method = (
        None
        if dimension == "source_reported"
        else BOUNDARY_METHOD
        if dimension == "governed_assignment"
        else PUBLICATION_METHOD
    )
    authority = str(stage.get("authority_status"))
    blocking = _text_list(stage.get("blocking_reasons"), "blocking reasons")
    authority_reasons = _text_list(stage.get("authority_reasons"), "authority reasons")
    state = _initial_cell_state(counts, dimension)
    _apply_source_policy(
        state,
        source_family=source_family,
        dimension=dimension,
        country_code=country_code,
        blocking=blocking,
        authority_reasons=authority_reasons,
    )
    _apply_partition_policy(
        state,
        dimension=dimension,
        country_code=country_code,
    )
    if authority == "refused" and state.lifecycle not in {"refused", "unavailable"}:
        state.lifecycle = "refused"
        state.reasons.extend(authority_reasons)
    return {
        "schema_version": "2.0.0",
        "country_code": country_code,
        "country_dimension": dimension,
        "country_assignment_method": assignment_method,
        "source_family": source_family,
        "resolution": "source",
        "feature_key": None,
        "classification_contract_version": None,
        "availability_status": state.availability,
        "lifecycle_status": state.lifecycle,
        "counts": state.counts,
        "reason_codes": sorted(set(state.reasons)),
        "source_snapshot_id": snapshot_id,
        "boundary_artifact_digest": (
            None if dimension == "source_reported" else boundary_digest
        ),
        "config_digest": config_digest,
        "producer_version": PRODUCER_VERSION,
        "build_id": build_id,
    }


def _initial_cell_state(
    counts: dict[str, int | None] | None, dimension: str
) -> _CellState:
    if counts is None:
        return _CellState(
            counts=_empty_counts(),
            availability="blocked",
            lifecycle="unavailable",
            reasons=[f"{dimension}_partition_not_materialized"],
        )
    availability = (
        "zero_observations"
        if not any(value for value in counts.values() if value is not None)
        else "available_collected"
    )
    return _CellState(counts, availability, "admitted", [])


def _apply_source_policy(
    state: _CellState,
    *,
    source_family: str,
    dimension: str,
    country_code: str,
    blocking: list[str],
    authority_reasons: list[str],
) -> None:
    if source_family in {"raa", "svar"}:
        state.counts = _empty_counts()
        if country_code == "SE":
            state.availability = "blocked"
            state.lifecycle = "refused"
            state.reasons.extend(authority_reasons)
        else:
            state.availability = "not_available_from_source"
            state.lifecycle = "unavailable"
            state.reasons.append("national_source_sweden_only")
    elif source_family == "boundaries":
        state.lifecycle = "review_required"
        state.reasons.extend(authority_reasons)
    elif source_family == "sead" and dimension == "governed_assignment":
        if country_code == "UNASSIGNED":
            state.lifecycle = "review_required"
            state.availability = "unresolved"
            state.reasons.append("boundary_assignment_review_required")
        elif country_code == "OUTSIDE":
            state.lifecycle = "refused"
            state.availability = "available_partial"
            state.reasons.append("outside_governed_boundaries")
    elif source_family == "aadr":
        state.lifecycle = "review_required"
        state.reasons.extend(blocking)


def _apply_partition_policy(
    state: _CellState, *, dimension: str, country_code: str
) -> None:
    has_observations = any(
        value for value in state.counts.values() if value is not None
    )
    if country_code == "UNASSIGNED" and has_observations:
        if dimension == "source_reported":
            state.availability = "available_partial"
            state.reasons.append("source_country_not_reported")
        elif dimension == "governed_assignment":
            state.availability = "unresolved"
            state.lifecycle = "review_required"
            state.reasons.append("country_assignment_review_required")
    if country_code in {"UNASSIGNED", "OUTSIDE"} and not state.reasons:
        if has_observations:
            state.reasons.append("explicit_non_nordic_partition")
        else:
            state.reasons.append("explicit_empty_partition")
