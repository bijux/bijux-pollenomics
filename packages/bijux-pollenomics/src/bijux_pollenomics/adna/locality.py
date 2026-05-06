from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
import re

from ..core.bp_time import (
    build_bp_interval_label,
    merge_bp_intervals,
    midpoint_bp_year,
)
from .models import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
    AdnaSampleRecord,
)
from .species import resolve_species_definition

__all__ = ["build_locality_identity", "summarize_sample_localities"]


def build_locality_identity(
    *,
    species_name: str,
    source_family: str,
    locality_text: str,
    political_entity: str,
    latitude_text: str,
    longitude_text: str,
) -> AdnaLocalityIdentity:
    """Build a canonical shared locality anchor for species-aware ancient-DNA records."""
    species = resolve_species_definition(species_name)
    locality_slug = _slugify(locality_text)
    political_slug = _slugify(political_entity)
    source_slug = _slugify(source_family)
    coordinate_slug = _slugify(f"{latitude_text}:{longitude_text}")
    stable_token = (
        f"{species.slug}:{source_slug}:{political_slug}:{locality_slug}:{coordinate_slug}"
    )
    return AdnaLocalityIdentity(
        namespace=f"{species.slug}:locality",
        stable_token=stable_token,
        locality_text=locality_text,
        political_entity=political_entity,
        source_anchor_tokens=(source_family, latitude_text, longitude_text),
    )


def summarize_sample_localities(
    samples: Iterable[AdnaSampleRecord],
) -> list[AdnaLocalitySummary]:
    """Aggregate species-aware samples into locality summaries."""
    grouped: dict[tuple[str | None, str, str], list[AdnaSampleRecord]] = defaultdict(list)
    for sample in samples:
        grouped[(sample.locality, sample.latitude_text, sample.longitude_text)].append(
            sample
        )

    summaries: list[AdnaLocalitySummary] = []
    for (locality, latitude_text, longitude_text), records in grouped.items():
        datasets = tuple(
            sorted({dataset for record in records for dataset in record.datasets})
        )
        sample_ids = tuple(
            record.genetic_id
            for record in sorted(records, key=lambda item: item.genetic_id)
        )
        time_interval = merge_bp_intervals(
            *[
                (record.time_start_bp, record.time_end_bp)
                for record in records
                if record.time_start_bp is not None and record.time_end_bp is not None
            ]
        )
        summaries.append(
            AdnaLocalitySummary(
                identity=records[0].locality_identity,
                species_latin_name=records[0].species_latin_name,
                species_common_name=records[0].species_common_name,
                source_family=records[0].source_family,
                source_releases=tuple(
                    sorted({record.source_release for record in records})
                ),
                record_modalities=tuple(
                    sorted({record.record_modality for record in records})
                ),
                review_strengths=tuple(
                    sorted({record.review_strength for record in records})
                ),
                provenance_qualities=tuple(
                    sorted({record.provenance_quality for record in records})
                ),
                locality=locality,
                coordinates=AdnaCoordinate(
                    latitude=records[0].latitude,
                    longitude=records[0].longitude,
                    latitude_text=latitude_text,
                    longitude_text=longitude_text,
                    confidence=records[0].coordinate_confidence,
                ),
                sample_count=len(records),
                sample_ids=sample_ids,
                datasets=datasets,
                chronology=AdnaChronology(
                    original_text=build_bp_interval_label(
                        time_interval[0], time_interval[1]
                    )
                    if time_interval is not None
                    else "",
                    time_start_bp=time_interval[0] if time_interval is not None else None,
                    time_end_bp=time_interval[1] if time_interval is not None else None,
                    time_mean_bp=_mean_bp_from_interval(time_interval),
                    dating_basis=records[0].dating_basis,
                ),
                sample_namespace=records[0].sample_namespace,
            )
        )

    summaries.sort(
        key=lambda item: (-item.sample_count, (item.locality or "").casefold())
    )
    return summaries


def _slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().casefold())
    return normalized.strip("-") or "unknown"


def _mean_bp_from_interval(interval: tuple[int, int] | None) -> int | None:
    if interval is None:
        return None
    return midpoint_bp_year(interval[0], interval[1])
