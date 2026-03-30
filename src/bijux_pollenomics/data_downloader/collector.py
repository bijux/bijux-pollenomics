from __future__ import annotations

import shutil
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

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
class DataCollectionReport:
    generated_on: str
    output_root: Path
    version: str
    collected_sources: tuple[str, ...]
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
    write_data_directory_readme(output_root)

    selected_sources = normalize_requested_sources(sources)

    aadr_file_count = 0
    landclim_site_count = 0
    landclim_grid_cell_count = 0
    neotoma_point_count = 0
    sead_point_count = 0
    raa_total_site_count = 0
    raa_heritage_site_count = 0
    boundary_source: str | None = None

    if "aadr" in selected_sources:
        reset_output_dir(output_root / "aadr")
        aadr_report = download_aadr_anno_files(output_root=output_root / "aadr", version=version)
        aadr_file_count = len(aadr_report.downloaded_files)

    need_boundaries = any(source in selected_sources for source in ("boundaries", "landclim", "neotoma", "sead", "raa"))
    country_boundaries: dict[str, dict[str, object]] | None = None
    if need_boundaries:
        if "boundaries" in selected_sources:
            reset_output_dir(output_root / "boundaries")
            country_boundaries, _ = collect_boundaries_data(output_root / "boundaries")
            boundary_source = "collected"
        else:
            country_boundaries = load_country_boundaries(output_root / "boundaries")
            if country_boundaries is not None:
                boundary_source = "local"
            else:
                country_boundaries = fetch_country_boundaries()
                boundary_source = "network"

    if "landclim" in selected_sources and country_boundaries is not None:
        reset_output_dir(output_root / "landclim")
        landclim_report = collect_landclim_data(
            output_root=output_root / "landclim",
            country_boundaries=country_boundaries,
            bbox=NORDIC_BBOX,
        )
        landclim_site_count = landclim_report.site_count
        landclim_grid_cell_count = landclim_report.grid_cell_count

    if "neotoma" in selected_sources and country_boundaries is not None:
        reset_output_dir(output_root / "neotoma")
        neotoma_report = collect_neotoma_data(
            output_root=output_root / "neotoma",
            country_boundaries=country_boundaries,
            bbox=NORDIC_BBOX,
        )
        neotoma_point_count = neotoma_report.point_count

    if "sead" in selected_sources and country_boundaries is not None:
        reset_output_dir(output_root / "sead")
        sead_report = collect_sead_data(
            output_root=output_root / "sead",
            country_boundaries=country_boundaries,
            bbox=NORDIC_BBOX,
        )
        sead_point_count = sead_report.point_count

    if "raa" in selected_sources and country_boundaries is not None:
        reset_output_dir(output_root / "raa")
        raa_report = collect_raa_data(
            output_root=output_root / "raa",
            country_boundaries=country_boundaries,
        )
        raa_total_site_count = raa_report.total_site_count
        raa_heritage_site_count = raa_report.heritage_site_count

    summary_path = output_root / "collection_summary.json"
    summary = DataCollectionSummary(
        generated_on=str(date.today()),
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        boundary_source=boundary_source,
        aadr_file_count=aadr_file_count,
        landclim_site_count=landclim_site_count,
        landclim_grid_cell_count=landclim_grid_cell_count,
        neotoma_point_count=neotoma_point_count,
        sead_point_count=sead_point_count,
        raa_total_site_count=raa_total_site_count,
        raa_heritage_site_count=raa_heritage_site_count,
        summary_path=summary_path,
    )
    write_collection_summary(summary)

    return DataCollectionReport(
        generated_on=summary.generated_on,
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        aadr_file_count=aadr_file_count,
        landclim_site_count=landclim_site_count,
        landclim_grid_cell_count=landclim_grid_cell_count,
        neotoma_point_count=neotoma_point_count,
        sead_point_count=sead_point_count,
        raa_total_site_count=raa_total_site_count,
        raa_heritage_site_count=raa_heritage_site_count,
        boundary_source=boundary_source,
        summary_path=summary_path,
    )


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
    return """# Data Layout

Tracked source data lives directly under `data/`:

```text
data
├── aadr
│   └── v62.0
├── boundaries
├── landclim
├── neotoma
├── raa
└── sead
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- `docs/03-data-guide/index.md`
- `docs/07-reference/data-layout.md`

The collector also writes `collection_summary.json` so the current data tree can be inspected with machine-readable counts and provenance metadata.
"""


def render_data_root_readme_for(output_root: Path) -> str:
    """Render the data-root README with the active output directory name."""
    root_name = output_root.name or str(output_root)
    return render_data_root_readme().replace("under `data/`", f"under `{root_name}/`").replace(
        "\ndata\n",
        f"\n{root_name}\n",
        1,
    )


def write_data_directory_readme(output_root: Path) -> None:
    """Write the stable README that documents the generated data tree."""
    write_text(Path(output_root) / "README.md", render_data_root_readme_for(Path(output_root)))


def reset_output_dir(path: Path) -> None:
    """Remove one generated source directory so recollection is deterministic."""
    if path.exists():
        shutil.rmtree(path)


def write_collection_summary(summary: DataCollectionSummary) -> None:
    """Write a machine-readable summary for the collected data tree."""
    payload = asdict(summary)
    payload["output_root"] = str(summary.output_root)
    payload["summary_path"] = str(summary.summary_path)
    write_json(summary.summary_path, payload)
