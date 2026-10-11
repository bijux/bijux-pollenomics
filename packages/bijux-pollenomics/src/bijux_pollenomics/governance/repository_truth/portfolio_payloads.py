"""Typed field views for repository-truth portfolio counts and rendered rows."""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict


class TruthPostureText(TypedDict):
    primary_domains: list[str]
    contextual_domains: list[str]
    overall_recovery_posture: str
    claim_freeze_reasons: list[str]
    recovery_priorities: list[str]
    do_not_repeat: list[str]


class ClaimCheckText(TypedDict):
    check_id: str
    passed: bool
    finding_count: int


class DocsRecoveryRowText(TypedDict):
    dimension_key: str
    score: int
    finding: str


class DocsRecoveryText(TypedDict):
    rows: list[DocsRecoveryRowText]
    evidence_anchors: list[str]


def object_mapping(value: object, label: str) -> Mapping[str, object]:
    """Expose JSON object fields only after checking the mapping and key domain."""
    if not isinstance(value, Mapping) or any(not isinstance(key, str) for key in value):
        raise TypeError(f"Repository portfolio {label} must be a string-keyed mapping")
    return {key: item for key, item in value.items() if isinstance(key, str)}


def nonnegative_count(counts: Mapping[str, object], field: str) -> int:
    """Keep unavailable counts distinct from certified nonnegative integers."""
    value = counts.get(field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"Repository truth {field} must be a nonnegative integer")
    return value


def _text(value: object, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"Repository portfolio {label} must be a string")
    return value


def _strings(value: object, label: str) -> list[str]:
    if not isinstance(value, list):
        raise TypeError(f"Repository portfolio {label} must be a string list")
    return [_text(item, label) for item in value]


def _rows(value: object, label: str) -> list[Mapping[str, object]]:
    if not isinstance(value, list):
        raise TypeError(f"Repository portfolio {label} must be an object list")
    return [object_mapping(item, label) for item in value]


def truth_posture_text(payload: Mapping[str, object]) -> TruthPostureText:
    """Certify the text fields consumed by the truth-posture renderer."""
    overview = object_mapping(payload["recovery_review_overview"], "recovery overview")
    return {
        "primary_domains": _strings(payload["primary_domains"], "primary domains"),
        "contextual_domains": _strings(
            payload["contextual_domains"], "contextual domains"
        ),
        "overall_recovery_posture": _text(
            overview["overall_recovery_posture"], "recovery posture"
        ),
        "claim_freeze_reasons": _strings(
            payload["claim_freeze_reasons"], "claim freeze reasons"
        ),
        "recovery_priorities": _strings(
            payload["recovery_priorities"], "recovery priorities"
        ),
        "do_not_repeat": _strings(payload["do_not_repeat"], "do not repeat"),
    }


def claim_check_text(payload: Mapping[str, object]) -> list[ClaimCheckText]:
    """Certify claim identifiers, decisions and finding counts before rendering."""
    checks: list[ClaimCheckText] = []
    for row in _rows(payload["checks"], "claim checks"):
        passed = row["passed"]
        if not isinstance(passed, bool):
            raise TypeError("Repository portfolio claim decision must be a boolean")
        checks.append(
            {
                "check_id": _text(row["check_id"], "claim identifier"),
                "passed": passed,
                "finding_count": nonnegative_count(row, "finding_count"),
            }
        )
    return checks


def docs_recovery_text(payload: Mapping[str, object]) -> DocsRecoveryText:
    """Certify the rendered recovery dimensions and their evidence anchors."""
    return {
        "rows": [
            {
                "dimension_key": _text(row["dimension_key"], "recovery dimension"),
                "score": nonnegative_count(row, "score"),
                "finding": _text(row["finding"], "recovery finding"),
            }
            for row in _rows(payload["rows"], "recovery rows")
        ],
        "evidence_anchors": _strings(payload["evidence_anchors"], "evidence anchors"),
    }
