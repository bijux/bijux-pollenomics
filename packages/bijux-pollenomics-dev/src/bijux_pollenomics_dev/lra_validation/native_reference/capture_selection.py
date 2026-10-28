"""Select one independently admitted native capture without fallback."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from .annulus_capture import AnnulusCapture, validated_annulus_capture
from .count_domain_capture import CountDomainCapture, validated_count_domain_capture

from .finite_covariance_capture import (
    FiniteCovarianceCapture,
    validated_finite_covariance_capture,
)

CaptureProfile = Literal["annulus", "count-domain", "finite-covariance"]


def validated_current_capture(
    repository: Path, *, profile: CaptureProfile = "annulus"
) -> AnnulusCapture | CountDomainCapture | FiniteCovarianceCapture:
    """Keep historical admission as the default and require explicit current selection."""
    if profile == "annulus":
        return validated_annulus_capture(repository)
    if profile == "count-domain":
        return validated_count_domain_capture(repository)
    if profile == "finite-covariance":
        return validated_finite_covariance_capture(repository)
    raise ValueError(
        "Native capture profile must be annulus, count-domain or finite-covariance"
    )
