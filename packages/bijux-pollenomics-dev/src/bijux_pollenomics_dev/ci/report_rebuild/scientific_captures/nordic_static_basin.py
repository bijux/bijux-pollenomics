"""Transport fixed Nordic aggregate/source/review captures without model replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.source_completion.pollen_reconstruction.nordic_static_basin.authority import (
    CAPTURE_PINS,
    PUBLICATION_AUTHORITY,
)

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

OWNER = "pollen-reconstruction/nordic-static-basin-scenarios/scientific-capture"
CAPTURE_AUTHORITY = {
    "original_scientific_candidate": "33d45ecfd6be7d275b69a7a7350bb72ae7c5269e",
    "original_scientific_plan_sha256": "84049168f9423f80c21b9c360f85b9f4025b5c92cd1afa096b253115cba98828",
    "original_scientific_control_sha256": "bccafc042a6d0e80c36a3761de8c969217f8610b42389a68e0565d6f5ece8a2b",
    "actual_scientific_report_sha256": "50d2e11aa053f22afe8aeb2b0867c2ee3c00340ad002a6ece71c36aafdbbedfe",
    "actual_scientific_terminal_sha256": "b00ad8785bacb49d6e48e3060acd9229e31e2ea26e356b6057bc82b6f924577c",
    "actual_source_census_sha256": "659a2fb5039b778ceb1879036f1a87238f7b021c3b2db5174fb66e582c262156",
    "actual_source_census_terminal_sha256": "4cf58a39d738f04c40e806b5f2ed716d7cf7327fe0003a2bceebbf4fe071af6f",
    "actual_scalar_review_sha256": "d419615c986bccb09bb67e7af68508885502b2a56fe1030a6ca7b6f13f92e486",
    "actual_scalar_review_terminal_sha256": "fc844afa08fe802f8800e6dd2ba2b4357896e36f67d1a1f4a412a003d3db384e",
    "actual_physical_review_sha256": "ce27a738d2673396daf9555537671f6c06560ffe3501413c0f27d6e76938ec78",
    "actual_physical_review_terminal_sha256": "419854788e096ef9dfa7a0e9c650df5cea762164331e1a0034aa18897464f7c8",
    "private_raw_source_support_sha256": "10c250757923f37ac383b2efd6fcc41af3d5d73b21f69f65ff6fee99443e2fa7",
    "original_foreground_diagnostic_scope": "Saved aggregate bookkeeping projection; not a native independent numerical/physical receipt.",
}


def validated_nordic_static_basin_captures(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Admit exact retained Nordic captures without repeating numerical execution."""
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    if not rows and not set(CAPTURE_PINS).intersection(tracked_by_path):
        return (), {}
    retained_rows = []
    for owner in owners:
        paths = owner.get("paths", [])
        if not isinstance(paths, list) or any(
            not isinstance(name, str) for name in paths
        ):
            raise ReportRebuildError(
                "scientific capture owner paths must be a string list"
            )
        # This transport owns its sealed capture paths, not every report in the family.
        if set(CAPTURE_PINS).intersection(paths):
            if owner.get("role") != "retained_source":
                raise ReportRebuildError("Nordic static-basin capture owner differs")
            retained_rows.append(owner)
    if len(rows) != 1 or retained_rows != rows:
        raise ReportRebuildError("Nordic static-basin capture owner differs")
    row = rows[0]
    if (
        row.get("role") != "retained_source"
        or row.get("paths") != sorted(CAPTURE_PINS)
        or row.get("producer_paths") != []
        or row.get("producer_inputs") != []
    ):
        raise ReportRebuildError("Nordic static-basin capture declaration differs")
    entries = []
    for name, expected in sorted(CAPTURE_PINS.items()):
        try:
            path = _regular_confined_file(repository, name, "Nordic scientific capture")
            body = path.read_bytes()
            value = json.loads(body)
            valid = (
                isinstance(value, list)
                if name.endswith("verification/physical-response-tuples.json")
                else isinstance(value, dict)
            )
            entry = tracked_by_path.get(name)
        except (OSError, ValueError) as error:
            raise ReportRebuildError(
                "Nordic scientific capture input refused"
            ) from error
        if (
            not valid
            or entry is None
            or entry.kind != "file"
            or entry.size != len(body)
            or entry.sha256 != expected
            or hashlib.sha256(body).hexdigest() != expected
        ):
            raise ReportRebuildError("Nordic scientific capture bytes changed")
        entries.append(entry)
    return tuple(entries), {
        "owner_id": OWNER,
        "original_capture_authority": dict(CAPTURE_AUTHORITY),
        "native_publication_capture_authority": dict(PUBLICATION_AUTHORITY),
        "reviewed_capture_sha256": dict(CAPTURE_PINS),
        "paths": [entry.path for entry in entries],
        "source_scope": "Twenty-two exact captures: fourteen original aggregate/source/protocol/import/terminal/policy/diagnostic and independent scalar/physical records, plus eight separately qualified native publication acquisition/response/terminal records for four dataset relations to three primary publications. Native metadata attribution does not authenticate article contents. The original scientific pending flag is preserved; separate actual reviews admit only their declared9case/182window/6840value or23tuple/29use consumers. Transport repeats no acquisition, model, physical quadrature or R computation. Private raw314sample count/age/mask support stays local. No full vegetation/cross-panel comparable composition, historical reproduction, chronology accuracy, raw rights, morphology/partition or qualified human review is admitted.",
    }
