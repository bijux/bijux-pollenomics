"""Validate the fixed original R reference as retained report source evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.lra_reference.contracts import ReferenceRefusal
from bijux_pollenomics_dev.ci.lra_reference.evidence import validate_bundle
from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry, inventory_reports
from bijux_pollenomics_dev.lra_validation.reference_replay import CERTIFICATE_SHA256

from .contracts import JsonObject, ReportRebuildError

_PREFIX = "method-certification/original-r-reference/reference-bundle"


def validated_original_r_reference(
    repo_root: Path, policy: JsonObject
) -> tuple[InventoryEntry, ...]:
    """Bind retained source bytes to the independently pinned R certificate."""
    bundle = repo_root / cast(str, policy["tracked_report_root"]) / _PREFIX
    certificate_path = bundle / "certificate.json"
    try:
        certificate_bytes = certificate_path.read_bytes()
        if hashlib.sha256(certificate_bytes).hexdigest() != CERTIFICATE_SHA256:
            raise ReportRebuildError(
                "original R certificate differs from pinned source"
            )
        certificate = json.loads(certificate_bytes)
        validate_bundle(
            bundle,
            target_sha=certificate["source_commit"],
            expected_lock_sha256=certificate["lock_sha256"],
        )
        inventory = inventory_reports(bundle, policy)
    except (OSError, ValueError, KeyError, ReferenceRefusal) as error:
        raise ReportRebuildError(
            "original R retained source validation failed"
        ) from error
    if len(inventory) != 125:
        raise ReportRebuildError("original R retained source coverage changed")
    return tuple(
        InventoryEntry(
            path=f"{_PREFIX}/{entry.path}",
            kind=entry.kind,
            size=entry.size,
            sha256=entry.sha256,
            canonical_sha256=entry.canonical_sha256,
        )
        for entry in inventory
    )
