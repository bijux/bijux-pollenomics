"""Immutable receipts for authenticated observations and their prediction join."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from ...contracts import required_identity
from ..contracts import EvaluationRow, digest, refuse
from ..observation_access import ObservationAssignment
from ..observation_sources import (
    HeldoutPollenCountUnit,
    MeasuredVegetationUnit,
)

AUTHENTICATED_OBSERVATION_PROFILE = "pollenomics-authenticated-observations.v1"
OBSERVED_SIX_CELL_PROFILE = "pollenomics-observed-six-cell-product.v1"
ObservationStatus = Literal["available", "missing", "refused"]
SourceUnit = MeasuredVegetationUnit | HeldoutPollenCountUnit


@dataclass(frozen=True)
class AuthenticatedObservationAssignment:
    """One model-free assignment derived from the frozen access plan."""

    protocol_id: str
    cell_id: str
    fold_id: str
    record_id: str
    target: str
    observation_kind: str
    observation_id: str
    source_reference_id: str
    source_product_sha256: str
    source_unit_sha256: str
    status: ObservationStatus
    reason: str | None

    def __post_init__(self) -> None:
        for value in (
            self.protocol_id,
            self.cell_id,
            self.fold_id,
            self.record_id,
            self.target,
            self.observation_kind,
            self.observation_id,
            self.source_reference_id,
        ):
            required_identity(value)
        for value in (self.source_product_sha256, self.source_unit_sha256):
            digest(value)
        if (self.target, self.observation_kind) not in {
            ("vegetation_cover", "independent_measured_vegetation"),
            ("pollen_composition", "heldout_pollen_counts"),
        }:
            refuse("Authenticated observation assignment kind differs from target")
        if self.status not in {"available", "missing", "refused"}:
            refuse("Authenticated observation assignment status differs")
        if (self.status == "available") != (self.reason is None):
            refuse("Authenticated observation assignment reason differs")
        if self.reason is not None:
            required_identity(self.reason)

    @property
    def key(self) -> tuple[str, str, str, str]:
        return self.protocol_id, self.cell_id, self.fold_id, self.record_id

    def matches_plan(self, planned: ObservationAssignment) -> bool:
        return (
            self.protocol_id,
            self.cell_id,
            self.fold_id,
            self.record_id,
            self.target,
            self.observation_kind,
            self.observation_id,
            self.source_reference_id,
        ) == (
            planned.protocol_id,
            planned.cell_id,
            planned.fold_id,
            planned.record_id,
            planned.target,
            planned.observation_kind,
            planned.observation_id,
            planned.source_reference_id,
        )


@dataclass(frozen=True)
class ObservedRowAttachment:
    """Separate prediction and source terminals for one joined comparison row."""

    protocol_id: str
    cell_id: str
    row: EvaluationRow
    prediction_status: str
    observation_status: ObservationStatus
    observation_reason: str | None
    observation_id: str
    source_product_sha256: str
    source_unit_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.row, EvaluationRow):
            refuse("Observed attachments require typed evaluation rows")
        for value in (
            self.protocol_id,
            self.cell_id,
            self.observation_id,
        ):
            required_identity(value)
        if self.prediction_status != self.row.status:
            refuse("Observed attachment prediction status differs")
        if self.observation_status not in {"available", "missing", "refused"}:
            refuse("Observed attachment source status differs")
        if (self.observation_status == "available") != (
            self.observation_reason is None
        ):
            refuse("Observed attachment source reason differs")
        if self.observation_reason is not None:
            required_identity(self.observation_reason)
        attached = (
            self.row.status == "predicted" and self.observation_status == "available"
        )
        fields_present = (
            self.row.observation is not None,
            self.row.observation_reference_id is not None,
            self.row.observation_kind is not None,
            self.row.observation_support is not None,
        )
        if any(fields_present) != all(fields_present) or attached != all(
            fields_present
        ):
            refuse("Observed attachment fields differ from its two status channels")
        if self.row.status not in {"predicted", "prediction_failed"}:
            refuse("Observed products do not admit excluded prediction parents")
        digest(self.source_product_sha256)
        digest(self.source_unit_sha256)

    @property
    def key(self) -> tuple[str, str, str, str, str]:
        return (
            self.protocol_id,
            self.cell_id,
            self.row.fold_id,
            self.row.record_id,
            self.row.model_id,
        )
