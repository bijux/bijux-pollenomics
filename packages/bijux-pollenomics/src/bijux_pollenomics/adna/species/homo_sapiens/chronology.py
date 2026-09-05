"""Duplicate-row reconciliation and canonical BP chronology merging."""

from __future__ import annotations

from bijux_pollenomics.adna.domain.models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaSampleIdentity,
    AdnaSampleRecord,
)
from bijux_pollenomics.core.bp_time import build_bp_interval_label, midpoint_bp_year

from .text import clean_text


def merge_duplicate_samples(
    existing: AdnaSampleRecord, sample: AdnaSampleRecord
) -> AdnaSampleRecord:
    """Merge duplicate Homo sapiens AADR rows across datasets."""
    merged_datasets = tuple(sorted(set(existing.datasets) | set(sample.datasets)))
    merged_interval = merge_sample_time_interval(existing, sample)
    return AdnaSampleRecord(
        identity=AdnaSampleIdentity(
            namespace=existing.sample_namespace,
            stable_token=existing.genetic_id,
            accession_lineage=tuple(
                dict.fromkeys(existing.accession_lineage + sample.accession_lineage)
            ),
        ),
        locality_identity=existing.locality_identity,
        species_latin_name=existing.species_latin_name,
        species_common_name=existing.species_common_name,
        source_family=existing.source_family,
        source_release=existing.source_release,
        record_modality=existing.record_modality,
        review_strength=existing.review_strength,
        provenance_quality=existing.provenance_quality,
        master_id=pick_value(existing.master_id, sample.master_id),
        group_id=pick_value(existing.group_id, sample.group_id),
        locality=existing.locality or sample.locality,
        political_entity=existing.political_entity or sample.political_entity,
        coordinates=AdnaCoordinate(
            latitude=existing.latitude,
            longitude=existing.longitude,
            latitude_text=pick_value(existing.latitude_text, sample.latitude_text),
            longitude_text=pick_value(existing.longitude_text, sample.longitude_text),
            confidence=pick_value(
                existing.coordinate_confidence, sample.coordinate_confidence
            )
            or "unknown",
        ),
        publication=pick_value(existing.publication, sample.publication),
        year_first_published=pick_value(
            existing.year_first_published, sample.year_first_published
        ),
        full_date=pick_value(existing.full_date, sample.full_date),
        chronology=AdnaChronology(
            original_text=pick_time_label(existing, sample, merged_interval),
            time_start_bp=merged_interval[0] if merged_interval is not None else None,
            time_end_bp=merged_interval[1] if merged_interval is not None else None,
            time_mean_bp=mean_bp_from_samples(existing, sample, merged_interval),
            date_stddev_bp=pick_value(existing.date_stddev_bp, sample.date_stddev_bp),
            dating_basis=pick_value(existing.dating_basis, sample.dating_basis)
            or "unknown",
        ),
        data_type=pick_value(existing.data_type, sample.data_type),
        molecular_sex=pick_value(existing.molecular_sex, sample.molecular_sex),
        datasets=merged_datasets,
    )


def merge_sample_time_interval(
    left: AdnaSampleRecord, right: AdnaSampleRecord
) -> tuple[int, int] | None:
    """Merge two sample intervals into one canonical younger/older BP span."""
    intervals = [
        interval
        for interval in (
            (left.time_start_bp, left.time_end_bp)
            if left.time_start_bp is not None and left.time_end_bp is not None
            else None,
            (right.time_start_bp, right.time_end_bp)
            if right.time_start_bp is not None and right.time_end_bp is not None
            else None,
        )
        if interval is not None
    ]
    if not intervals:
        return None
    return (min(start for start, _ in intervals), max(end for _, end in intervals))


def pick_value(left: str, right: str) -> str:
    """Prefer the first populated release value."""
    return left or right


def mean_bp_from_samples(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> int | None:
    """Preserve source means, deriving a midpoint only for a populated span."""
    for value in (left.time_mean_bp, right.time_mean_bp):
        if value is not None:
            return value
    if merged_interval is None:
        return None
    return midpoint_bp_year(merged_interval[0], merged_interval[1])


def pick_time_label(
    left: AdnaSampleRecord,
    right: AdnaSampleRecord,
    merged_interval: tuple[int, int] | None,
) -> str:
    """Preserve the strongest source label before deriving a BP interval label."""
    for value in (left.time_label, right.time_label, left.full_date, right.full_date):
        if clean_text(value):
            return clean_text(value)
    if merged_interval is None:
        return ""
    return build_bp_interval_label(merged_interval[0], merged_interval[1])


_pick_value = pick_value
_mean_bp_from_samples = mean_bp_from_samples
_pick_time_label = pick_time_label
