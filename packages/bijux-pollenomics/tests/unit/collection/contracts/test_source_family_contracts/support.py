from __future__ import annotations

import hashlib
import json
from pathlib import Path

from bijux_pollenomics.collection.contracts.capabilities import (
    SEAD_ADMITTED_ACQUISITION_ADMISSION,
)
from bijux_pollenomics.collection.sources.sead.acquisition.archive import (
    SEAD_FULL_EVIDENCE_SOURCE_TABLES,
)

from tests.support.repository import REPOSITORY_ROOT

REPO_ROOT = REPOSITORY_ROOT


def _write_full_sead_admission_fixture(
    output_root: Path, payload_bytes: bytes
) -> tuple[Path, Path]:
    admission_path = output_root / SEAD_ADMITTED_ACQUISITION_ADMISSION.removeprefix(
        "data/"
    )
    acquisition_root = admission_path.parent
    payload_path = acquisition_root / "payloads/tbl_sites.json"
    payload_path.parent.mkdir(parents=True)
    payload_path.write_bytes(payload_bytes)
    manifest_path = acquisition_root / "manifest.json"
    manifest_path.write_bytes(b'#{"acquisition":"fixture"}')
    expected_paths = {
        "country-decisions.json",
        "manifest.json",
        "parent-admission.json",
        "reconciliation/countries.json",
        "reconciliation/joins.json",
        *(f"payloads/{table}.json" for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES),
        *(f"receipts/{table}.json" for table in SEAD_FULL_EVIDENCE_SOURCE_TABLES),
    }
    copied_files = [
        {"path": path, "byte_count": 0, "sha256": "0" * 64}
        for path in sorted(expected_paths)
    ]
    for record in copied_files:
        if record["path"] == "manifest.json":
            record["byte_count"] = manifest_path.stat().st_size
            record["sha256"] = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
        elif record["path"] == "payloads/tbl_sites.json":
            record["byte_count"] = len(payload_bytes)
            record["sha256"] = hashlib.sha256(payload_bytes).hexdigest()
    admission_path.write_text(
        json.dumps(
            {
                "schema_version": "sead-acquisition-admission.v1",
                "source_family": "sead",
                "run_id": acquisition_root.name,
                "acquisition_manifest_sha256": hashlib.sha256(
                    manifest_path.read_bytes()
                ).hexdigest(),
                "declared_scope": {
                    "scope_key": "full_evidence_relations",
                    "status": "complete_for_declared_relations",
                    "table_count": 61,
                    "join_count": 86,
                    "tables": list(SEAD_FULL_EVIDENCE_SOURCE_TABLES),
                    "wp01_complete": False,
                },
                "release_status": "refused",
                "copied_files": copied_files,
            }
        ),
        encoding="utf-8",
    )
    return admission_path, payload_path
