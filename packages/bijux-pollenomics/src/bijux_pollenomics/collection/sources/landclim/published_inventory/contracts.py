"""Typed contracts for retained LandClim II published estimates."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
from typing import ClassVar, Literal

from ..collection.model import LandClimRawReceiptError

SCHEMA_VERSION = "landclim-published-estimate-inventory.v1"
EVIDENCE_ROLE = "published_reconstruction_comparison_target"
VALUE_UNIT = "percentage_cover"


class LandClimPublishedInventoryRefusal(LandClimRawReceiptError):
    """Raised when the published-result closure is not exact and source-bound."""


CoordinateStatus = Literal["available", "refused"]


@dataclass(frozen=True, slots=True)
class LandClimPublishedEstimate:
    """One paired published mean/SE value with both source-native tokens."""

    variable: str
    mean_token: str
    mean: Decimal
    standard_error_token: str
    standard_error: Decimal

    def payload(self) -> dict[str, object]:
        """Return exact JSON-safe values without reformatting source tokens."""
        return {
            "variable": self.variable,
            "mean_token": self.mean_token,
            "mean": str(self.mean),
            "standard_error_token": self.standard_error_token,
            "standard_error": str(self.standard_error),
        }


@dataclass(frozen=True, slots=True)
class LandClimPublishedEstimateRow:
    """One mean/SE grid-window row, including coordinate refusals."""

    time_window: str
    cell_id: str
    mean_cell_id_token: str
    standard_error_cell_id_token: str
    mean_source_locator: str
    standard_error_source_locator: str
    mean_longitude_token: str
    mean_latitude_token: str
    standard_error_longitude_token: str
    standard_error_latitude_token: str
    longitude: Decimal | None
    latitude: Decimal | None
    coordinate_status: CoordinateStatus
    coordinate_refusal_reason: str | None
    estimates: tuple[LandClimPublishedEstimate, ...]
    evidence_role: str = field(default=EVIDENCE_ROLE, init=False)
    value_unit: str = field(default=VALUE_UNIT, init=False)

    def payload(self) -> dict[str, object]:
        """Return the retained values and explicit spatial eligibility posture."""
        return {
            "time_window": self.time_window,
            "cell_id": self.cell_id,
            "source_identity_tokens": {
                "mean_cell_id": self.mean_cell_id_token,
                "standard_error_cell_id": self.standard_error_cell_id_token,
            },
            "source_locators": {
                "mean": self.mean_source_locator,
                "standard_error": self.standard_error_source_locator,
            },
            "coordinates": {
                "mean_longitude_token": self.mean_longitude_token,
                "mean_latitude_token": self.mean_latitude_token,
                "standard_error_longitude_token": (self.standard_error_longitude_token),
                "standard_error_latitude_token": (self.standard_error_latitude_token),
                "longitude": None if self.longitude is None else str(self.longitude),
                "latitude": None if self.latitude is None else str(self.latitude),
                "status": self.coordinate_status,
                "refusal_reason": self.coordinate_refusal_reason,
            },
            "evidence_role": self.evidence_role,
            "value_unit": self.value_unit,
            "estimates": [estimate.payload() for estimate in self.estimates],
        }


_FACTORY_TOKEN = object()


@dataclass(frozen=True, init=False, slots=True)
class LandClimPublishedEstimateInventory:
    """Authenticated published outputs, never a raw-input model rerun."""

    receipt_sha256: str
    archive_sha256: str
    dataset_doi: str
    time_windows: tuple[str, ...]
    variables: tuple[str, ...]
    records: tuple[LandClimPublishedEstimateRow, ...]
    coordinate_available_record_count: int
    coordinate_refused_record_count: int
    mean_zero_value_count: int
    mean_above_one_value_count: int
    mean_negative_value_count: int
    mean_negative_record_count: int
    schema_version: ClassVar[str] = SCHEMA_VERSION
    evidence_role: ClassVar[str] = EVIDENCE_ROLE
    value_unit: ClassVar[str] = VALUE_UNIT
    expected_mean_member_count: ClassVar[int] = 25
    expected_standard_error_member_count: ClassVar[int] = 25
    expected_record_count: ClassVar[int] = 10500
    expected_variable_count: ClassVar[int] = 47
    expected_value_pair_count: ClassVar[int] = 493500
    published_products_only: ClassVar[bool] = True
    raw_pollen_inputs_authenticated: ClassVar[bool] = False
    historical_chronologies_authenticated: ClassVar[bool] = False
    original_r_execution: ClassVar[bool] = False
    pft_discrepancy_resolved: ClassVar[bool] = False
    published_product_rights: ClassVar[str] = "not_evaluated"
    independent_measured_vegetation: ClassVar[bool] = False
    whole_paper_reproduction_certified: ClassVar[bool] = False
    publication_allowed: ClassVar[bool] = False
    scientifically_accepted: ClassVar[bool] = False
    scientific_acceptance: ClassVar[str] = "not_evaluated"

    def __init__(
        self,
        *,
        receipt_sha256: str,
        archive_sha256: str,
        dataset_doi: str,
        time_windows: tuple[str, ...],
        variables: tuple[str, ...],
        records: tuple[LandClimPublishedEstimateRow, ...],
        coordinate_available_record_count: int,
        coordinate_refused_record_count: int,
        mean_zero_value_count: int,
        mean_above_one_value_count: int,
        mean_negative_value_count: int,
        mean_negative_record_count: int,
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise LandClimPublishedInventoryRefusal(
                "LandClim published inventory must be created by its governed reader"
            )
        object.__setattr__(self, "receipt_sha256", receipt_sha256)
        object.__setattr__(self, "archive_sha256", archive_sha256)
        object.__setattr__(self, "dataset_doi", dataset_doi)
        object.__setattr__(self, "time_windows", time_windows)
        object.__setattr__(self, "variables", variables)
        object.__setattr__(self, "records", records)
        object.__setattr__(
            self, "coordinate_available_record_count", coordinate_available_record_count
        )
        object.__setattr__(
            self, "coordinate_refused_record_count", coordinate_refused_record_count
        )
        object.__setattr__(self, "mean_zero_value_count", mean_zero_value_count)
        object.__setattr__(
            self, "mean_above_one_value_count", mean_above_one_value_count
        )
        object.__setattr__(self, "mean_negative_value_count", mean_negative_value_count)
        object.__setattr__(
            self, "mean_negative_record_count", mean_negative_record_count
        )

    @property
    def record_count(self) -> int:
        """Return the complete mean/SE row-pair denominator."""
        return len(self.records)

    @property
    def value_pair_count(self) -> int:
        """Return the complete paired variable-value denominator."""
        return sum(len(record.estimates) for record in self.records)

    def payload(self) -> dict[str, object]:
        """Return a deterministic manifest with non-admission claims explicit."""
        return {
            "schema_version": self.schema_version,
            "inputs": {
                "receipt_sha256": self.receipt_sha256,
                "archive_sha256": self.archive_sha256,
            },
            "dataset_doi": self.dataset_doi,
            "evidence_role": self.evidence_role,
            "value_unit": self.value_unit,
            "time_windows": list(self.time_windows),
            "variables": list(self.variables),
            "denominators": {
                "mean_members": self.expected_mean_member_count,
                "standard_error_members": self.expected_standard_error_member_count,
                "paired_records": self.record_count,
                "variables_per_record": self.expected_variable_count,
                "paired_values": self.value_pair_count,
                "coordinate_available_records": (
                    self.coordinate_available_record_count
                ),
                "coordinate_refused_records": self.coordinate_refused_record_count,
                "mean_zero_values": self.mean_zero_value_count,
                "mean_values_above_one": self.mean_above_one_value_count,
                "mean_negative_values": self.mean_negative_value_count,
                "mean_negative_records": self.mean_negative_record_count,
            },
            "records": [record.payload() for record in self.records],
            "admission": {
                "published_products_only": self.published_products_only,
                "raw_pollen_inputs_authenticated": (
                    self.raw_pollen_inputs_authenticated
                ),
                "historical_chronologies_authenticated": (
                    self.historical_chronologies_authenticated
                ),
                "original_r_execution": self.original_r_execution,
                "pft_discrepancy_resolved": self.pft_discrepancy_resolved,
                "published_product_rights": self.published_product_rights,
                "independent_measured_vegetation": (
                    self.independent_measured_vegetation
                ),
                "whole_paper_reproduction_certified": (
                    self.whole_paper_reproduction_certified
                ),
                "publication_allowed": self.publication_allowed,
                "scientifically_accepted": self.scientifically_accepted,
                "scientific_acceptance": self.scientific_acceptance,
            },
        }

    @property
    def canonical_bytes(self) -> bytes:
        """Return deterministic bytes for the exact source-derived inventory."""
        return json.dumps(
            self.payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @property
    def sha256(self) -> str:
        """Return the canonical inventory identity."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def _mint_inventory(
    *,
    receipt_sha256: str,
    archive_sha256: str,
    dataset_doi: str,
    time_windows: tuple[str, ...],
    variables: tuple[str, ...],
    records: tuple[LandClimPublishedEstimateRow, ...],
    coordinate_available_record_count: int,
    coordinate_refused_record_count: int,
    mean_zero_value_count: int,
    mean_above_one_value_count: int,
    mean_negative_value_count: int,
    mean_negative_record_count: int,
) -> LandClimPublishedEstimateInventory:
    return LandClimPublishedEstimateInventory(
        receipt_sha256=receipt_sha256,
        archive_sha256=archive_sha256,
        dataset_doi=dataset_doi,
        time_windows=time_windows,
        variables=variables,
        records=records,
        coordinate_available_record_count=coordinate_available_record_count,
        coordinate_refused_record_count=coordinate_refused_record_count,
        mean_zero_value_count=mean_zero_value_count,
        mean_above_one_value_count=mean_above_one_value_count,
        mean_negative_value_count=mean_negative_value_count,
        mean_negative_record_count=mean_negative_record_count,
        _factory_token=_FACTORY_TOKEN,
    )
