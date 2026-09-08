"""Scoring and release-claim decisions for repository evidence."""

from __future__ import annotations

from typing import Any, cast

SCORE_MAX = 4

__all__: list[str] = []


def _build_claim_freeze_reasons(counts: dict[str, object]) -> list[str]:
    reasons = []
    if int(cast(Any, counts["papers_with_archived_supplements"])) < int(
        cast(Any, counts["tracked_paper_count"])
    ):
        reasons.append("supplement recovery is still far below paper coverage")
    sample_review_available = bool(counts["animal_sample_database_review_available"])
    map_readiness_available = bool(counts["animal_map_readiness_available"])
    if (
        sample_review_available
        and int(cast(Any, counts["published_atlas_point_count"])) <= 2
    ):
        reasons.append(
            "the shipped animal atlas point surface is still effectively empty"
        )
    if not sample_review_available:
        reasons.append("animal sample publication accounting is unavailable")
    if not map_readiness_available:
        reasons.append("animal coordinate-provenance accounting is unavailable")
    if (
        map_readiness_available
        and int(cast(Any, counts["animal_unresolved_sample_count"])) > 0
    ):
        reasons.append(
            "tracked animal samples still include unresolved locality assignments"
        )
    if map_readiness_available and (
        int(cast(Any, counts["animal_coordinate_refused_provenance_count"])) > 0
        or int(cast(Any, counts["animal_coordinate_not_materialized_count"])) > 0
    ):
        reasons.append(
            "animal coordinate provenance still includes refused or unpublished rows"
        )
    if counts["zero_collection_summary_surfaces"]:
        reasons.append(
            "collection summary still under-reports several non-aDNA source counts"
        )
    if not counts["raa_density_admitted"]:
        reasons.append(
            "RAÄ density remains refused until source inventory and qualified review reconcile"
        )
    return reasons


def _claim_check(
    check_id: str,
    passed: bool,
    description: str,
    findings: list[str],
) -> dict[str, object]:
    return {
        "check_id": check_id,
        "passed": passed,
        "description": description,
        "finding_count": len(findings),
        "findings": findings,
    }


def _ratio_score(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    ratio = numerator / denominator
    if ratio >= 0.9:
        return 4
    if ratio >= 0.6:
        return 3
    if ratio >= 0.3:
        return 2
    if ratio >= 0.1:
        return 1
    return 0
