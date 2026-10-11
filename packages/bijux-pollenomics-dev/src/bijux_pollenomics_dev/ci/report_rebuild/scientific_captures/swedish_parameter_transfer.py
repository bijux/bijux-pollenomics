"""Transport exact broader scenario captures without repeating their consumers."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry

from ..contracts import JsonObject, ReportRebuildError
from ..ownership import _regular_confined_file

FAMILY = "docs/report/pollen-reconstruction/swedish-parameter-transfer-scenarios"
OWNER = "pollen-reconstruction/swedish-parameter-transfer-scenarios/scientific-capture"
CAPTURE_PINS = {
    FAMILY
    + "/execution/independent-physical-response-review.json": "123de5038343c22bcf02c25a3b69160755d0c3c563cc4705e10db9630323147e",
    FAMILY
    + "/execution/independent-scientific-source-review.json": "0fe8391ac7b09387b0f376b359beb5a0079e42526dcf6d02071991553d61303e",
    FAMILY
    + "/execution/independent-source-mask-review.json": "19b4cf2bd6bc11de2835680a61d0d35200adc4cdd81e11d21f36f2fc73be9389",
    FAMILY
    + "/execution/maintained-producer-capture.json": "57eabe192b5d7582d88049a61cbdc271a96502f544e7fac42757748f20f65a2a",
    FAMILY
    + "/execution/observed-imports.json": "34ce457892496a942950dbf07b4870399ee3e3a50d577af5ee4d2424ce043da8",
    FAMILY
    + "/inputs/engine-source-identities.json": "a4eda356f001bf5326e652bf6867aa9672957b0def1d5210e819a893d28e9e4f",
}
CAPTURE_AUTHORITY = {
    "maintained_source_candidate": "827cdccd64273cdeb59f7ac4ce42b005a6aa4c8f",
    "actual_maintained_plan_sha256": "9fa2b7804f52bc3bb953a8d07a53fea27ca79266655400bd453fb1a4e9b8b636",
    "actual_maintained_terminal_sha256": "ad217ffc8d1a23d4efe2212c28a3ee6a4d07cfc67340fcb6b82f59ff3fb8aacd",
    "actual_reference_replay_report_sha256": "4d682a9b8ed2fde20ec4cbec4d0604d21596451511726fd8a3692ae7f69e610d",
    "actual_reference_replay_comparison_sha256": "081ef7687745154135adac4a41a07e497af31f025aba11fcc66ea43d5eb3bbe0",
    "private_actual_source_mask_capsule_sha256": "c6cd154713d0cfed085435341752b8798e05ec219efeaf01d7c9d2f4b518d888",
    "actual_source_support_keys": 316,
    "actual_compared_saved_numerical_values": 344952,
    "scalar_review_terminal_sha256": "a039698ace02c6cff2b6193921638186d3fb2b8426eba0ccbc1a0a496c696a7a",
    "physical_review_terminal_sha256": "1c8b8f2efb9fa599ea708418c04b8f80f5c9e97a33455475f1fc44d9a7dbac0e",
    "scientific_code_review_scope": (
        "Independent read-only source inspection; no native computation or "
        "qualified external review receipt is claimed."
    ),
}


def validated_swedish_parameter_transfer_captures(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Refuse changes to the exact retained family and its original authority."""
    rows = [row for row in owners if row.get("owner_id") == OWNER]
    active = bool(rows) or any(
        name.startswith(FAMILY + "/") for name in tracked_by_path
    )
    if not active:
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
        if owner.get("role") == "retained_source" and any(
            name.startswith(FAMILY + "/") for name in paths
        ):
            retained_rows.append(owner)
    if len(rows) != 1 or retained_rows != rows:
        raise ReportRebuildError("Swedish parameter-transfer capture owner differs")
    row = rows[0]
    if (
        row.get("role") != "retained_source"
        or row.get("paths") != sorted(CAPTURE_PINS)
        or row.get("producer_paths") != []
        or row.get("producer_inputs") != []
    ):
        raise ReportRebuildError(
            "Swedish parameter-transfer capture declaration differs"
        )
    accepted = []
    for name, expected in sorted(CAPTURE_PINS.items()):
        try:
            path = _regular_confined_file(
                repository, name, "parameter-transfer capture"
            )
            body = path.read_bytes()
            valid = isinstance(json.loads(body), dict)
            entry = tracked_by_path.get(name)
        except (OSError, ValueError) as error:
            raise ReportRebuildError(
                "Swedish parameter-transfer capture input refused"
            ) from error
        if (
            not valid
            or entry is None
            or entry.kind != "file"
            or entry.size != len(body)
            or entry.sha256 != expected
            or hashlib.sha256(body).hexdigest() != expected
        ):
            raise ReportRebuildError("Swedish parameter-transfer capture bytes changed")
        accepted.append(entry)
    return tuple(accepted), {
        "owner_id": OWNER,
        "original_capture_authority": dict(CAPTURE_AUTHORITY),
        "reviewed_capture_sha256": dict(CAPTURE_PINS),
        "paths": [entry.path for entry in accepted],
        "source_scope": (
            "Six immutable native producer/import/engine and independent review "
            "records retain their exact original source and consumer scopes. "
            "Current transport repeats no mathematical, physical or R consumer, "
            "does not promote the private raw sample masks, and establishes no "
            "new taxonomy, observed sparse zeros, historical reproduction, "
            "ecological accuracy, calibrated uncertainty, reader qualification, "
            "qualified external review or source rights."
        ),
    }
