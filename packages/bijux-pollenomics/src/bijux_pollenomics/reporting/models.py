from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ..adna import AdnaLocalitySummary, AdnaSampleRecord

SampleRecord = AdnaSampleRecord
LocalitySummary = AdnaLocalitySummary


@dataclass(frozen=True)
class CountryReport:
    country: str
    version: str
    generated_on: str
    total_unique_samples: int
    total_unique_localities: int
    dataset_row_counts: dict[str, int]
    samples: tuple[SampleRecord, ...]
    localities: tuple[LocalitySummary, ...]
    output_dir: Path


@dataclass(frozen=True)
class MultiCountryMapReport:
    title: str
    slug: str
    version: str
    generated_on: str
    countries: tuple[str, ...]
    country_sample_counts: dict[str, int]
    total_unique_samples: int
    output_dir: Path


@dataclass(frozen=True)
class PublishedReportsReport:
    version: str
    generated_on: str
    countries: tuple[str, ...]
    shared_map_dir: Path
    country_output_dirs: tuple[Path, ...]
    summary_path: Path


class SchemaError(ValueError):
    """Raised when an AADR anno file does not contain expected columns."""
