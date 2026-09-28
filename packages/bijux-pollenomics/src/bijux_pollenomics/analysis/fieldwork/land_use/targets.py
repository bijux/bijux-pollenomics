from __future__ import annotations

from collections.abc import Callable, Iterable
import json
from pathlib import Path
from typing import Any

from .models import _Target as Target


def named_registry_details(context_root: Path) -> dict[str, dict[str, object]]:
    """Bind named lake decisions to exact current SVAR review identities."""
    review_path = (
        context_root / "svar" / "review" / "lake_candidate_registry_review.json"
    )
    features_path = (
        context_root / "svar" / "review" / "sweden_lake_candidate_registry.geojson"
    )
    if not review_path.exists() and not features_path.exists():
        return {}
    if not review_path.is_file() or not features_path.is_file():
        raise ValueError("Named SVAR review is incomplete")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    features = json.loads(features_path.read_text(encoding="utf-8"))
    by_id: dict[str, dict[str, object]] = {}
    for feature in features["features"]:
        properties = feature["properties"]
        record_id = properties["record_id"]
        if record_id in by_id:
            raise ValueError("Named SVAR registry ID is duplicated")
        by_id[record_id] = properties
    result: dict[str, dict[str, object]] = {}
    for row in review["named_targets"]:
        if row["registry_status"] != "matched":
            continue
        source = by_id.get(row["registry_match"])
        if source is None or source["source"] != "SMHI SVAR":
            raise ValueError("Named SVAR match has no source feature")
        name = row["requested_name"]
        if name in result:
            raise ValueError("Named SVAR target is duplicated")
        result[name] = {
            "registry_id": source["record_id"],
            "registry_name": source["name"],
            "lake_area_km2": source["area_km2"],
            "source_url": source["source_url"],
        }
    return result


def synthesis_targets(
    lake_report: Any,
    *,
    governed_named_targets: tuple[Target, ...],
    target_type: type[Target],
) -> tuple[Target, ...]:
    named_lake_targets = {
        target.registry_name: target
        for target in governed_named_targets
        if target.target_class == "registered_lake" and target.registry_name
    }
    ranked_targets = list(named_lake_targets.values())
    for assessment in lake_report.assessments:
        candidate = assessment.candidate
        if candidate.lake_name in named_lake_targets:
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
