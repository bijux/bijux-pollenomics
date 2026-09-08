from __future__ import annotations

from dataclasses import dataclass

ACQUISITION_RECEIPT_SCHEMA_VERSION = "sead-acquisition-receipt.v1"
TABLE_PAYLOAD_SCHEMA_VERSION = "sead-table-payload.v1"
ACQUISITION_MANIFEST_SCHEMA_VERSION = "sead-acquisition-manifest.v1"
ACQUISITION_TOOL_VERSION = "sead-postgrest-acquisition.v1"
NORDIC_COUNTRY_CODES = ("SE", "DK", "NO", "FI", "UNASSIGNED")


@dataclass(frozen=True)
class SeadTableAcquisition:
    """One table payload and the receipt that proves how it was obtained."""

    table: str
    rows: tuple[dict[str, object], ...]
    receipt: dict[str, object]


class SeadAcquisitionError(RuntimeError):
    """A failed or partial table acquisition carrying its auditable result."""

    def __init__(self, message: str, result: SeadTableAcquisition) -> None:
        super().__init__(message)
        self.result = result
