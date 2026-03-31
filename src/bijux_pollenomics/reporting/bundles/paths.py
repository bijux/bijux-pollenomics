from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..utils import slugify

__all__ = [
    "AtlasBundlePaths",
    "CountryBundlePaths",
    "build_atlas_bundle_paths",
    "build_country_bundle_paths",
]


@dataclass(frozen=True)
class CountryBundlePaths:
    output_dir: Path
    slug: str
    version: str
    readme_path: Path
    samples_csv_path: Path
    localities_csv_path: Path
    samples_geojson_path: Path
    samples_markdown_path: Path
    summary_json_path: Path


@dataclass(frozen=True)
class AtlasBundlePaths:
    output_dir: Path
    slug: str
    version: str
    readme_path: Path
    map_html_path: Path
    samples_geojson_path: Path
    summary_json_path: Path


def build_country_bundle_paths(output_dir: Path, country: str, version: str) -> CountryBundlePaths:
    """Build the stable artifact paths for one country bundle."""
    output_dir = Path(output_dir)
    country_slug = slugify(country)
    return CountryBundlePaths(
        output_dir=output_dir,
        slug=country_slug,
        version=version,
        readme_path=output_dir / "README.md",
        samples_csv_path=output_dir / f"{country_slug}_aadr_{version}_samples.csv",
        localities_csv_path=output_dir / f"{country_slug}_aadr_{version}_localities.csv",
        samples_geojson_path=output_dir / f"{country_slug}_aadr_{version}_samples.geojson",
        samples_markdown_path=output_dir / f"{country_slug}_aadr_{version}_samples.md",
        summary_json_path=output_dir / f"{country_slug}_aadr_{version}_summary.json",
    )


def build_atlas_bundle_paths(output_dir: Path, slug: str, version: str) -> AtlasBundlePaths:
    """Build the stable artifact paths for one atlas bundle."""
    output_dir = Path(output_dir)
    atlas_slug = slugify(slug)
    return AtlasBundlePaths(
        output_dir=output_dir,
        slug=atlas_slug,
        version=version,
        readme_path=output_dir / "README.md",
        map_html_path=output_dir / f"{atlas_slug}_map.html",
        samples_geojson_path=output_dir / f"{atlas_slug}_samples.geojson",
        summary_json_path=output_dir / f"{atlas_slug}_summary.json",
    )
