"""Conservative chronology and domestication admission for pig source rows."""

from __future__ import annotations

import re

GOVERNED_DOMESTIC_ANCHORS = frozenset({"AA015", "AA016"})
_SOURCE_MEAN_RE = re.compile(r"(?:0|[1-9]\d*)(?:\.\d+)?")


def classify_domestication(
    sample_label: str, statuses: tuple[str, str, str]
) -> tuple[str, str, str]:
    """Retain source classification while admitting only governed anchors."""
    if sample_label in GOVERNED_DOMESTIC_ANCHORS and statuses != ("Domestic",) * 3:
        raise ValueError(
            f"Governed pig anchor {sample_label} domestication claims drift: {statuses!r}"
        )
    if statuses == ("Domestic",) * 3:
        if sample_label in GOVERNED_DOMESTIC_ANCHORS:
            return (
                "Domestic",
                "admitted_domesticated_core",
                "The existing governed anchor has three concordant Domestic claims.",
            )
        return (
            "Domestic",
            "excluded_unreviewed_domesticated_scope",
            "Three source fields report Domestic, but publication admission has not been widened.",
        )
    if statuses == ("Wild",) * 3:
        return (
            "Wild",
            "excluded_wild",
            "Three source classification fields concordantly report Wild.",
        )
    if statuses == ("Unknown",) * 3:
        return (
            "Unknown",
            "excluded_domestication_unknown",
            "Three source classification fields report Unknown domestication status.",
        )
    return (
        " || ".join(statuses),
        "excluded_noncanonical_domestication_status",
        "Source domestication fields are noncanonical or discordant and remain unreviewed.",
    )


def chronology_admission(
    *, sample_label: str, source_mean: str, source_mean_is_numeric: bool
) -> tuple[str, str, str]:
    """Keep source means raw unless an existing governed anchor admits one."""
    if sample_label in GOVERNED_DOMESTIC_ANCHORS:
        if not source_mean_is_numeric:
            raise ValueError(
                f"Governed pig anchor {sample_label} lacks its source mean"
            )
        return (
            f"{source_mean} BP",
            "admitted_existing_context_point",
            "The existing governed anchor retains its accepted context-only mean BP point.",
        )
    if source_mean_is_numeric:
        return (
            "",
            "refused_context_only_unresolved_age_semantics",
            "The source mean is preserved, but its age system is not admitted as comparable chronology.",
        )
    return (
        "",
        "unresolved_missing_source_mean",
        "The source row does not report a numeric Age (Mean years BP) value.",
    )


def source_mean_is_numeric(value: str) -> bool:
    """Recognize a source numeric token without converting or truncating it."""
    return _SOURCE_MEAN_RE.fullmatch(value.strip()) is not None
