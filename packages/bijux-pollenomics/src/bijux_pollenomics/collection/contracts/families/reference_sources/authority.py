"""Authority posture for candidate-only reference-source evidence."""

from __future__ import annotations

from pathlib import Path

from ..models import _SourceAuthorityState
from .metrics import reference_source_metrics


def reference_source_authority_state(
    output_root: Path, source_key: str
) -> _SourceAuthorityState:
    """Require qualified admission after structural evidence review."""
    metrics = reference_source_metrics(output_root, source_key)
    if source_key == "empd2":
        invalid_reason = "missing_or_invalid_empd2_reference_review_evidence"
        review_reason = "qualified_empd2_source_review_missing"
    elif source_key == "nfi":
        invalid_reason = "missing_or_invalid_nfi_reference_review_evidence"
        review_reason = "qualified_nfi_source_review_missing"
    else:
        raise ValueError(f"unsupported reference source: {source_key}")
    has_review_evidence = any(value is not None for value in metrics.values())
    return _SourceAuthorityState(
        status="review_required",
        reason_codes=(review_reason,) if has_review_evidence else (invalid_reason,),
        governed_metrics=metrics,
    )
