"""Homo sapiens AADR metadata runtime facade."""

from __future__ import annotations

from collections import Counter
from contextvars import ContextVar
from functools import lru_cache
from hashlib import sha256
from pathlib import Path

from bijux_pollenomics.adna.domain.models import AdnaSampleRecord
from bijux_pollenomics.adna.workflow.runtime import (
    AdnaSampleQuery,
    AdnaSourceBundle,
    AdnaSpeciesRuntimeManifest,
)
from bijux_pollenomics.adna.workflow.runtime import (
    sample_matches_query as sample_matches_query,
)

from .chronology import (
    _mean_bp_from_samples as _mean_bp_from_samples,
)
from .chronology import (
    _pick_time_label as _pick_time_label,
)
from .chronology import (
    _pick_value as _pick_value,
)
from .chronology import (
    merge_duplicate_samples as merge_duplicate_samples,
)
from .chronology import (
    merge_sample_time_interval as merge_sample_time_interval,
)
from .constants import (
    HOMO_SAPIENS_PROVENANCE_QUALITY as HOMO_SAPIENS_PROVENANCE_QUALITY,
)
from .constants import (
    HOMO_SAPIENS_RECORD_MODALITY as HOMO_SAPIENS_RECORD_MODALITY,
)
from .constants import (
    HOMO_SAPIENS_REVIEW_STRENGTH as HOMO_SAPIENS_REVIEW_STRENGTH,
)
from .loading import (
    EMPTY_COUNTRY_RECORDS,
    is_country_only_query,
    sample_sort_key,
)
from .loading import (
    CountryRecords as _CountryRecords,
)
from .loading import (
    load_homo_sapiens_samples as _load_homo_sapiens_samples,
)
from .loading import (
    single_human_bundle as _single_human_bundle,
)
from .manifest import (
    build_homo_sapiens_runtime_manifest,
    build_homo_sapiens_runtime_manifest_for_version_dir,
)
from .records import (
    _dating_basis as _dating_basis,
)
from .records import (
    iter_homo_sapiens_samples_from_anno,
    iter_homo_sapiens_samples_from_bytes,
)
from .release import (
    ReleaseCacheKey,
    capture_release_inputs,
    discover_homo_sapiens_anno_files,
    release_cache_key,
    release_dataset_names,
    validate_release_manifest_identity,
)
from .text import clean_text as _clean_text

_CAPTURED_RELEASE: ContextVar[tuple[tuple[str, bytes], ...] | None] = ContextVar(
    "aadr_captured_release", default=None
)

_EMPTY_COUNTRY_RECORDS = EMPTY_COUNTRY_RECORDS
_is_country_only_query = is_country_only_query
_release_dataset_names = release_dataset_names
_validate_release_manifest_identity = validate_release_manifest_identity

__all__ = [
    "build_homo_sapiens_runtime_manifest",
    "build_homo_sapiens_runtime_manifest_for_version_dir",
    "discover_homo_sapiens_anno_files",
    "iter_homo_sapiens_samples_from_anno",
    "load_homo_sapiens_country_samples",
    "load_homo_sapiens_samples",
]


def load_homo_sapiens_country_samples(
    manifest: AdnaSpeciesRuntimeManifest, country: str
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Compatibility helper for country-scoped Homo sapiens sample loading."""
    return load_homo_sapiens_samples(
        manifest=manifest,
        query=AdnaSampleQuery(political_entity=country),
    )


def load_homo_sapiens_samples(
    *,
    manifest: AdnaSpeciesRuntimeManifest,
    query: AdnaSampleQuery | None = None,
) -> tuple[list[AdnaSampleRecord], Counter[str]]:
    """Load normalized Homo sapiens AADR samples via the runtime manifest."""
    if manifest.species.latin_name != "Homo sapiens":
        raise ValueError(
            "Homo sapiens AADR loader cannot be used for species "
            f"{manifest.species.latin_name}"
        )
    bundle = _single_human_bundle(manifest)
    normalized_query = query.normalized() if query is not None else AdnaSampleQuery()
    captured = capture_release_inputs(bundle)
    cache_key = release_cache_key(bundle, captured)
    token = _CAPTURED_RELEASE.set(captured)
    try:
        return _load_homo_sapiens_samples(
            manifest=manifest,
            query=normalized_query,
            cache_key=cache_key,
            release_loader=_cached_release_samples,
            country_loader=_cached_country_records,
            sample_matcher=sample_matches_query,
        )
    finally:
        _CAPTURED_RELEASE.reset(token)


@lru_cache(maxsize=32)
def _cached_release_samples(
    cache_key: ReleaseCacheKey,
) -> tuple[AdnaSampleRecord, ...]:
    (
        source_release,
        source_family,
        record_modality,
        review_strength,
        provenance_quality,
        file_rows,
    ) = cache_key
    records: list[AdnaSampleRecord] = []
    captured = _CAPTURED_RELEASE.get()
    if captured is None:
        raise ValueError("AADR cache miss requires captured annotation bytes")
    if tuple((path, sha256(raw).hexdigest()) for path, raw in captured) != file_rows:
        raise ValueError("AADR captured annotations do not match cache identity")
    for file_path, raw in captured:
        anno_path = Path(file_path)
        records.extend(
            iter_homo_sapiens_samples_from_bytes(
                raw,
                dataset_name=anno_path.parent.name,
                source_release=source_release,
                source_family=source_family,
                record_modality=record_modality,
                review_strength=review_strength,
                provenance_quality=provenance_quality,
            )
        )
    return tuple(records)


@lru_cache(maxsize=32)
def _cached_country_records(
    cache_key: ReleaseCacheKey,
) -> dict[str, _CountryRecords]:
    grouped_samples: dict[str, dict[str, AdnaSampleRecord]] = {}
    grouped_dataset_counts: dict[str, Counter[str]] = {}
    for sample in _cached_release_samples(cache_key):
        political_entity = _clean_text(sample.political_entity)
        if not political_entity:
            continue
        country_key = political_entity.casefold()
        grouped_dataset_counts.setdefault(country_key, Counter())
        grouped_samples.setdefault(country_key, {})
        for dataset_name in sample.datasets:
            grouped_dataset_counts[country_key][dataset_name] += 1
        existing = grouped_samples[country_key].get(sample.genetic_id)
        grouped_samples[country_key][sample.genetic_id] = (
            sample if existing is None else merge_duplicate_samples(existing, sample)
        )
    return {
        country_key: _CountryRecords(
            samples=tuple(sorted(rows.values(), key=sample_sort_key)),
            dataset_counts=tuple(sorted(grouped_dataset_counts[country_key].items())),
        )
        for country_key, rows in grouped_samples.items()
    }


def _release_cache_key(bundle: AdnaSourceBundle) -> ReleaseCacheKey:
    return release_cache_key(bundle)
