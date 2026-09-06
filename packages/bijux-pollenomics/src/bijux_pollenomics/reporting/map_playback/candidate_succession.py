"""Fail-closed candidate-succession playback posture."""

from __future__ import annotations

from collections.abc import Mapping

from .contracts import PlaybackContractError, PlaybackRefusal


def refuse_candidate_succession_storyboard(
    propagation_summary: Mapping[str, object],
) -> PlaybackRefusal:
    """Return no story unless a future governed candidate model is integrated."""
    status = propagation_summary.get("propagation_status")
    edge_count = propagation_summary.get("edge_count")
    reason = propagation_summary.get("reason_code")
    if status != "refused" or edge_count != 0:
        raise PlaybackContractError(
            "candidate-succession media is unsupported without a governed accepted model"
        )
    if not isinstance(reason, str) or not reason.strip():
        raise PlaybackContractError(
            "candidate-succession refusal requires a reason code"
        )
    return PlaybackRefusal(
        product_key="candidate_succession",
        reason_code=reason,
        detail=(
            "No candidate-succession story is published. Dated observations and "
            "modeled context do not establish movement, migration, or causation."
        ),
    )


__all__ = ["refuse_candidate_succession_storyboard"]
