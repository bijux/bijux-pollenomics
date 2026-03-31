from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DataDefaults:
    aadr_version: str
    nordic_bbox: tuple[float, float, float, float]


@dataclass(frozen=True)
class AtlasDefaults:
    slug: str
    title: str
    published_countries: tuple[str, ...]


@dataclass(frozen=True)
class ProjectPaths:
    data_root: Path
    aadr_root: Path
    report_root: Path
    context_root: Path


DATA_DEFAULTS = DataDefaults(
    aadr_version="v62.0",
    nordic_bbox=(4.0, 54.0, 35.0, 72.0),
)

ATLAS_DEFAULTS = AtlasDefaults(
    slug="nordic-atlas",
    title="Nordic Evidence Atlas",
    published_countries=("Sweden", "Norway", "Finland", "Denmark"),
)

PROJECT_PATHS = ProjectPaths(
    data_root=Path("data"),
    aadr_root=Path("data/aadr"),
    report_root=Path("docs/report"),
    context_root=Path("data"),
)
