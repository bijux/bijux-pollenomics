from __future__ import annotations

from collections.abc import Iterable

from ...adna import AdnaLocalitySummary, AdnaSampleRecord, summarize_sample_localities

__all__ = ["summarize_localities"]


def summarize_localities(
    samples: Iterable[AdnaSampleRecord],
) -> list[AdnaLocalitySummary]:
    """Compatibility wrapper for species-aware locality summarization."""
    return summarize_sample_localities(samples)
