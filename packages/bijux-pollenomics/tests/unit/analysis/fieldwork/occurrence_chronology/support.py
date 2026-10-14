"""Source-declared coverage stays spatial context across analytical consumers."""

from __future__ import annotations

from dataclasses import replace

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.landclim.sites import (
    landclim_site_temporal_semantics,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization.site_temporal_semantics import (
    build_sead_temporal_semantics,
)
from bijux_pollenomics.core.temporal_semantics import (
    build_temporal_semantics,
)

from ..ranking_examples import _point


def _semantics(evidence_class: str, precision: str) -> dict[str, object]:
    return build_temporal_semantics(
        source_family="controlled_source",
        evidence_class=evidence_class,
        precision_posture=precision,
        comparability_posture="numeric_interval_with_caveat",
        time_start_bp=2500,
        time_end_bp=3500,
        time_mean_bp=3000,
    ).as_dict()


def _coverage() -> tuple[dict[str, object], ...]:
    return (
        landclim_site_temporal_semantics(
            dataset_id="897303",
            interval=(2500, 3500),
            summary_label="2500-3500 BP",
            provenance_locator="SiteData:controlled",
        ),
        build_sead_temporal_semantics({}, time_interval=(2500, 3500)),
        build_sead_temporal_semantics(
            {"dating_range_rows": [{"uncertainty_label": "controlled qualifier"}]},
            time_interval=(2500, 3500),
        ),
        build_sead_temporal_semantics(
            {
                "relative_period_rows": [
                    {"relative_age_label": "controlled source period"}
                ]
            },
            time_interval=(2500, 3500),
        ),
        _semantics("nearby_lake_context_summary", "source_interval_window_summary"),
    )


def _context(
    semantics: dict[str, object] | None, *, layer: str = "controlled"
) -> ContextPointRecord:
    return replace(
        _point(layer, 59, 18, time_start_bp=2500, time_end_bp=3500),
        layer_key=layer,
        temporal_semantics=semantics,
    )
