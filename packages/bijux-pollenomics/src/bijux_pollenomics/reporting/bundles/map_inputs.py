from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..models import SampleRecord


@dataclass(frozen=True)
class MultiCountryMapInputs:
    """Prepared sample inputs for atlas bundle generation."""

    countries: tuple[str, ...]
    country_samples: dict[str, tuple[SampleRecord, ...]]
    country_sample_counts: dict[str, int]
    all_samples: tuple[SampleRecord, ...]


def load_multi_country_map_inputs(
    *,
    version_dir: Path,
    countries: tuple[str, ...],
    load_country_samples_fn: Callable[..., tuple[list[SampleRecord], dict[str, int]]],
) -> MultiCountryMapInputs:
    """Load and aggregate all country sample sets needed for one atlas bundle."""
    country_samples: dict[str, tuple[SampleRecord, ...]] = {}
    country_sample_counts: dict[str, int] = {}
    for country in countries:
        samples, _ = load_country_samples_fn(version_dir=version_dir, country=country)
        country_samples[country] = tuple(samples)
        country_sample_counts[country] = len(samples)

    all_samples = tuple(
        sample for country in countries for sample in country_samples[country]
    )
    return MultiCountryMapInputs(
        countries=countries,
        country_samples=country_samples,
        country_sample_counts=country_sample_counts,
        all_samples=all_samples,
    )


__all__ = ["MultiCountryMapInputs", "load_multi_country_map_inputs"]
