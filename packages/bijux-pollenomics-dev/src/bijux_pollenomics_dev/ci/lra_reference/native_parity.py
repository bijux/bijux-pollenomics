"""Join independent native case preparation to same-revision live R evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from typing import Any

from .contracts import ReferenceRefusal, read_json
from .evidence import EXTENDED_CASE_IDS, validate_bundle


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _manifest(root: Path) -> tuple[bytes, list[dict[str, Any]]]:
    data = (root / "case_manifest.json").read_bytes()
    rows = read_json(data)
    if (
        not isinstance(rows, list)
        or len(rows) != 43
        or any(not isinstance(row, dict) for row in rows)
    ):
        raise ReferenceRefusal("Native/live case inventory must contain 43 records")
    if {row.get("id") for row in rows} != EXTENDED_CASE_IDS:
        raise ReferenceRefusal("Native/live case identifiers differ from the oracle")
    if any(
        not isinstance(row.get(field), str)
        or re.fullmatch(r"[0-9a-f]{64}", row[field]) is None
        for row in rows
        for field in ("input_sha256", "python_expected_sha256")
    ):
        raise ReferenceRefusal("Per-case input or Python expectation digest is missing")
    return data, rows


def verify_native_parity(
    *,
    native: Path,
    live: Path,
    lock: Path,
    target_sha: str,
    output: Path,
) -> dict[str, Any]:
    """Require equal cases and a complete actual-R certificate before passing."""
    if output.exists():
        raise ReferenceRefusal("Parity receipt destination must be absent")
    native_report = read_json((native / "report.json").read_bytes())
    if not isinstance(native_report, dict) or any(
        native_report.get(key) != value
        for key, value in {
            "status": "prepared_not_executed",
            "live_R_executed": False,
            "prepared_cases": 43,
            "passed_cases": 0,
        }.items()
    ):
        raise ReferenceRefusal("Separate native preparation is missing or mislabelled")
    native_bytes, native_rows = _manifest(native)
    live_bytes, _ = _manifest(live / "oracle")
    if native_bytes != live_bytes:
        raise ReferenceRefusal("Native and live-R case inventory/input digests differ")
    lock_hash = _sha(lock.read_bytes())
    certificate = validate_bundle(
        live, target_sha=target_sha, expected_lock_sha256=lock_hash
    )
    live_report = read_json((live / "oracle/report.json").read_bytes())
    if (
        live_report.get("prepared_cases") != 43
        or native_report.get("source_archive_sha256")
        != live_report.get("source_archive_sha256")
        or certificate.get("committed_source") is not True
    ):
        raise ReferenceRefusal("Native preparation and committed live-R source differ")
    receipt = {
        "schema_version": "lra-native-live-r-parity-gate.v1",
        "status": "passed",
        "target_sha": target_sha,
        "case_count": len(native_rows),
        "case_ids": [row["id"] for row in native_rows],
        "case_manifest_sha256": _sha(native_bytes),
        "case_input_sha256": {row["id"]: row["input_sha256"] for row in native_rows},
        "python_expected_sha256": {
            row["id"]: row["python_expected_sha256"] for row in native_rows
        },
        "source_lock_sha256": lock_hash,
        "live_r_certificate_sha256": _sha((live / "certificate.json").read_bytes()),
        "live_R_executed": True,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--live", type=Path, required=True)
    parser.add_argument("--lock", type=Path, required=True)
    parser.add_argument("--target-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        verify_native_parity(
            native=args.native,
            live=args.live,
            lock=args.lock,
            target_sha=args.target_sha,
            output=args.output,
        )
    except (OSError, ValueError) as error:
        parser.exit(2, "Native/live R parity refused: " + str(error) + "\n")


if __name__ == "__main__":
    main()
