"""Direct contracts for bounded artifact accounting and retention decisions."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.artifact_custody import inventory


def test_scan_counts_paths_and_unique_inodes_without_following_links(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.write_bytes(b"external-source")
    (root / "proof").write_bytes(b"evidence")
    os.link(root / "proof", root / "alias")
    (root / "link").symlink_to(outside)

    scan = inventory.scan_artifacts(root, selected_prefixes=("proof",))
    assert scan["complete"] is True
    assert scan["bytes"]["files"] == 2
    assert scan["bytes"]["entries"] == 3
    assert scan["symlink_count"] == 1
    assert scan["hardlink_path_count"] == 1
    assert scan["selected_prefixes"]["proof"]["apparent_bytes"] == 8
    assert scan["bytes"]["apparent_bytes"] > scan["unique_inode_apparent_bytes"]
    assert scan["symlink_examples"][0]["target"] == str(outside)


def test_cap_boundary_and_incomplete_scan_never_authorize_deletion() -> None:
    scan: dict[str, Any] = {
        "complete": True,
        "bytes": {
            "apparent_bytes": inventory.CAP_BYTES - inventory.OUTPUT_RESERVE_BYTES - 1
        },
    }
    below = inventory.cap_decision(scan)
    assert below["threshold_bytes"] == 800_000_000_000
    assert below["status"] == "observed_below_cap"
    assert below["deletion_authorized_by_this_report"] is False
    scan["bytes"]["apparent_bytes"] += 1
    boundary = inventory.cap_decision(scan)
    assert boundary["status"] == "at_or_above_reserved_cap_boundary"
    assert boundary["deletion_authorized_by_this_report"] is False
    scan["complete"] = False
    assert inventory.cap_decision(scan)["status"] == "indeterminate_incomplete_scan"


def test_reference_scan_records_exact_mentions_and_skipped_large_files(
    tmp_path: Path,
) -> None:
    report = tmp_path / "docs/report"
    report.mkdir(parents=True)
    (report / "index.md").write_text(
        "Proof: artifacts/jobs/oracle/receipt.json.\n"
        "Again: artifacts/jobs/oracle/receipt.json\n"
    )
    (report / "large.md").write_text("x" * 100)
    result = inventory.scan_references(tmp_path, max_file_bytes=99)
    assert result["references"] == {
        "artifacts/jobs/oracle/receipt.json": ["docs/report/index.md"]
    }
    assert result["skipped_large_files"] == 1
    assert result["complete"] is False


def test_exact_cache_candidate_has_receipt_but_no_deletion_authority(
    tmp_path: Path,
) -> None:
    root = tmp_path / "artifacts"
    cache = root / "jobs/linux-r-oracle/mypy-cache"
    cache.mkdir(parents=True)
    (cache / "meta.json").write_text("{}")
    log = root / "jobs/linux-r-oracle/terminal-checks.log"
    log.write_text("mypy --cache-dir artifacts/jobs/linux-r-oracle/mypy-cache\n")
    scan = inventory.scan_artifacts(root)
    candidates = inventory._candidates(root, scan, {})
    row = next(item for item in candidates if item["path"].endswith("mypy-cache"))
    assert row["classification"] == "exact_regenerable_cache_for_review"
    assert row["regeneration_command_recorded"] is True
    assert row["metadata"]["files"] == 1
    assert row["deletion_authorized"] is False
    assert row["inactive_independently_verified"] is False
    cited = {"artifacts/jobs/linux-r-oracle/mypy-cache/x": ["docs/report/x.md"]}
    assert (
        inventory._candidates(root, scan, cited)[0]["classification"]
        == "not_established"
    )


def test_entry_limit_refuses_complete_measurement(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    root.mkdir()
    for name in ("one", "two"):
        (root / name).write_bytes(b"a")
    scan = inventory.scan_artifacts(root, max_entries=1)
    assert scan["complete"] is False
    assert scan["limit_reason"] == "entry_limit"
    assert inventory.cap_decision(scan)["status"] == "indeterminate_incomplete_scan"


def test_native_cap_binding_checks_raw_units_and_independent_references(
    tmp_path: Path,
) -> None:
    repository = tmp_path / "repository"
    retained = repository / "artifacts/jobs/artifact-retention"
    retained.mkdir(parents=True)
    metadata = retained / "metadata-scan.json"
    metadata.write_text(
        json.dumps(
            {
                "requirement_id": "V3-26",
                "cap_decision": {"status": "indeterminate_incomplete_scan"},
                "reference_scan": {
                    "references": {
                        "artifacts/jobs/oracle": ["docs/report/oracle/README.md"],
                        "artifacts/jobs/oracle/receipt.json": [
                            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/artifact_custody/inventory.py"
                        ],
                    }
                },
                "selected_proofs": [
                    {"path": "artifacts/jobs/oracle/receipt.json", "role": "proof"}
                ],
            }
        )
    )
    stdout = retained / "native-du.stdout"
    stdout.write_text("100\tartifacts\n")
    (retained / "native-du.stderr").write_text("")
    receipt = retained / "native-du-receipt.json"
    receipt.write_text(
        json.dumps(
            {
                "command": [
                    "du",
                    "-A",
                    "-B",
                    "1",
                    "-l",
                    "-s",
                    str(repository / "artifacts"),
                ],
                "exit_code": 0,
                "threshold_bytes": inventory.CAP_BYTES,
                "display_unit_bytes": 512,
                "reported_512_byte_units": 100,
                "apparent_byte_upper_bound": 51_200,
                "apparent_byte_lower_bound": 50_689,
                "status": "observed_below_cap",
                "stdout_path": "artifacts/jobs/artifact-retention/native-du.stdout",
                "stderr_path": "artifacts/jobs/artifact-retention/native-du.stderr",
            }
        )
    )
    output = repository / "docs/report/maintenance/artifact-retention/report.json"
    report = inventory.bind_native_cap_check(
        repository, metadata, receipt, output, concurrent_artifact_writes_observed=True
    )
    assert report["cap_decision"]["status"] == "indeterminate_incomplete_scan"
    assert report["native_cap_check"]["status"] == "observed_below_cap_non_atomic"
    assert report["native_cap_check"]["apparent_byte_upper_bound"] == 51_200
    assert report["native_cap_check"]["concurrent_artifact_writes_observed"] is True
    assert report["selected_proofs"][0]["independent_reference_origins"] == [
        "docs/report/oracle/README.md"
    ]
    assert json.loads(output.read_text()) == report
    (retained / "native-du.stdout").write_text("101\tartifacts\n")
    with pytest.raises(ValueError, match="differs from raw stdout"):
        inventory.bind_native_cap_check(
            repository, metadata, receipt, retained / "bad-report.json"
        )
