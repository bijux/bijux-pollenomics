"""Temporal evidence extraction and interval comparison."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace

from bijux_pollenomics.collection.contracts.cardinality import (
    require_nonnegative_count,
    resolve_declared_count,
)
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.core import (
    build_temporal_semantics,
    haversine_km,
    resolve_temporal_window,
    temporal_semantics_has_numeric_interval,
)
from bijux_pollenomics.core.temporal_semantics import (
    BpInterval,
    InvalidBpIntervalError,
    canonical_bp_interval,
    closed_bp_intervals_overlap,
)

from .models import (
    _TEMPORAL_NAVIGATION_INTERVALS,
    LakeEvidenceCandidate,
    LakeEvidenceSourceAnchor,
    _PointEvidence,
)

__all__ = []


def _extract_human_points(localities: Iterable[object]) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in localities:
        latitude = getattr(locality, "latitude", None)
        longitude = getattr(locality, "longitude", None)
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = getattr(locality, "sample_count", 0)
        locality_token = str(getattr(locality, "locality_token", "")).strip()
        locality_name = str(getattr(locality, "locality", "") or "").strip()
        chronology = getattr(locality, "chronology", None)
        temporal_semantics: dict[str, object] | None = None
        if chronology is not None and hasattr(chronology, "as_temporal_semantics"):
            resolved_temporal_semantics = chronology.as_temporal_semantics(
                source_family="human_adna",
                comparison_note=(
                    "Nearby human aDNA provides dated regional context; it is not "
                    "chronology measured from the candidate lake."
                ),
            )
            if isinstance(resolved_temporal_semantics, dict):
                temporal_semantics = resolved_temporal_semantics
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=require_nonnegative_count(
                    sample_count,
                    field=f"human aDNA {locality_token or locality_name} sample_count",
                ),
                time_start_bp=_optional_int(getattr(locality, "time_start_bp", None)),
                time_end_bp=_optional_int(getattr(locality, "time_end_bp", None)),
                time_mean_bp=_optional_int(getattr(locality, "time_mean_bp", None)),
                source_record=f"human-adna:{locality_token or locality_name}",
                source_name=locality_name or locality_token or "Human aDNA locality",
                source_layer_key="human-adna",
                time_label=str(getattr(locality, "time_label", "")).strip(),
                temporal_semantics=temporal_semantics,
            )
        )
    return tuple(rows)


def _extract_animal_points(
    animal_localities: Iterable[dict[str, object]],
) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality in animal_localities:
        latitude = locality.get("latitude")
        longitude = locality.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        sample_count = resolve_declared_count(
            locality,
            "sample_count",
            field="animal aDNA locality sample_count",
            absent_default=0,
        )
        source_token = str(
            locality.get("site_record_id")
            or locality.get("feature_id")
            or locality.get("locality")
            or "unresolved-locality"
        ).strip()
        temporal_semantics = locality.get("temporal_semantics")
        rows.append(
            _PointEvidence(
                latitude=float(latitude),
                longitude=float(longitude),
                sample_count=sample_count,
                time_start_bp=_optional_int(locality.get("time_start_bp")),
                time_end_bp=_optional_int(locality.get("time_end_bp")),
                time_mean_bp=_optional_int(locality.get("time_mean_bp")),
                source_record=f"animal-adna:{source_token}",
                source_name=str(locality.get("locality") or source_token).strip(),
                source_layer_key="animal-adna",
                source_url=str(locality.get("source_url") or "").strip(),
                time_label=str(locality.get("time_label") or "").strip(),
                temporal_semantics=(
                    temporal_semantics if isinstance(temporal_semantics, dict) else None
                ),
            )
        )
    return tuple(rows)


def _attach_temporal_context(
    candidates: Sequence[LakeEvidenceCandidate],
    *,
    pollen_points: Sequence[ContextPointRecord],
    human_points: Sequence[_PointEvidence],
    animal_points: Sequence[_PointEvidence],
    sead_points: Sequence[ContextPointRecord],
) -> tuple[LakeEvidenceCandidate, ...]:
    evidence = (
        *(_context_point_evidence(point) for point in pollen_points),
        *human_points,
        *animal_points,
        *(_context_point_evidence(point) for point in sead_points),
    )
    numeric_evidence = tuple(
        point
        for point in evidence
        if _validated_interval(point.time_start_bp, point.time_end_bp) is not None
    )
    return tuple(
        replace(
            candidate,
            temporal_context_points=_summarize_candidate_temporal_context(
                candidate,
                numeric_evidence,
            ),
        )
        for candidate in candidates
    )


def _context_point_evidence(point: ContextPointRecord) -> _PointEvidence:
    return _PointEvidence(
        latitude=point.latitude,
        longitude=point.longitude,
        sample_count=point.record_count,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        time_mean_bp=point.time_mean_bp,
        source_record=f"{point.layer_key}:{point.record_id}",
        source_name=point.name,
        source_layer_key=point.layer_key,
        source_url=point.source_url,
        time_label=point.time_label,
        temporal_semantics=point.temporal_semantics,
    )


def _summarize_candidate_temporal_context(
    candidate: LakeEvidenceCandidate,
    evidence: Sequence[_PointEvidence],
) -> tuple[LakeEvidenceSourceAnchor, ...]:
    groups: dict[tuple[str, str], list[tuple[_PointEvidence, BpInterval]]] = {}
    for point in evidence:
        if (
            haversine_km(
                latitude_a=candidate.latitude,
                longitude_a=candidate.longitude,
                latitude_b=point.latitude,
                longitude_b=point.longitude,
            )
            > 50
        ):
            continue
        interval = _validated_interval(point.time_start_bp, point.time_end_bp)
        if interval is None:
            continue
        window_key, _ = resolve_temporal_window(
            time_start_bp=int(interval.younger_bp),
            time_end_bp=int(interval.older_bp),
            time_mean_bp=point.time_mean_bp,
        )
        if window_key == "unresolved":
            continue
        groups.setdefault((point.source_layer_key, window_key), []).append(
            (point, interval)
        )

    anchors: list[LakeEvidenceSourceAnchor] = []
    for (source_layer_key, window_key), grouped_evidence in sorted(groups.items()):
        points = [point for point, _ in grouped_evidence]
        intervals = [interval for _, interval in grouped_evidence]
        observed_end_bp = max(int(interval.older_bp) for interval in intervals)
        governed_interval = _TEMPORAL_NAVIGATION_INTERVALS.get(window_key)
        if governed_interval is None:
            time_start_bp = 6001
            time_end_bp = max(6001, observed_end_bp)
        else:
            time_start_bp, time_end_bp = governed_interval
        means = [
            point.time_mean_bp
            if point.time_mean_bp is not None
            else round((interval.younger_bp + interval.older_bp) / 2)
            for point, interval in zip(points, intervals, strict=True)
        ]
        time_mean_bp = min(
            time_end_bp,
            max(time_start_bp, round(sum(means) / len(means))),
        )
        _, window_label = resolve_temporal_window(
            time_start_bp=points[0].time_start_bp,
            time_end_bp=points[0].time_end_bp,
            time_mean_bp=points[0].time_mean_bp,
        )
        source_records = tuple(
            sorted({point.source_record for point in points if point.source_record})
        )
        source_urls = tuple(
            sorted({point.source_url for point in points if point.source_url})
        )
        comparison_note = (
            f"{len(points)} source record(s) within 50 km provide {window_label} "
            "context. The published interval is the governed navigation window, "
            "not a merged date range and not chronology measured from the lake."
        )
        semantics = build_temporal_semantics(
            source_family=source_layer_key,
            evidence_class="nearby_lake_context_summary",
            precision_posture="source_interval_window_summary",
            comparability_posture="numeric_interval_with_caveat",
            time_start_bp=time_start_bp,
            time_end_bp=time_end_bp,
            time_mean_bp=time_mean_bp,
            summary_label=window_label,
            comparison_note=comparison_note,
            original_labels=tuple(
                sorted({point.time_label for point in points if point.time_label})
            ),
            uncertainty_notes=(
                "Underlying source intervals may extend beyond this navigation window.",
                "The summary is nearby context and is not a lake-owned date.",
            ),
        ).as_dict()
        semantics["context_record_count"] = len(points)
        semantics["context_sample_count"] = sum(point.sample_count for point in points)
        semantics["context_radius_km"] = 50
        semantics["representative_source_records"] = list(source_records[:25])
        anchors.append(
            LakeEvidenceSourceAnchor(
                source_record=(
                    f"lake-context:{candidate.lake_registry_id or candidate.lake_token}:"
                    f"{source_layer_key}:{window_key}"
                ),
                source_name=f"{window_label} nearby {source_layer_key} context",
                source_layer_key=source_layer_key,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                source_url=source_urls[0] if source_urls else "",
                time_start_bp=time_start_bp,
                time_end_bp=time_end_bp,
                time_mean_bp=time_mean_bp,
                time_label=window_label,
                temporal_semantics=semantics,
                evidence_role="nearby_temporal_context",
                record_count=len(points),
                sample_count=sum(point.sample_count for point in points),
                context_radius_km=50,
                representative_source_records=source_records[:25],
            )
        )
    return tuple(anchors)


def _time_aware_ratio(points: Sequence[ContextPointRecord]) -> float:
    if not points:
        return 0.0
    time_aware = sum(
        1 for point in points if _context_point_has_numeric_interval(point)
    )
    return round(time_aware / len(points), 4)


def _context_point_has_numeric_interval(point: ContextPointRecord) -> bool:
    if point.temporal_semantics and not temporal_semantics_has_numeric_interval(
        point.temporal_semantics
    ):
        return False
    return _validated_interval(point.time_start_bp, point.time_end_bp) is not None


def _human_context_overlap_ratio(
    points: Sequence[ContextPointRecord],
    human_points: Sequence[_PointEvidence],
) -> float:
    if not points:
        return 0.0
    overlaps = sum(
        1 for point in points if _context_point_overlaps_any_human(point, human_points)
    )
    return round(overlaps / len(points), 4)


def _context_point_overlaps_any_human(
    point: ContextPointRecord,
    human_points: Sequence[_PointEvidence],
) -> bool:
    if not _context_point_has_numeric_interval(point):
        return False
    return any(
        _intervals_overlap(
            point.time_start_bp,
            point.time_end_bp,
            human_point.time_start_bp,
            human_point.time_end_bp,
        )
        for human_point in human_points
    )


def _intervals_overlap(
    start_a: int | None,
    end_a: int | None,
    start_b: int | None,
    end_b: int | None,
) -> bool:
    left = _validated_interval(start_a, end_a)
    right = _validated_interval(start_b, end_b)
    if left is None or right is None:
        return False
    return closed_bp_intervals_overlap(left, right)


def _validated_interval(
    younger_bp: int | None,
    older_bp: int | None,
) -> BpInterval | None:
    try:
        return canonical_bp_interval(younger_bp, older_bp)
    except InvalidBpIntervalError:
        return None


def _optional_int(value: object) -> int | None:
    if isinstance(value, int):
        return value
    return None
