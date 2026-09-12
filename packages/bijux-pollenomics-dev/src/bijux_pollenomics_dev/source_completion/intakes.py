"""Inventory supplied intake receipts while preserving their admission decisions."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .evidence import EvidenceReader, digest


def audit_intakes(root: Path) -> dict[str, Any]:
    """Verify delivered bytes against receipts; never promote quarantine to admission."""
    reader = EvidenceReader(root)
    receipts = []
    directory = root / "contracts/intake"
    for path in sorted(directory.glob("*.json")):
        relative = path.relative_to(root).as_posix()
        receipt = reader.json(relative)
        if receipt is None or "intake_id" not in receipt:
            continue
        delivery = receipt["delivery"]
        original_name = delivery.get("original_name")
        actual = None
        if original_name:
            reader.verify(
                original_name,
                {
                    "sha256": delivery.get("sha256"),
                    "byte_count": delivery.get("byte_size"),
                },
            )
            actual = reader.files[original_name]
        receipts.append(
            {
                "intake_id": receipt["intake_id"],
                "receipt_path": relative,
                "lifecycle_state": receipt["lifecycle_state"],
                "declared_delivery": delivery,
                "observed_original_file": actual,
                "rights": receipt["rights"],
                "decision": receipt["decision"],
                "scientific_scope": receipt["scientific_scope"],
                "country_coverage": receipt["country_coverage"],
                "semantic_confirmation": "not_established_by_delivery_verification",
            }
        )
    return {
        "schema_version": "source-intake-receipt-audit.v1",
        "receipt_count": len(receipts),
        "receipts": receipts,
        "accounting_findings": reader.issues,
        "manifest_byte_verifications": sorted(
            reader.verifications.values(), key=lambda entry: entry["path"]
        ),
        "input_files": sorted(reader.files.values(), key=lambda entry: entry["path"]),
        "input_closure_sha256": digest(
            sorted(reader.files.values(), key=lambda entry: entry["path"])
        ),
        "scope": "Only receipt files in contracts/intake and their root-local original filenames; historical lifecycle and rights remain unchanged.",
    }


def find_hyde_candidates(roots: list[Path]) -> list[dict[str, Any]]:
    """Name-only discovery in explicitly supplied trees; filenames do not establish release."""
    inventories = []
    for root in roots:
        paths = sorted(
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
            if path.is_file() and "hyde" in path.name.casefold()
        )
        inventories.append(
            {
                "searched_root_name": root.name,
                "filename_matches": paths,
                "confirmed_hyde_35_asset_count": None,
                "note": "Name matches may include documentation; absent matches are limited to this search tree and do not prove absence elsewhere.",
            }
        )
    return inventories
