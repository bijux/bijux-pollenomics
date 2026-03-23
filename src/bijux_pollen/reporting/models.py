from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SampleRecord:
    genetic_id: str
    master_id: str
    group_id: str
    locality: str
    political_entity: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    publication: str
    year_first_published: str
    full_date: str
    date_mean_bp: str
    data_type: str
    molecular_sex: str
    datasets: tuple[str, ...]


@dataclass(frozen=True)
class LocalitySummary:
    locality: str
    latitude: float
    longitude: float
    latitude_text: str
    longitude_text: str
    sample_count: int
    sample_ids: tuple[str, ...]
    datasets: tuple[str, ...]


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


class SchemaError(ValueError):
    """Raised when an AADR anno file does not contain expected columns."""
