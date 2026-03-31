from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .sources.aadr import download_aadr_anno_files
from .boundaries import collect_boundaries_data, fetch_country_boundaries, load_country_boundaries
from .pipeline.collection_reports import (
    build_data_collection_report,
    build_data_collection_summary,
    initialize_source_counts,
)
from .pipeline.context_collection import collect_context_source
from .data_layout import AVAILABLE_SOURCES, build_source_output_roots, write_data_directory_readme
from .landclim import collect_landclim_data
from .models import DataCollectionReport
from .neotoma import collect_neotoma_data
from .pipeline.requested_sources import normalize_requested_sources
from .pipeline.source_registry import CONTEXT_SOURCE_SPECS
from .pipeline.staging import build_staging_output_dir, collect_into_staging_dir
from .pipeline.summary_writer import write_collection_summary
from .sources.boundaries import resolve_country_boundaries
from .raa import collect_raa_data
from .sead import collect_sead_data
from ..config import DEFAULT_AADR_VERSION

__all__ = [
    "AVAILABLE_SOURCES",
    "DataCollectionReport",
    "build_staging_output_dir",
    "collect_data",
    "normalize_requested_sources",
]


def collect_data(
    output_root: Path,
    sources: Iterable[str],
    version: str = DEFAULT_AADR_VERSION,
) -> DataCollectionReport:
    """Collect one or more tracked data sources into the project data tree."""
    selected_sources = normalize_requested_sources(sources)
    output_root = Path(output_root)
    source_output_roots = build_source_output_roots(output_root=output_root, version=version)

    counts = initialize_source_counts()
    boundary_source: str | None = None

    if "aadr" in selected_sources:
        aadr_report = collect_into_staging_dir(
            final_output_root=output_root / "aadr",
            collect=lambda staging_root: download_aadr_anno_files(output_root=staging_root, version=version),
        )
        counts["aadr_file_count"] = len(aadr_report.downloaded_files)

    country_boundaries, boundary_source = resolve_country_boundaries(
        output_root=output_root,
        selected_sources=selected_sources,
        collect_boundaries_data=collect_boundaries_data,
        collect_into_staging_dir=collect_into_staging_dir,
        fetch_country_boundaries=fetch_country_boundaries,
        load_country_boundaries=load_country_boundaries,
    )

    if country_boundaries is not None:
        for source_name in selected_sources:
            spec = CONTEXT_SOURCE_SPECS.get(source_name)
            if spec is None:
                continue
            counts.update(
                collect_context_source(
                    collect_function=resolve_context_collect_function(source_name),
                    spec=spec,
                    output_root=output_root,
                    country_boundaries=country_boundaries,
                    )
            )

    summary = build_data_collection_summary(
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        source_output_roots=source_output_roots,
        boundary_source=boundary_source,
        counts=counts,
    )
    output_root.mkdir(parents=True, exist_ok=True)
    write_data_directory_readme(output_root, version=version)
    write_collection_summary(summary)

    return build_data_collection_report(summary)


def resolve_context_collect_function(name: str):
    """Resolve a context-source collector function by tracked source name."""
    functions = {
        "landclim": collect_landclim_data,
        "neotoma": collect_neotoma_data,
        "raa": collect_raa_data,
        "sead": collect_sead_data,
    }
    try:
        return functions[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported context source: {name}") from exc
