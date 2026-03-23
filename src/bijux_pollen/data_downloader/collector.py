from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .aadr import download_aadr_anno_files
from .boundaries import collect_boundaries_data, fetch_country_boundaries
from .common import write_text
from .neotoma import collect_neotoma_data
from .raa import collect_raa_data
from .sead import collect_sead_data


NORDIC_BBOX = (4.0, 54.0, 35.0, 72.0)
AVAILABLE_SOURCES = ("aadr", "boundaries", "neotoma", "raa", "sead")


@dataclass(frozen=True)
class DataCollectionReport:
    generated_on: str
    output_root: Path
    version: str
    collected_sources: tuple[str, ...]
    aadr_file_count: int
    neotoma_point_count: int
    sead_point_count: int
    raa_total_site_count: int
    raa_heritage_site_count: int


def collect_data(
    output_root: Path,
    sources: Iterable[str],
    version: str = "v62.0",
) -> DataCollectionReport:
    """Collect one or more tracked data sources into the project data tree."""
    output_root = Path(output_root)
    output_root.mkdir(parents=True, exist_ok=True)
    write_data_directory_readme(output_root)

    selected_sources = normalize_requested_sources(sources)

    aadr_file_count = 0
    neotoma_point_count = 0
    sead_point_count = 0
    raa_total_site_count = 0
    raa_heritage_site_count = 0

    if "aadr" in selected_sources:
        aadr_report = download_aadr_anno_files(output_root=output_root / "aadr", version=version)
        aadr_file_count = len(aadr_report.downloaded_files)

    need_boundaries = any(source in selected_sources for source in ("boundaries", "neotoma", "sead", "raa"))
    country_boundaries: dict[str, dict[str, object]] | None = None
    if need_boundaries:
        if "boundaries" in selected_sources:
            country_boundaries, _ = collect_boundaries_data(output_root / "boundaries")
        else:
            country_boundaries = fetch_country_boundaries()

    if "neotoma" in selected_sources and country_boundaries is not None:
        neotoma_report = collect_neotoma_data(
            output_root=output_root / "neotoma",
            country_boundaries=country_boundaries,
            bbox=NORDIC_BBOX,
        )
        neotoma_point_count = neotoma_report.point_count

    if "sead" in selected_sources and country_boundaries is not None:
        sead_report = collect_sead_data(
            output_root=output_root / "sead",
            country_boundaries=country_boundaries,
            bbox=NORDIC_BBOX,
        )
        sead_point_count = sead_report.point_count

    if "raa" in selected_sources and country_boundaries is not None:
        raa_report = collect_raa_data(
            output_root=output_root / "raa",
            country_boundaries=country_boundaries,
        )
        raa_total_site_count = raa_report.total_site_count
        raa_heritage_site_count = raa_report.heritage_site_count

    return DataCollectionReport(
        generated_on=str(date.today()),
        output_root=output_root,
        version=version,
        collected_sources=selected_sources,
        aadr_file_count=aadr_file_count,
        neotoma_point_count=neotoma_point_count,
        sead_point_count=sead_point_count,
        raa_total_site_count=raa_total_site_count,
        raa_heritage_site_count=raa_heritage_site_count,
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
├── neotoma
├── raa
└── sead
```

Detailed acquisition commands, source explanations, and storage rationale are documented in the canonical docs pages:

- `docs/03-data-guide/index.md`
- `docs/07-reference/data-layout.md`
"""


def write_data_directory_readme(output_root: Path) -> None:
    """Write the stable README that documents the generated data tree."""
    write_text(Path(output_root) / "README.md", render_data_root_readme())
