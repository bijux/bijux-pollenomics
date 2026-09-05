"""Rows describing recovery scoring and governance-artifact decisions."""

from __future__ import annotations

__all__: list[str] = []


def _recovery_review_row(
    key: str,
    display_name: str,
    *,
    data_completeness: int,
    provenance_clarity: int,
    documentation_clarity: int,
    output_honesty: int,
    metrics: dict[str, object],
    note: str,
) -> dict[str, object]:
    return {
        "surface_key": key,
        "display_name": display_name,
        "data_completeness": data_completeness,
        "provenance_clarity": provenance_clarity,
        "documentation_clarity": documentation_clarity,
        "output_honesty": output_honesty,
        "metrics": metrics,
        "note": note,
    }


def _artifact_review_row(
    artifact_path: str,
    action: str,
    surface_kind: str,
    reason: str,
) -> dict[str, object]:
    return {
        "artifact_path": artifact_path,
        "action": action,
        "surface_kind": surface_kind,
        "reason": reason,
    }
