from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from .models import _Target as Target


def synthesis_targets(
    lake_report: Any,
    *,
    governed_named_targets: tuple[Target, ...],
    target_type: type[Target],
) -> tuple[Target, ...]:
    named_lake_targets = {
        target.registry_name: target
        for target in governed_named_targets
        if target.registry_name
    }
    ranked_targets = []
    for assessment in lake_report.assessments:
        candidate = assessment.candidate
        governed_target = named_lake_targets.get(candidate.lake_name)
        if governed_target is not None:
            ranked_targets.append(governed_target)
            continue
        ranked_targets.append(
            target_type(
                requested_name=candidate.lake_name,
                registry_name=candidate.lake_name,
                latitude=candidate.latitude,
                longitude=candidate.longitude,
                target_class="registered_lake",
                lake_decision="include_lake_review",
                decision_reason=(
                    "Ranked SVAR lake retained in the time-aware synthesis so the "
                    "published ranking and temporal comparison have the same scope."
                ),
                coordinate_source="official SVAR lake representative point",
            )
        )
    context_targets = [
        target
        for target in governed_named_targets
        if target.target_class == "archaeological_wetland_context"
    ]
    return (*ranked_targets, *context_targets)


def target_row(
    target: Target,
    *,
    lake_candidates: Iterable[Any],
    landclim_features: list[dict[str, object]],
    distance_km: Callable[..., float],
    context_report_url: str,
) -> dict[str, object]:
    matching_assessments = tuple(
        assessment
        for assessment in lake_candidates
        if assessment.candidate.lake_name == target.registry_name
    )
    assessment = min(
        matching_assessments,
        key=lambda item: distance_km(
            latitude_a=target.latitude,
            longitude_a=target.longitude,
            latitude_b=item.candidate.latitude,
            longitude_b=item.candidate.longitude,
        ),
        default=None,
    )
    candidate = assessment.candidate if assessment is not None else None
    return {
        "requested_name": target.requested_name,
        "registry_name": target.registry_name,
        "target_class": target.target_class,
        "lake_decision": target.lake_decision,
        "decision_reason": target.decision_reason,
        "latitude": target.latitude,
        "longitude": target.longitude,
        "coordinate_source": target.coordinate_source,
        "registry_id": candidate.lake_registry_id if candidate is not None else "",
        "lake_area_km2": candidate.lake_area_km2 if candidate is not None else None,
        "lake_rank": assessment.aggregate_rank if assessment is not None else None,
        "sampling_readiness_posture": (
            candidate.lake_sampling_readiness_posture
            if candidate is not None
            else "not_applicable"
        ),
        "source_url": (
            candidate.representative_source_url
            if candidate is not None
            else context_report_url
        ),
        "landclim_coverage_posture": (
            "covered_by_governed_grid" if landclim_features else "outside_governed_grid"
        ),
        "landclim_window_count": len(landclim_features),
    }
