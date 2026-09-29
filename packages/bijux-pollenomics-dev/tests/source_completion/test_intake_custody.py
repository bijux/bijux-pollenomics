from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.intake_custody import (
    build_intake_custody_report,
)


def _write(path: Path, content: bytes) -> dict[str, object]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


def _json(path: Path, value: dict[str, object]) -> dict[str, object]:
    return _write(path, (json.dumps(value, sort_keys=True) + "\n").encode())


def _sources(tmp_path: Path) -> tuple[Path, Path]:
    repository = tmp_path / "repository"
    private = tmp_path / "private"
    receipts = []
    archives = []
    for name, disposition, archive_bytes in (
        ("OPENLAND-001", "pending", None),
        ("OPENLAND-002", "adapt", b"private modeled source"),
        ("ROOTSI-001", "review", b"private pollen candidates"),
    ):
        ident = f"EXT-2026-09-04-{name}"
        archive = None
        if archive_bytes is not None:
            relative = f"original/{name}.zip"
            archive = {
                "intake_id": ident,
                "relative_path": relative,
                **_write(private / relative, archive_bytes),
            }
            archives.append(archive)
        payload: dict[str, object] = {
            "intake_id": ident,
            "lifecycle_state": "pending_delivery" if archive is None else "quarantined",
            "delivery": {
                "materialization_status": "unavailable"
                if archive is None
                else "received",
                "sha256": None if archive is None else archive["sha256"],
                "byte_size": None if archive is None else archive["bytes"],
            },
            "decision": {"disposition": disposition, "public_release_allowed": False},
            "rights": {"status": "unknown"},
            "country_coverage": [
                {"country_code": country, "content_state": "not_admitted"}
                for country in ("SE", "DK", "NO", "FI")
            ],
        }
        path = f"{ident}.json"
        receipts.append(
            {
                "intake_id": ident,
                "path": path,
                **_json(private / "source-intakes/receipts" / path, payload),
            }
        )
    _json(
        private / "source-intakes/custody.json",
        {
            "schema_version": "source-intake-custody.v1",
            "receipts": receipts,
            "archives": archives,
        },
    )
    _json(
        private / "landclim/rootsi-workbooks/manifest.json",
        {"archive_sha256": archives[1]["sha256"]},
    )
    _json(
        repository / "docs/report/source-relations/openland-intake/report.json",
        {
            "source_archive": {"sha256": archives[0]["sha256"]},
            "independent_vegetation_benchmarks": 0,
            "rights": {"public_map_or_export_authorized": False},
        },
    )
    _json(
        repository / "docs/report/source-relations/rootsi-landclim-overlap/report.json",
        {"admission": {"sample_chronology_admitted": False}},
    )
    return repository, private


def test_original_bytes_do_not_upgrade_historical_rights(tmp_path: Path) -> None:
    repository, private = _sources(tmp_path)
    report = build_intake_custody_report(repository, private)
    assert report["verified_original_archives"] == 2
    assert report["country_claim_rows"] == 12
    assert report["scientific_admission"] == "not_established_by_custody"
    assert all(
        row["historical_public_release_allowed"] is False
        and row["scientific_admission_from_custody"] is False
        for row in report["historical_receipts"]
    )


def test_changed_archive_refuses_the_custody_report(tmp_path: Path) -> None:
    repository, private = _sources(tmp_path)
    (private / "original/ROOTSI-001.zip").write_bytes(b"changed")
    with pytest.raises(ValueError, match="identity changed"):
        build_intake_custody_report(repository, private)
