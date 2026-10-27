"""Keep quantitative source accounting outside common native fit ancestry."""

from __future__ import annotations

from typing import Any

from .scalar import require

QUANTITATIVE = {
    "counts",
    "panel_counts",
    "panel_N",
    "pollen_N",
    "excluded_pollen_N",
    "reported_pollen_N",
    "projected_panel_N",
    "source_panel_N",
    "excluded_panel_N",
    "source_support_sha256",
    "native_sample_ids",
    "native_sample_count",
    "qualified_source_support",
    "original_projection",
    "source_window_authority",
    "source_population",
    "krag_audit",
}


def count_free_evidence(value: Any) -> None:
    if isinstance(value, dict):
        require(
            not set(value) & QUANTITATIVE,
            "quantitative source accounting in common fitting evidence",
        )
        for item in value.values():
            count_free_evidence(item)
    elif isinstance(value, list):
        for item in value:
            count_free_evidence(item)
    elif isinstance(value, str):
        require(
            "projection.json" not in value
            and "-raw.json" not in value
            and "krageholm-regional-source-support" not in value,
            "quantitative source reference in common fitting evidence",
        )


def metadata_admission(names: list[str]) -> list[str]:
    require(len(names) == len(set(names)), "duplicate materialized member admission")
    return sorted(
        name for name in names if not name.endswith(("-raw.json", "/projection.json"))
    )
