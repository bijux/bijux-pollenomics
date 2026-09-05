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
    if int(cast(Any, counts["published_atlas_point_count"])) <= 2:
        reasons.append(
            "the shipped animal atlas point surface is still effectively empty"
        )
    if int(cast(Any, counts["animal_map_unresolved_rows"])) > int(
        cast(Any, counts["animal_map_supported_rows"])
    ):
        reasons.append("unresolved animal geography still overwhelms mapped support")
    if (
        int(cast(Any, counts["animal_map_unresolved_rows"])) > 0
        or int(cast(Any, counts["animal_map_refused_rows"])) > 0
    ):
        reasons.append(
            "tracked animal geography still leaves unresolved or refused rows outside the published surface"
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
