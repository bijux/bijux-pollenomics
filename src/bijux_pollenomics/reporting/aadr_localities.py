from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import LocalitySummary, SampleRecord
from ..temporal import build_bp_interval_label, merge_bp_intervals, midpoint_bp_year


def summarize_localities(samples: Iterable[SampleRecord]) -> list[LocalitySummary]:
    """Aggregate samples into unique locality coordinates."""
    grouped: dict[tuple[str, str, str], list[SampleRecord]] = defaultdict(list)
    for sample in samples:
        grouped[(sample.locality, sample.latitude_text, sample.longitude_text)].append(sample)

    summaries: list[LocalitySummary] = []
    for (locality, latitude_text, longitude_text), records in grouped.items():
        datasets = tuple(sorted({dataset for record in records for dataset in record.datasets}))
        sample_ids = tuple(record.genetic_id for record in sorted(records, key=lambda item: item.genetic_id))
        time_interval = merge_bp_intervals(
            *[
                (record.time_start_bp, record.time_end_bp)
                for record in records
                if record.time_start_bp is not None and record.time_end_bp is not None
            ]
        )
        summaries.append(
            LocalitySummary(
                locality=locality,
                latitude=records[0].latitude,
                longitude=records[0].longitude,
                latitude_text=latitude_text,
                longitude_text=longitude_text,
                sample_count=len(records),
                sample_ids=sample_ids,
                datasets=datasets,
                time_start_bp=time_interval[0] if time_interval is not None else None,
                time_end_bp=time_interval[1] if time_interval is not None else None,
                time_mean_bp=mean_bp_from_interval(time_interval),
                time_label=build_bp_interval_label(time_interval[0], time_interval[1]) if time_interval is not None else "",
            )
        )

    summaries.sort(key=lambda item: (-item.sample_count, item.locality.casefold()))
    return summaries


def mean_bp_from_interval(interval: tuple[int, int] | None) -> int | None:
    """Return the midpoint of a merged BP interval."""
    if interval is None:
        return None
    return midpoint_bp_year(interval[0], interval[1])
