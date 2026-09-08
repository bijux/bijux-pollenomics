"""Deterministic selection of representative atlas-media poster frames."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from .contracts import AtlasMediaError


def poster_frame_ordinal(
    evidence_role: str, capture_frames: Sequence[Mapping[str, object]]
) -> int:
    """Return the earliest frame containing the maximum selected evidence."""
    if not capture_frames:
        raise AtlasMediaError("poster selection requires capture frames")
    field = (
        "visible_source_chronology_point_count"
        if evidence_role == "observation_chronology"
        else "visible_modeled_context_feature_count"
    )
    values = [frame.get(field) for frame in capture_frames]
    if any(
        isinstance(value, bool) or not isinstance(value, int) or value < 0
        for value in values
    ):
        raise AtlasMediaError("poster evidence counts are invalid")
    return max(range(len(values)), key=lambda ordinal: (values[ordinal], -ordinal))
