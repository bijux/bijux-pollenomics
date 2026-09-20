"""Typed identities for non-aggregated regional REVEALS components."""

from __future__ import annotations

from dataclasses import dataclass
import json
from math import isfinite
from pathlib import Path
import re
from typing import Literal

from ..engine.errors import LRARefusal

_DIGEST = re.compile(r"^[0-9a-f]{64}$")

ComponentStatus = Literal["completed", "refused", "failed", "not_run", "unobserved"]
ExecutionStatus = Literal["complete", "partial", "refused"]


def _identity(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise LRARefusal("invalid_regional_component_plan", f"Invalid {name}")
    return value


def _digest(value: object, name: str) -> str:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        raise LRARefusal("invalid_regional_component_plan", f"Invalid {name}")
    return value


@dataclass(frozen=True, slots=True)
class RegionalComponentPlan:
    """One explicitly ordered site cohort for one declared regional/time support.

    The plan authorizes component execution only. It contains no aggregation
    algorithm, weighting rule, covariance model or publication-profile claim.
    """

    component_set_id: str
    regional_support_id: str
    bin_id: str
    bin_bounds_bp: tuple[float, float]
    ordered_item_ids: tuple[str, ...]
    grouping_evidence_path: str
    grouping_evidence_sha256: str
    batch_summary_sha256: str
    schema_version: str = "regional-reveals-components.v1"
    aggregation_requested: bool = False
    aggregation_profile: None = None

    def __post_init__(self) -> None:
        if self.schema_version != "regional-reveals-components.v1":
            raise LRARefusal(
                "invalid_regional_component_plan", "Unsupported plan schema"
            )
        for name in ("component_set_id", "regional_support_id", "bin_id"):
            object.__setattr__(self, name, _identity(getattr(self, name), name))
        bounds = tuple(self.bin_bounds_bp)
        if (
            len(bounds) != 2
            or any(isinstance(value, bool) for value in bounds)
            or not all(isinstance(value, (int, float)) for value in bounds)
            or not all(isfinite(float(value)) for value in bounds)
            or float(bounds[0]) >= float(bounds[1])
        ):
            raise LRARefusal(
                "invalid_regional_component_plan",
                "bin_bounds_bp must be finite [younger, older] with younger < older",
            )
        object.__setattr__(self, "bin_bounds_bp", (float(bounds[0]), float(bounds[1])))
        items = tuple(self.ordered_item_ids)
        if not items or any(
            _identity(value, "ordered_item_id") != value for value in items
        ):
            raise LRARefusal(
                "invalid_regional_component_plan", "At least one item is required"
            )
        if len(set(items)) != len(items):
            raise LRARefusal(
                "invalid_regional_component_plan", "Item IDs must be unique"
            )
        object.__setattr__(self, "ordered_item_ids", items)
        path = _identity(self.grouping_evidence_path, "grouping_evidence_path")
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise LRARefusal(
                "invalid_regional_component_plan",
                "Grouping evidence must use a relative path inside the input root",
            )
        _digest(self.grouping_evidence_sha256, "grouping_evidence_sha256")
        _digest(self.batch_summary_sha256, "batch_summary_sha256")
        if (
            self.aggregation_requested is not False
            or self.aggregation_profile is not None
        ):
            raise LRARefusal(
                "aggregation_not_supported",
                "This plan authenticates components and cannot request aggregation",
            )

    def as_dict(self) -> dict[str, object]:
        """Return the complete, JSON-safe plan contract."""
        return {
            "schema_version": self.schema_version,
            "component_set_id": self.component_set_id,
            "regional_support_id": self.regional_support_id,
            "bin_id": self.bin_id,
            "bin_bounds_bp": list(self.bin_bounds_bp),
            "ordered_item_ids": list(self.ordered_item_ids),
            "grouping_evidence": {
                "path": self.grouping_evidence_path,
                "sha256": self.grouping_evidence_sha256,
            },
            "batch_summary_sha256": self.batch_summary_sha256,
            "aggregation_requested": False,
            "aggregation_profile": None,
        }


@dataclass(frozen=True, slots=True)
class RegionalComponentRecord:
    """One requested site component and its observed terminal outcome."""

    index: int
    item_id: str
    request_sha256: str
    site_id: str
    sample_id: str
    bin_id: str
    basin_type: str
    basin_diameter_m: float
    geometry_evidence_id: str
    item_status: ComponentStatus
    product_path: str | None = None
    product_manifest_sha256: str | None = None
    product_scientific_content_sha256: str | None = None
    product_producer_identity_json: str | None = None
    canonical_error: str | None = None

    def as_dict(self) -> dict[str, object]:
        """Return a lossless public row without inventing an estimate."""
        return {
            "index": self.index,
            "item_id": self.item_id,
            "request_sha256": self.request_sha256,
            "site_id": self.site_id,
            "sample_id": self.sample_id,
            "bin_id": self.bin_id,
            "geometry": {
                "site_type": self.basin_type,
                "diameter_m": self.basin_diameter_m,
                "geometry_evidence_id": self.geometry_evidence_id,
            },
            "item_status": self.item_status,
            "product_path": self.product_path,
            "product_manifest_sha256": self.product_manifest_sha256,
            "product_scientific_content_sha256": (
                self.product_scientific_content_sha256
            ),
            "product_producer_identity": (
                None
                if self.product_producer_identity_json is None
                else json.loads(self.product_producer_identity_json)
            ),
            "error": self.canonical_error,
        }

    def scientific_identity(self) -> dict[str, object]:
        """Retain the deterministic bundle-relative product path."""
        return self.as_dict()


@dataclass(frozen=True, slots=True)
class RegionalComponentSet:
    """Published component closure; never a regional aggregate estimate."""

    directory: Path
    manifest_sha256: str
    scientific_content_sha256: str
    component_execution_status: ExecutionStatus
    counts: dict[str, int]
