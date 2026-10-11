"""Immutable identities for retained joint-product presentation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

JointProductStatus = Literal["complete", "incomplete"]


@dataclass(frozen=True)
class JointLRAPresentation:
    """A local report receipt, not publication or scientific approval."""

    directory: Path
    manifest_sha256: str
    product_manifest_sha256: str
    scientific_content_sha256: str
    plan_sha256: str
    product_status: JointProductStatus
    interrupted: bool
    bin_count: int
    requested_draw_bins: int
    successful_draw_bins: int
    refused_draw_bins: int
    not_run_draw_bins: int


__all__ = ["JointLRAPresentation", "JointProductStatus"]
