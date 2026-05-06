from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from ...adna import AdnaChronology, AdnaCoordinate, AdnaLocalitySummary, AdnaSampleRecord
from ...core.bp_time import (
    build_bp_interval_label,
    merge_bp_intervals,
    midpoint_bp_year,
)

__all__ = ["summarize_localities"]


def summarize_localities(
    samples: Iterable[AdnaSampleRecord],
) -> list[AdnaLocalitySummary]:
    """Aggregate samples into unique locality coordinates."""
    grouped: dict[tuple[str, str, str], list[AdnaSampleRecord]] = defaultdict(list)
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
                species_latin_name=records[0].species_latin_name,
                species_common_name=records[0].species_common_name,
                source_family=records[0].source_family,
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
                    time_mean_bp=mean_bp_from_interval(time_interval),
                    dating_basis=records[0].dating_basis,
                ),
                sample_namespace=records[0].sample_namespace,
            )
        )

    summaries.sort(key=lambda item: (-item.sample_count, item.locality.casefold()))
    return summaries


def mean_bp_from_interval(interval: tuple[int, int] | None) -> int | None:
    """Return the midpoint of a merged BP interval."""
    if interval is None:
        return None
    return midpoint_bp_year(interval[0], interval[1])
