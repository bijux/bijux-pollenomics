"""Capability support, materialization, and evidence bytes stay distinct."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.capability_evidence import derive


@pytest.fixture
def documents(tmp_path: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    (tmp_path / "data").mkdir()
    (tmp_path / "data/a.json").write_text('{"source":"a"}\n')
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/b.json").write_text('{"source":"b"}\n')
    dimensions = ["site_identity", "numeric_chronology"]
    contract = {
        "capability_contract": {
            "schema_version": "source-capability-contract.v1",
            "source_count": 2,
            "dimension_count": 2,
            "dimensions": dimensions,
            "sources": [
                {
                    "source_key": "a",
                    "support_by_dimension": {
                        "site_identity": "supported",
                        "numeric_chronology": "unsupported",
                    },
                    "evidence_paths_by_dimension": {
                        "site_identity": ["data/a.json"],
                        "numeric_chronology": [],
                    },
                },
                {
                    "source_key": "b",
                    "support_by_dimension": {
                        "site_identity": "partial",
                        "numeric_chronology": "partial",
                    },
                    "evidence_paths_by_dimension": {
                        "site_identity": ["docs/b.json", "docs/missing.json"],
                        "numeric_chronology": ["docs/missing.json"],
                    },
                },
            ],
        }
    }

    def row(
        source: str,
        dimension: str,
        support: str,
        materialization: str,
        paths: list[str],
        present: list[str],
    ) -> dict[str, Any]:
        return {
            "source_key": source,
            "dimension": dimension,
            "support": support,
            "materialization": materialization,
            "evidence_paths": paths,
            "present_evidence_paths": present,
            "missing_evidence_paths": [name for name in paths if name not in present],
            "evidence_file_count": len(present),
            "required_evidence_count": len(paths),
            "coverage_metrics": {"records": None if support == "unsupported" else 1},
            "reason_codes": [],
            "human_review_required": support != "unsupported",
        }

    stage = {
        "capability_materialization_audit": {
            "schema_version": "source-capability-materialization-audit.v1",
            "source_count": 2,
            "dimension_count": 2,
            "row_count": 4,
            "rows": [
                row(
                    "a",
                    "site_identity",
                    "supported",
                    "complete",
                    ["data/a.json"],
                    ["data/a.json"],
                ),
                row("a", "numeric_chronology", "unsupported", "not_applicable", [], []),
                row(
                    "b",
                    "site_identity",
                    "partial",
                    "partial",
                    ["docs/b.json", "docs/missing.json"],
                    ["docs/b.json"],
                ),
                row(
                    "b",
                    "numeric_chronology",
                    "partial",
                    "missing",
                    ["docs/missing.json"],
                    [],
                ),
            ],
        }
    }
    return tmp_path, contract, stage


def test_separate_support_and_materialization(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = documents
    report = derive(root, contract, stage)
    assert report["source_count"] == 2
    assert report["audit_row_count"] == 4
    assert report["evidence_path_count"] == 2
    assert report["missing_evidence_path_count"] == 1
    assert report["human_review_required_row_count"] == 3
    assert report["support_counts"] == {"partial": 2, "supported": 1, "unsupported": 1}
    assert report["materialization_counts"] == {
        "complete": 1,
        "missing": 1,
        "not_applicable": 1,
        "partial": 1,
    }
    assert all("sha256" in row for row in report["evidence_paths"])


def test_missing_evidence_cannot_be_reported_present(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = deepcopy(documents)
    stage["capability_materialization_audit"]["rows"][2][
        "present_evidence_paths"
    ].append("docs/missing.json")
    with pytest.raises(ValueError, match="materialization differs"):
        derive(root, contract, stage)


def test_source_support_cannot_be_promoted_by_audit(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = deepcopy(documents)
    stage["capability_materialization_audit"]["rows"][3]["support"] = "supported"
    with pytest.raises(ValueError, match="support/evidence differs"):
        derive(root, contract, stage)


def test_invalid_coverage_metric_refuses(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = deepcopy(documents)
    stage["capability_materialization_audit"]["rows"][0]["coverage_metrics"][
        "records"
    ] = -1
    with pytest.raises(ValueError, match="coverage metric invalid"):
        derive(root, contract, stage)


def test_evidence_path_escape_refuses(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = deepcopy(documents)
    contract["capability_contract"]["sources"][0]["evidence_paths_by_dimension"][
        "site_identity"
    ] = ["data/../outside.json"]
    stage["capability_materialization_audit"]["rows"][0]["evidence_paths"] = [
        "data/../outside.json"
    ]
    with pytest.raises(ValueError, match="Unsafe capability evidence path"):
        derive(root, contract, stage)


def test_symlink_evidence_path_escape_refuses(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
) -> None:
    root, contract, stage = documents
    outside = tmp_path.parent / "outside-capability.json"
    outside.write_text("{}\n")
    (root / "data/a.json").unlink()
    (root / "data/a.json").symlink_to(outside)
    with pytest.raises(ValueError, match="Unsafe capability evidence path"):
        derive(root, contract, stage)
