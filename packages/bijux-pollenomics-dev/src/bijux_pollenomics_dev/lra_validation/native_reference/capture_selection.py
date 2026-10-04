"""Select one independently admitted native capture without fallback."""

from __future__ import annotations
from pathlib import Path
from typing import Literal
from .annulus_capture import AnnulusCapture, validated_annulus_capture
from .count_domain_capture import CountDomainCapture, validated_count_domain_capture

CaptureProfile = Literal["annulus", "count-domain"]


def validated_current_capture(
    repository: Path, *, profile: CaptureProfile = "annulus"
) -> AnnulusCapture | CountDomainCapture:
    """Keep historical admission as the default and require explicit current selection."""
    if profile == "annulus":
        return validated_annulus_capture(repository)
    if profile == "count-domain":
        return validated_count_domain_capture(repository)
    raise ValueError("Native capture profile must be annulus or count-domain")
