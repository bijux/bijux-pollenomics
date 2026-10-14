"""Temporal evidence extraction and interval comparison."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import replace

from bijux_pollenomics.adna.domain.locality import (
    locality_sample_intervals,
    mapping_sample_intervals,
)
from bijux_pollenomics.adna.domain.models import AdnaLocalitySummary
from bijux_pollenomics.collection.contracts.cardinality import require_nonnegative_count
from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.contracts.occurrence_chronology import (
    occurrence_support_intervals,
)
from bijux_pollenomics.core import (
    build_temporal_semantics,
    haversine_km,
    resolve_temporal_window,
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
        if not isinstance(locality, AdnaLocalitySummary):
            continue
        require_nonnegative_count(locality.sample_count, field="sample_count")
        support_index = {
            support.sample_id: support for support in locality.sample_chronologies
        }
        admitted_samples = locality_sample_intervals(locality)
        for sample_id, interval in admitted_samples:
            support = support_index.get(sample_id)
            chronology = (
                support.chronology if support is not None else locality.chronology
            )
            rows.append(
                _PointEvidence(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    sample_count=1,
                    time_start_bp=int(interval.younger_bp),
                    time_end_bp=int(interval.older_bp),
                    time_mean_bp=chronology.time_mean_bp,
                    source_record=f"human-adna:{locality.locality_token}:sample:{sample_id}",
                    source_locality_key=(
                        locality.locality_namespace,
                        locality.locality_token,
                    ),
                    source_name=locality.locality or locality.locality_token,
                    source_layer_key="human-adna",
                    time_label=chronology.original_text,
                    temporal_semantics=chronology.as_temporal_semantics(
                        source_family="human_adna"
                    ),
                )
            )
        remainder = locality.sample_count - len(admitted_samples)
        if remainder > 0 or not admitted_samples:
            rows.append(
                _PointEvidence(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    sample_count=max(0, remainder),
                    source_record=f"human-adna:{locality.locality_token}",
                    source_locality_key=(
                        locality.locality_namespace,
                        locality.locality_token,
                    ),
                    source_name=locality.locality or locality.locality_token,
                    source_layer_key="human-adna",
                )
            )
    return tuple(rows)


def _extract_animal_points(
    animal_localities: Iterable[dict[str, object]],
) -> tuple[_PointEvidence, ...]:
    rows: list[_PointEvidence] = []
    for locality_index, locality in enumerate(animal_localities):
        latitude = locality.get("latitude")
        longitude = locality.get("longitude")
        if not isinstance(latitude, (int, float)) or not isinstance(
            longitude, (int, float)
        ):
            continue
        if "sample_count" in locality:
            require_nonnegative_count(locality["sample_count"], field="sample_count")
        source_token = str(
            locality.get("site_record_id")
            or locality.get("feature_id")
            or locality.get("locality")
            or "unresolved-locality"
        ).strip()
        admitted_samples = mapping_sample_intervals(locality)
        native_identity = locality.get("locality_identity", locality.get("identity"))
        source_locality_key = ("animal-row", str(locality_index))
        if isinstance(native_identity, dict) and all(
            isinstance(native_identity.get(key), str)
            and str(native_identity[key]).strip()
            for key in ("namespace", "stable_token")
        ):
            source_locality_key = (
                str(native_identity["namespace"]),
                str(native_identity["stable_token"]),
            )
        for support, interval in admitted_samples:
            chronology = support.chronology
            rows.append(
                _PointEvidence(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    sample_count=1,
                    time_start_bp=int(interval.younger_bp),
                    time_end_bp=int(interval.older_bp),
                    time_mean_bp=chronology.time_mean_bp,
                    source_record=f"animal-adna:{source_token}:sample:{support.sample_id}",
                    source_locality_key=source_locality_key,
                    source_name=str(locality.get("locality") or source_token),
                    source_layer_key="animal-adna",
                    source_url=str(locality.get("source_url") or ""),
                    time_label=chronology.original_text,
                    temporal_semantics=chronology.as_temporal_semantics(
                        source_family="animal_adna",
                        provenance_path=support.provenance_path,
                        provenance_locator=support.provenance_locator,
                        provenance_excerpt=support.provenance_excerpt,
                    ),
                )
            )
        sample_count = require_nonnegative_count(
            locality.get("sample_count", len(admitted_samples)), field="sample_count"
        )
        remainder = sample_count - len(admitted_samples)
        if remainder > 0 or not admitted_samples:
            rows.append(
                _PointEvidence(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    sample_count=max(0, remainder),
                    source_record=f"animal-adna:{source_token}",
                    source_locality_key=source_locality_key,
                    source_name=str(locality.get("locality") or source_token),
                    source_layer_key="animal-adna",
                    source_url=str(locality.get("source_url") or ""),
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
        if occurrence_support_intervals(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
            occurrence_supports=point.occurrence_supports,
        )
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
        occurrence_supports=point.occurrence_supports,
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
        for interval in occurrence_support_intervals(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
            occurrence_supports=point.occurrence_supports,
        ):
            window_key, _ = resolve_temporal_window(
                time_start_bp=int(interval.younger_bp),
                time_end_bp=int(interval.older_bp),
                time_mean_bp=None
                if point.occurrence_supports is not None
                else point.time_mean_bp,
            )
            if window_key != "unresolved":
                groups.setdefault((point.source_layer_key, window_key), []).append(
                    (point, interval)
                )

    anchors: list[LakeEvidenceSourceAnchor] = []
    for (source_layer_key, window_key), grouped_evidence in sorted(groups.items()):
        points = list({id(point): point for point, _ in grouped_evidence}.values())
        intervals = [interval for _, interval in grouped_evidence]
        observed_end_bp = max(int(interval.older_bp) for interval in intervals)
        governed_interval = _TEMPORAL_NAVIGATION_INTERVALS.get(window_key)
        if governed_interval is None:
            time_start_bp = 6001
            time_end_bp = max(6001, observed_end_bp)
        else:
            time_start_bp, time_end_bp = governed_interval
        means = []
        for point in points:
            member_intervals = [
                interval for member, interval in grouped_evidence if member is point
            ]
            means.append(
                point.time_mean_bp
                if point.occurrence_supports is None and point.time_mean_bp is not None
                else round(
                    sum(
                        (interval.younger_bp + interval.older_bp) / 2
                        for interval in member_intervals
                    )
                    / len(member_intervals)
                )
            )
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
    return bool(
        occurrence_support_intervals(
            temporal_semantics=point.temporal_semantics,
            time_start_bp=point.time_start_bp,
            time_end_bp=point.time_end_bp,
            occurrence_supports=point.occurrence_supports,
        )
    )


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
    intervals = occurrence_support_intervals(
        temporal_semantics=point.temporal_semantics,
        time_start_bp=point.time_start_bp,
        time_end_bp=point.time_end_bp,
        occurrence_supports=point.occurrence_supports,
    )
    return any(
        closed_bp_intervals_overlap(interval, human_interval)
        for interval in intervals
        for human_point in human_points
        for human_interval in occurrence_support_intervals(
            temporal_semantics=human_point.temporal_semantics,
            time_start_bp=human_point.time_start_bp,
            time_end_bp=human_point.time_end_bp,
            occurrence_supports=human_point.occurrence_supports,
        )
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
