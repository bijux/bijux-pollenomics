from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Callable, Iterable

from .aadr import download_aadr_anno_files
from .boundaries import collect_boundaries_data, fetch_country_boundaries, load_country_boundaries
from .common import write_json, write_text
from .landclim import collect_landclim_data
from .models import DataCollectionSummary
from .neotoma import collect_neotoma_data
from .raa import collect_raa_data
from .sead import collect_sead_data
from ..settings import DEFAULT_AADR_VERSION, NORDIC_BBOX


AVAILABLE_SOURCES = ("aadr", "boundaries", "landclim", "neotoma", "raa", "sead")


@dataclass(frozen=True)
class ContextSourceSpec:
    name: str
    output_dir_name: str
    requires_bbox: bool
    count_attributes: tuple[tuple[str, str], ...]


CONTEXT_SOURCE_SPECS = {
    "landclim": ContextSourceSpec(
        name="landclim",
        output_dir_name="landclim",
        requires_bbox=True,
        count_attributes=(
            ("landclim_site_count", "site_count"),
            ("landclim_grid_cell_count", "grid_cell_count"),
        ),
    ),
    "neotoma": ContextSourceSpec(
        name="neotoma",
        output_dir_name="neotoma",
        requires_bbox=True,
        count_attributes=(("neotoma_point_count", "point_count"),),
    ),
    "raa": ContextSourceSpec(
        name="raa",
        output_dir_name="raa",
        requires_bbox=False,
        count_attributes=(
            ("raa_total_site_count", "total_site_count"),
            ("raa_heritage_site_count", "heritage_site_count"),
        ),
    ),
    "sead": ContextSourceSpec(
        name="sead",
        output_dir_name="sead",
        requires_bbox=True,
        count_attributes=(("sead_point_count", "point_count"),),
    ),
}


@dataclass(frozen=True)
class DataCollectionReport:
    generated_on: str
    output_root: Path
    version: str
    collected_sources: tuple[str, ...]
    source_output_roots: dict[str, str]
    aadr_file_count: int
    landclim_site_count: int
    landclim_grid_cell_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int
    boundary_source: str | None
    summary_path: Path


def collect_data(
    output_root: Path,
    sources: Iterable[str],
    version: str = DEFAULT_AADR_VERSION,
) -> DataCollectionReport:
    """Collect one or more tracked data sources into the project data tree."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    write_data_directory_readme(output_root, version=version)

    selected_sources = normalize_requested_sources(sources)
    source_output_roots = build_source_output_roots(output_root=output_root, version=version)

    counts = initialize_source_counts()
    boundary_source: str | None = None

    if "aadr" in selected_sources:
        aadr_report = collect_into_staging_dir(
            final_output_root=output_root / "aadr",
            collect=lambda staging_root: download_aadr_anno_files(output_root=staging_root, version=version),
        )
        counts["aadr_file_count"] = len(aadr_report.downloaded_files)

    need_boundaries = any(source in selected_sources for source in ("boundaries", *CONTEXT_SOURCE_SPECS))
    country_boundaries: dict[str, dict[str, object]] | None = None
    if need_boundaries:
        if "boundaries" in selected_sources:
            country_boundaries, _ = collect_into_staging_dir(
                final_output_root=output_root / "boundaries",
                collect=collect_boundaries_data,
            )
            boundary_source = "collected"
        else:
            country_boundaries = load_country_boundaries(output_root / "boundaries")
            if country_boundaries is not None:
                boundary_source = "local"
            else:
                country_boundaries = fetch_country_boundaries()
                boundary_source = "network"

    if country_boundaries is not None:
        for source_name in selected_sources:
            spec = CONTEXT_SOURCE_SPECS.get(source_name)
            if spec is None:
                continue
            counts.update(
                collect_context_source(
                    spec=spec,
                    output_root=output_root,
                    country_boundaries=country_boundaries,
                )
            )

    summary_path = output_root / "collection_summary.json"
    summary = DataCollectionSummary(
        generated_on=str(date.today()),
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        source_output_roots=source_output_roots,
        boundary_source=boundary_source,
        aadr_file_count=counts["aadr_file_count"],
        landclim_site_count=counts["landclim_site_count"],
        landclim_grid_cell_count=counts["landclim_grid_cell_count"],
        neotoma_point_count=counts["neotoma_point_count"],
        sead_point_count=counts["sead_point_count"],
        raa_total_site_count=counts["raa_total_site_count"],
        raa_heritage_site_count=counts["raa_heritage_site_count"],
        summary_path=summary_path,
    )
    write_collection_summary(summary)

    return DataCollectionReport(
        generated_on=summary.generated_on,
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        source_output_roots=source_output_roots,
        aadr_file_count=counts["aadr_file_count"],
        landclim_site_count=counts["landclim_site_count"],
        landclim_grid_cell_count=counts["landclim_grid_cell_count"],
        neotoma_point_count=counts["neotoma_point_count"],
        sead_point_count=counts["sead_point_count"],
        raa_total_site_count=counts["raa_total_site_count"],
        raa_heritage_site_count=counts["raa_heritage_site_count"],
        boundary_source=boundary_source,
        summary_path=summary_path,
    )


def initialize_source_counts() -> dict[str, int]:
    """Create a zeroed count mapping for every tracked source metric."""
    return {
        "aadr_file_count": 0,
        "landclim_site_count": 0,
        "landclim_grid_cell_count": 0,
        "neotoma_point_count": 0,
        "sead_point_count": 0,
        "raa_total_site_count": 0,
        "raa_heritage_site_count": 0,
    }


def collect_context_source(
    spec: ContextSourceSpec,
    output_root: Path,
    country_boundaries: dict[str, dict[str, object]],
) -> dict[str, int]:
    """Collect one context source and return the counts it contributes."""
    source_output_root = Path(output_root) / spec.output_dir_name
    collect_function = resolve_context_collect_function(spec.name)
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


def resolve_context_collect_function(name: str) -> Callable[..., object]:
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


def normalize_requested_sources(sources: Iterable[str]) -> tuple[str, ...]:
    """Normalize user-selected sources and expand `all`."""
    requested = tuple(source.strip().casefold() for source in sources if source.strip())
    if not requested:
        raise ValueError("At least one data source is required")
    if "all" in requested:
        return AVAILABLE_SOURCES

    unique_sources: list[str] = []
    for source in requested:
        if source not in AVAILABLE_SOURCES:
            raise ValueError(f"Unsupported data source: {source}")
        if source not in unique_sources:
            unique_sources.append(source)
    return tuple(unique_sources)


def render_data_root_readme() -> str:
    """Render a stable README for the generated data root."""
    return render_data_root_readme_for(Path("data"), DEFAULT_AADR_VERSION)


def render_data_root_readme_for(output_root: Path, version: str) -> str:
    """Render the data-root README with the active output directory name."""
    root_name = output_root.name or str(output_root)
    tree_lines = [
        root_name,
        "├── aadr",
        f"│   └── {version}",
        *(f"├── {source}" for source in AVAILABLE_SOURCES[1:-1]),
        f"└── {AVAILABLE_SOURCES[-1]}",
    ]
    tree_text = "\n".join(tree_lines)
    return f"""# Data Layout

Tracked source data lives directly under `{root_name}/`:

```text
{tree_text}
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- `docs/03-data-guide/index.md`
- `docs/07-reference/data-layout.md`

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts, source output roots, and provenance metadata.
"""


def build_source_output_roots(output_root: Path, version: str) -> dict[str, str]:
    """Build the machine-readable output-root mapping for every tracked source."""
    roots = {
        "aadr": str(Path(output_root) / "aadr"),
        "aadr_version_dir": str(Path(output_root) / "aadr" / version),
    }
    roots.update(
        {
            source: str(Path(output_root) / source)
            for source in AVAILABLE_SOURCES
            if source != "aadr"
        }
    )
    return roots


def write_data_directory_readme(output_root: Path, version: str) -> None:
    """Write the stable README that documents the generated data tree."""
    write_text(Path(output_root) / "README.md", render_data_root_readme_for(Path(output_root), version))


def reset_output_dir(path: Path) -> None:
    """Remove one generated source directory so recollection is deterministic."""
    if path.exists():
        shutil.rmtree(path)


def build_staging_output_dir(final_output_root: Path) -> Path:
    """Build the sibling staging directory used for safe source recollection."""
    final_output_root = Path(final_output_root)
    return final_output_root.parent / f".{final_output_root.name}.tmp"


def collect_into_staging_dir(
    final_output_root: Path,
    collect: Callable[[Path], object],
) -> object:
    """Collect into a staging directory and swap it into place only after success."""
    final_output_root = Path(final_output_root)
    staging_output_root = build_staging_output_dir(final_output_root)
    reset_output_dir(staging_output_root)
    staging_output_root.mkdir(parents=True, exist_ok=True)
    try:
        report = collect(staging_output_root)
        reset_output_dir(final_output_root)
        staging_output_root.replace(final_output_root)
        return report
    except Exception:
        reset_output_dir(staging_output_root)
        raise


def write_collection_summary(summary: DataCollectionSummary) -> None:
    """Write a machine-readable summary for the collected data tree."""
    payload = asdict(summary)
    payload["output_root"] = str(summary.output_root)
    payload["summary_path"] = str(summary.summary_path)
    write_json(summary.summary_path, payload)
