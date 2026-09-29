"""Verify private intake custody without promoting historical source decisions."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

INTAKE_IDS = {
    "EXT-2026-09-04-OPENLAND-001",
    "EXT-2026-09-04-OPENLAND-002",
    "EXT-2026-09-04-ROOTSI-001",
}
COUNTRIES = {"SE", "DK", "NO", "FI"}
CURRENT_REPORTS = {
    "EXT-2026-09-04-OPENLAND-002": (
        "docs/report/source-relations/openland-intake/report.json"
    ),
    "EXT-2026-09-04-ROOTSI-001": (
        "docs/report/source-relations/rootsi-landclim-overlap/report.json"
    ),
}


def _verified_path(root: Path, relative: str, expected: dict[str, Any]) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Missing or escaping intake evidence: {relative}")
    if path.stat().st_size != expected["bytes"]:
        raise ValueError(f"Intake evidence identity changed: {relative}")
    with path.open("rb") as stream:
        observed = hashlib.file_digest(stream, "sha256").hexdigest()
    if observed != expected["sha256"]:
        raise ValueError(f"Intake evidence identity changed: {relative}")
    return path


def _json_object(content: bytes, label: str) -> dict[str, Any]:
    payload = json.loads(content)
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {label}")
    return payload


def build_intake_custody_report(
    repository: Path, private_source_root: Path
) -> dict[str, Any]:
    """Reconcile historical receipts with private bytes and current source reports."""
    root = private_source_root.resolve()
    custody_path = root / "source-intakes/custody.json"
    custody_bytes = custody_path.read_bytes()
    custody = _json_object(custody_bytes, str(custody_path))
    if custody.get("schema_version") != "source-intake-custody.v1":
        raise ValueError("Unexpected intake custody schema")
    receipt_specs = custody.get("receipts")
    archive_specs = custody.get("archives")
    if not isinstance(receipt_specs, list) or not isinstance(archive_specs, list):
        raise ValueError("Incomplete intake custody inventory")
    if {row["intake_id"] for row in receipt_specs} != INTAKE_IDS:
        raise ValueError("Intake receipt identities are incomplete or changed")
    if len(receipt_specs) != len(INTAKE_IDS):
        raise ValueError("Duplicate intake receipt identity")
    expected_archive_ids = INTAKE_IDS - {"EXT-2026-09-04-OPENLAND-001"}
    if {row["intake_id"] for row in archive_specs} != expected_archive_ids or len(
        archive_specs
    ) != len(expected_archive_ids):
        raise ValueError("Materialized intake archive identities changed")

    archives = {row["intake_id"]: row for row in archive_specs}
    rows = []
    for record in sorted(receipt_specs, key=lambda row: row["intake_id"]):
        ident = record["intake_id"]
        receipt = _json_object(
            _verified_path(
                root / "source-intakes/receipts", record["path"], record
            ).read_bytes(),
            ident,
        )
        if receipt.get("intake_id") != ident:
            raise ValueError(f"Receipt identity changed: {ident}")
        coverage = receipt.get("country_coverage")
        if (
            not isinstance(coverage, list)
            or {row["country_code"] for row in coverage} != COUNTRIES
            or len(coverage) != len(COUNTRIES)
        ):
            raise ValueError(f"Four-country receipt coverage changed: {ident}")
        delivery = receipt["delivery"]
        if receipt["decision"]["public_release_allowed"] is not False:
            raise ValueError(f"Historical public release decision changed: {ident}")
        archive = archives.get(ident)
        observed_archive: dict[str, Any] | None = None
        if archive is None:
            if (
                delivery.get("materialization_status") != "unavailable"
                or delivery.get("sha256") is not None
                or delivery.get("byte_size") is not None
            ):
                raise ValueError(f"Unmaterialized receipt has archive claims: {ident}")
        else:
            if (
                delivery.get("materialization_status") != "received"
                or delivery.get("sha256") != archive["sha256"]
                or delivery.get("byte_size") != archive["bytes"]
            ):
                raise ValueError(f"Archive and receipt disagree: {ident}")
            _verified_path(root, archive["relative_path"], archive)
            observed_archive = {
                "relative_private_path": archive["relative_path"],
                "bytes": archive["bytes"],
                "sha256": archive["sha256"],
                "verification": "byte_and_sha256_match",
            }
        rows.append(
            {
                "intake_id": ident,
                "receipt_sha256": record["sha256"],
                "historical_lifecycle_state": receipt["lifecycle_state"],
                "historical_delivery_state": delivery["materialization_status"],
                "historical_disposition": receipt["decision"]["disposition"],
                "historical_rights_status": receipt["rights"]["status"],
                "historical_public_release_allowed": receipt["decision"][
                    "public_release_allowed"
                ],
                "historical_country_coverage": sorted(
                    coverage, key=lambda row: row["country_code"]
                ),
                "verified_original_archive": observed_archive,
                "current_source_report": CURRENT_REPORTS.get(ident),
                "scientific_admission_from_custody": False,
            }
        )

    repository = repository.resolve()
    current_inputs = []
    for ident, relative in sorted(CURRENT_REPORTS.items()):
        path = repository / relative
        content = path.read_bytes()
        report = _json_object(content, relative)
        if ident.endswith("OPENLAND-002"):
            if report["source_archive"]["sha256"] != archives[ident]["sha256"]:
                raise ValueError("Current OpenLand report uses a different archive")
            if (
                report["independent_vegetation_benchmarks"] != 0
                or report["rights"]["public_map_or_export_authorized"] is not False
            ):
                raise ValueError("OpenLand independent benchmark posture changed")
        else:
            workbook_manifest = root / "landclim/rootsi-workbooks/manifest.json"
            workbooks = _json_object(
                workbook_manifest.read_bytes(), str(workbook_manifest)
            )
            if workbooks["archive_sha256"] != archives[ident]["sha256"]:
                raise ValueError("Retained Rootsi workbooks use a different archive")
            if any(report["admission"].values()):
                raise ValueError("Rootsi admission posture changed")
        current_inputs.append(
            {
                "intake_id": ident,
                "path": relative,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return {
        "schema_version": "source-intake-custody-review.v1",
        "private_custody_manifest_sha256": hashlib.sha256(custody_bytes).hexdigest(),
        "receipt_count": len(rows),
        "verified_original_archives": len(archive_specs),
        "country_claim_rows": len(rows) * len(COUNTRIES),
        "historical_receipts": rows,
        "current_source_report_inputs": current_inputs,
        "scientific_admission": "not_established_by_custody",
        "scope": "Historical receipt and original archive verification; current source reports retain scientific authority.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--private-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build_intake_custody_report(args.repository, args.private_source_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(
        f"Verified {result['receipt_count']} receipts and {result['verified_original_archives']} archives"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
