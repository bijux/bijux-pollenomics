"""Packet-level payload assembly and methodology ownership."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from bijux_pollenomics.analysis.fieldwork.evidence_richness import (
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
)


def build_payload(
    report: LakeEvidenceRichnessReport,
    *,
    top_n: int,
    select_rows: Callable[..., list[LakeEvidenceRichnessAssessment]],
    build_row: Callable[..., dict[str, object]],
) -> dict[str, Any]:
    ordered_assessments = select_rows(report, top_n=top_n)
    rows = [
        build_row(assessment, fieldwork_rank=index)
        for index, assessment in enumerate(ordered_assessments, start=1)
    ]
    return {
        "schema_version": "sweden-lake-fieldwork-preparation.v2",
        "country": report.country,
        "row_count": len(rows),
        "methodology": {
            "scope": "fieldwork-priority Sweden lake candidates only",
            "identity_rule": (
                "identity resolution remains required when duplicate names, "
                "non-official registry names, source coordinate spread, or "
                "source name variants remain visible"
            ),
            "sampling_rule": (
                "sampling fit stays separate from evidence density so very small "
                "basins remain review-first and engineered or wetland-style names "
                "never read as ordinary lake targets"
            ),
            "human_context_rule": (
                "near-lake human aDNA remains decisive for fieldwork ordering: "
                "10 km support is strongest, 20 km support remains shortlist-grade, "
                "and lakes with human support only beyond 20 km stay review-first "
                "even when their broader context is rich"
            ),
            "scenario_consistency_rule": (
                "scenario consistency is high when a lake appears in at least four "
                "top-20 scenario lists across aggregate and 10-50 km bands, medium "
                "at two to three lists, else low"
            ),
            "fieldwork_ordering_rule": (
                "fieldwork ordering sorts first by near-lake human aDNA posture, "
                "then by sampling posture, then by a human-weighted shortlist score; "
                "aggregate evidence score remains visible for traceability"
            ),
            "sead_context_rule": "SEAD 20 km context fit is high at >=20 sites, medium at >=5 sites, else low",
            "palaeopen_alignment_rule": (
                "PalaeOpen alignment fit is high when the lake already carries "
                ">=2 direct pollen sources and >=4 evidence families within 20 km"
            ),
            "warning": (
                "This is a fieldwork-preparation surface, not a final sampling "
                "recommendation."
            ),
        },
        "rows": rows,
    }
