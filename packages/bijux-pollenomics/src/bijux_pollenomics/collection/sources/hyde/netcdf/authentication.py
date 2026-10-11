"""Source-bound public facade for retained HYDE NetCDF declarations."""

from __future__ import annotations

from pathlib import Path

from .contracts import HydeNetcdfDeclarationInventory
from .reading import (
    _read_hyde_netcdf_declaration_inventory,
    _reopen_hyde_netcdf_declaration_inventory,
)

_FILE_INVENTORY_SHA256 = (
    "727893bef686146611dcb702e7fab5c497f70c8630b8d2a3fc158b3b5b7d53ef"
)
_INVENTORY_REPORT_SHA256 = (
    "3b951d91b064fa6885ec5e3ffaac82217bb7d9058f11e21d9b58216f4d3d1ac9"
)
_HEADER_INVENTORY_SHA256 = (
    "b1809b9a5f935332c336aa695b9c2614a5c8db4a15ee1b86106fa6a13a622d1f"
)
_CONFLICT_REPORT_SHA256 = (
    "1de8918edcb9e27507effc6ab360a7c23a4e06c9bbb369552ea3e4d88589fcbb"
)


def read_hyde_netcdf_declaration_inventory(
    *,
    file_inventory_path: Path,
    inventory_report_path: Path,
    header_inventory_path: Path,
    conflict_report_path: Path,
) -> HydeNetcdfDeclarationInventory:
    """Read the four shipped compact inputs as a refusal-only declaration view."""
    return _read_hyde_netcdf_declaration_inventory(
        file_inventory_path=file_inventory_path,
        expected_file_inventory_sha256=_FILE_INVENTORY_SHA256,
        inventory_report_path=inventory_report_path,
        expected_inventory_report_sha256=_INVENTORY_REPORT_SHA256,
        header_inventory_path=header_inventory_path,
        expected_header_inventory_sha256=_HEADER_INVENTORY_SHA256,
        conflict_report_path=conflict_report_path,
        expected_conflict_report_sha256=_CONFLICT_REPORT_SHA256,
    )


def reopen_hyde_netcdf_declaration_inventory(
    canonical_bytes: bytes,
    *,
    file_inventory_path: Path,
    inventory_report_path: Path,
    header_inventory_path: Path,
    conflict_report_path: Path,
) -> HydeNetcdfDeclarationInventory:
    """Reconstruct from shipped parents and accept only their canonical bytes."""
    return _reopen_hyde_netcdf_declaration_inventory(
        canonical_bytes,
        file_inventory_path=file_inventory_path,
        expected_file_inventory_sha256=_FILE_INVENTORY_SHA256,
        inventory_report_path=inventory_report_path,
        expected_inventory_report_sha256=_INVENTORY_REPORT_SHA256,
        header_inventory_path=header_inventory_path,
        expected_header_inventory_sha256=_HEADER_INVENTORY_SHA256,
        conflict_report_path=conflict_report_path,
        expected_conflict_report_sha256=_CONFLICT_REPORT_SHA256,
    )
