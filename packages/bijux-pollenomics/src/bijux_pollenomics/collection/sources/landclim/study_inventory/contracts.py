"""Typed, refusal-bounded LandClim full-study metadata inventory."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
import hashlib
import json
from typing import Literal

from ..collection.model import LandClimRawReceiptError

SCHEMA_VERSION = "landclim-study-metadata-inventory.v1"


class LandClimStudyInventoryRefusal(LandClimRawReceiptError):
    """Raised when the governed study-metadata closure is not exact."""


ValueKind = Literal["null", "text", "number"]


@dataclass(frozen=True)
class StudyMetadataValue:
    """One source-native cell with its raw spelling and conservative type."""

    column: str
    kind: ValueKind
    raw: str | None
    number: Decimal | None

    def payload(self) -> dict[str, object]:
        """Return an exact JSON-safe representation without rounding numbers."""
        return {
            "column": self.column,
            "kind": self.kind,
            "raw": self.raw,
            "number": None if self.number is None else str(self.number),
        }


@dataclass(frozen=True)
class StudyMetadataRecord:
    """One retained workbook row, not an inferred provider sample identity."""

    worksheet_row: int
    source_locator: str
    values: tuple[StudyMetadataValue, ...]
    primary_pollen_count_identity: None = field(default=None, init=False)
    chronology_input_identity: None = field(default=None, init=False)
    rights_status: str = field(default="unresolved", init=False)

    def payload(self) -> dict[str, object]:
        """Return the explicit per-row refusal and retained source values."""
        return {
            "worksheet_row": self.worksheet_row,
            "source_locator": self.source_locator,
            "values": [value.payload() for value in self.values],
            "primary_pollen_count_identity": self.primary_pollen_count_identity,
            "chronology_input_identity": self.chronology_input_identity,
            "rights_status": self.rights_status,
        }


_FACTORY_TOKEN = object()


@dataclass(frozen=True, init=False)
class LandClimStudyMetadataInventory:
    """Authenticated publication metadata that grants no input admission."""

    receipt_sha256: str
    workbook_sha256: str
    dataset_doi: str
    sheet_name: str
    header: tuple[str, ...]
    records: tuple[StudyMetadataRecord, ...]
    schema_version: str = field(default=SCHEMA_VERSION, init=False)
    expected_record_count: int = field(default=1128, init=False)
    publication_metadata_only: bool = field(default=True, init=False)
    raw_pollen_counts_authenticated: bool = field(default=False, init=False)
    historical_chronologies_authenticated: bool = field(default=False, init=False)
    per_sequence_rights_cleared: bool = field(default=False, init=False)
    reproduction_input_complete: bool = field(default=False, init=False)
    publication_allowed: bool = field(default=False, init=False)
    scientifically_accepted: bool = field(default=False, init=False)
    scientific_acceptance: str = field(default="not_evaluated", init=False)

    def __init__(
        self,
        *,
        receipt_sha256: str,
        workbook_sha256: str,
        dataset_doi: str,
        sheet_name: str,
        header: tuple[str, ...],
        records: tuple[StudyMetadataRecord, ...],
        _factory_token: object | None = None,
    ) -> None:
        if _factory_token is not _FACTORY_TOKEN:
            raise LandClimStudyInventoryRefusal(
                "LandClim study inventory must be created by its governed reader"
            )
        object.__setattr__(self, "receipt_sha256", receipt_sha256)
        object.__setattr__(self, "workbook_sha256", workbook_sha256)
        object.__setattr__(self, "dataset_doi", dataset_doi)
        object.__setattr__(self, "sheet_name", sheet_name)
        object.__setattr__(self, "header", header)
        object.__setattr__(self, "records", records)

    @property
    def metadata_record_count(self) -> int:
        """Return the exact retained publication-metadata denominator."""
        return len(self.records)

    def payload(self) -> dict[str, object]:
        """Return a canonical manifest with explicit zero-closure claims."""
        return {
            "schema_version": self.schema_version,
            "inputs": {
                "receipt_sha256": self.receipt_sha256,
                "workbook_sha256": self.workbook_sha256,
            },
            "dataset_doi": self.dataset_doi,
            "sheet_name": self.sheet_name,
            "header": list(self.header),
            "denominators": {
                "expected_study_records": self.expected_record_count,
                "publication_metadata_records": self.metadata_record_count,
                "authenticated_primary_pollen_count_records": 0,
                "authenticated_historical_chronology_records": 0,
                "rights_cleared_records": 0,
            },
            "records": [record.payload() for record in self.records],
            "admission": {
                "publication_metadata_only": self.publication_metadata_only,
                "raw_pollen_counts_authenticated": (
                    self.raw_pollen_counts_authenticated
                ),
                "historical_chronologies_authenticated": (
                    self.historical_chronologies_authenticated
                ),
                "per_sequence_rights_cleared": self.per_sequence_rights_cleared,
                "reproduction_input_complete": self.reproduction_input_complete,
                "publication_allowed": self.publication_allowed,
                "scientifically_accepted": self.scientifically_accepted,
                "scientific_acceptance": self.scientific_acceptance,
            },
        }

    @property
    def canonical_bytes(self) -> bytes:
        """Return deterministic bytes for the exact typed product."""
        return json.dumps(
            self.payload(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")

    @property
    def sha256(self) -> str:
        """Return the canonical product identity."""
        return hashlib.sha256(self.canonical_bytes).hexdigest()


def _mint_inventory(
    *,
    receipt_sha256: str,
    workbook_sha256: str,
    dataset_doi: str,
    sheet_name: str,
    header: tuple[str, ...],
    records: tuple[StudyMetadataRecord, ...],
) -> LandClimStudyMetadataInventory:
    return LandClimStudyMetadataInventory(
        receipt_sha256=receipt_sha256,
        workbook_sha256=workbook_sha256,
        dataset_doi=dataset_doi,
        sheet_name=sheet_name,
        header=header,
        records=records,
        _factory_token=_FACTORY_TOKEN,
    )
