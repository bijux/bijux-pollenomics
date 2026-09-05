"""Query application and release-bundle boundaries for Homo sapiens records."""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.workflow.runtime import (
    AdnaSampleQuery,
    AdnaSourceBundle,
    AdnaSpeciesRuntimeManifest,
)

from .chronology import merge_duplicate_samples
from .release import ReleaseCacheKey


@dataclass(frozen=True)
class CountryRecords:
    """Immutable cached samples and dataset counts for one country."""

    samples: tuple[AdnaSampleRecord, ...]
    dataset_counts: tuple[tuple[str, int], ...]


EMPTY_COUNTRY_RECORDS = CountryRecords(samples=(), dataset_counts=())

ReleaseLoader = Callable[[ReleaseCacheKey], tuple[AdnaSampleRecord, ...]]
CountryLoader = Callable[[ReleaseCacheKey], dict[str, CountryRecords]]
SampleMatcher = Callable[[AdnaSampleRecord, AdnaSampleQuery], bool]


def load_homo_sapiens_samples(
    *,
    manifest: AdnaSpeciesRuntimeManifest,
    query: AdnaSampleQuery | None,
    cache_key: ReleaseCacheKey,
    release_loader: ReleaseLoader,
    country_loader: CountryLoader,
    sample_matcher: SampleMatcher,
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Load and filter normalized AADR records using injected stable caches."""
    if manifest.species.latin_name != "Homo sapiens":
        raise ValueError(
            "Homo sapiens AADR loader cannot be used for species "
            f"{manifest.species.latin_name}"
        )
    normalized_query = query.normalized() if query is not None else AdnaSampleQuery()
    if is_country_only_query(normalized_query):
        political_entity = normalized_query.political_entity
        if political_entity is None:
            raise ValueError("Country-only AADR queries require a political entity")
        cached_records = country_loader(cache_key).get(
            political_entity.casefold(), EMPTY_COUNTRY_RECORDS
        )
        return list(cached_records.samples), Counter(
            dict(cached_records.dataset_counts)
        )

    combined: dict[str, AdnaSampleRecord] = {}
    dataset_counts: Counter[str] = Counter()
    for sample in release_loader(cache_key):
        if not sample_matcher(sample, normalized_query):
            continue
        for dataset_name in sample.datasets:
            dataset_counts[dataset_name] += 1
        existing = combined.get(sample.genetic_id)
        combined[sample.genetic_id] = (
            sample if existing is None else merge_duplicate_samples(existing, sample)
        )
    samples = sorted(combined.values(), key=sample_sort_key)
    return samples, dataset_counts


def single_human_bundle(manifest: AdnaSpeciesRuntimeManifest) -> AdnaSourceBundle:
    """Require exactly one AADR source bundle for the human runtime."""
    if len(manifest.source_bundles) != 1:
        raise ValueError(
            "Homo sapiens runtime manifest must expose exactly one source bundle"
        )
    return manifest.source_bundles[0]


def is_country_only_query(query: AdnaSampleQuery) -> bool:
    """Identify the cacheable country-only query surface."""
    return bool(query.political_entity) and not any(
        (
            query.locality_token,
            query.dataset_names,
            query.modalities,
            query.provenance_qualities,
            query.review_strengths,
            query.time_start_bp is not None,
            query.time_end_bp is not None,
        )
    )


def sample_sort_key(sample: AdnaSampleRecord) -> tuple[str, str, str]:
    """Return the stable public ordering key for normalized samples."""
    return (
        (sample.locality or "").casefold(),
        sample.master_id.casefold(),
        sample.genetic_id.casefold(),
    )
