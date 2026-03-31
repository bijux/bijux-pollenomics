from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from .source_registry import ContextSourceSpec
from .staging import collect_into_staging_dir
from ..settings import NORDIC_BBOX


def collect_context_source(
    *,
    collect_function: Callable[..., object],
    spec: ContextSourceSpec,
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, int]:
    """Collect one context source and return the counts it contributes."""
    source_output_root = output_root / spec.output_dir_name
    report = collect_into_staging_dir(
        final_output_root=source_output_root,
        collect=lambda staging_root: collect_context_source_into_dir(
            spec=spec,
            collect_function=collect_function,
            source_output_root=staging_root,
            country_boundaries=country_boundaries,
        ),
    )
    return {
        summary_field: int(getattr(report, report_field))
        for summary_field, report_field in spec.count_attributes
    }


def collect_context_source_into_dir(
    *,
    spec: ContextSourceSpec,
    collect_function: Callable[..., object],
    source_output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> object:
    """Collect one context source into a prepared directory."""
    collect_kwargs = {
        "output_root": source_output_root,
        "country_boundaries": country_boundaries,
    }
    if spec.requires_bbox:
        collect_kwargs["bbox"] = NORDIC_BBOX
    return collect_function(**collect_kwargs)
