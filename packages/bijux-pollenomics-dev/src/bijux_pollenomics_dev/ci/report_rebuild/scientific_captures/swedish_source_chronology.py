"""Transport original Tibetanus point-sensitivity captures with exact authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.swedish_source_chronology.authority import (
    CAPTURE_PINS,
    FAMILY,
)

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

OWNER = "pollen-reconstruction/tibetanus-point-age-sensitivity/scientific-capture"
CAPTURE_AUTHORITY = {
    "actual_scientific_plan_sha256": "a36aff64a0e7e794c6911fa021da0a1f1efc1598382db0c4616cf6843b9cd5be",
    "actual_scientific_registration_candidate": "3e6935b96111da878bf0d7065adf65526891ba53",
    "actual_scientific_terminal_sha256": "cb8111b4ee4d660a2633e967cf561af551a69ed5838df045af8dab87f90e0c0f",
    "actual_scientific_report_sha256": "5abb9af22673ec7e93fb38642b2d5f7958bd002218a5edd4514e11ffa093e5fe",
    "private_source_point_support_sha256": "7173832dbe169d089db1219b97cf3ee3c62529a4c069a42262190aee921ab156",
    "diagnostic_producer_sha256": "b4b09281b454efa70d5396f1c7e4e16944e8d24f4b6f06833d1c116d2f430b8b",
    "diagnostic_custody_scope": "Foreground source-bound projection; no native supervised terminal or independent numerical oracle.",
    "actual_saved_source_output_review_sha256": "2625f8ce8d37f520db3078f925cbdf549273f8dd7065bb6bd28025426d19af8f",
    "saved_source_output_review_scope": "Read-only source/case membership and saved native baseline output verification; no model rerun or qualified human review.",
}


def validated_swedish_source_chronology_captures(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit exactly nine original records, preserving failed predecessors."""
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    active = bool(rows) or any(
        name.startswith(FAMILY + "/") for name in tracked_by_path
    )
    if not active:
        return (), {}
    retained_rows = [
        row
        for row in owners
        if row.get("role") == "retained_source"
        and any(
            isinstance(name, str) and name.startswith(FAMILY + "/")
            for name in row.get("paths", [])
        )
    ]
    if len(rows) != 1 or retained_rows != rows:
        raise ReportRebuildError("Tibetanus chronology capture owner differs")
    row = rows[0]
    if (
        row.get("role") != "retained_source"
        or row.get("paths") != sorted(CAPTURE_PINS)
        or row.get("producer_paths") != []
        or row.get("producer_inputs") != []
    ):
        raise ReportRebuildError("Tibetanus chronology capture declaration differs")
    accepted = []
    for name, expected in sorted(CAPTURE_PINS.items()):
        try:
            path = _regular_confined_file(repository, name, "chronology capture")
            body = path.read_bytes()
            valid = isinstance(json.loads(body), dict)
            entry = tracked_by_path.get(name)
        except (OSError, ValueError) as error:
            raise ReportRebuildError(
                "Tibetanus chronology capture input refused"
            ) from error
        if (
            not valid
            or entry is None
            or entry.kind != "file"
            or entry.size != len(body)
            or entry.sha256 != expected
            or hashlib.sha256(body).hexdigest() != expected
        ):
            raise ReportRebuildError("Tibetanus chronology capture bytes changed")
        accepted.append(entry)
    return tuple(accepted), {
        "owner_id": OWNER,
        "original_capture_authority": dict(CAPTURE_AUTHORITY),
        "reviewed_capture_sha256": dict(CAPTURE_PINS),
        "paths": [entry.path for entry in accepted],
        "source_scope": "Nine exact original protocol, documentary, native numerical, foreground diagnostic, read-only review and failed source-comparison records. Transport performs no source acquisition, chronology fit, model execution or physical integration; it admits no new historical, vegetation, chronology accuracy, taxonomy, rights or qualified human review claim. Private raw sample/age/count associations remain outside the report tree.",
    }
