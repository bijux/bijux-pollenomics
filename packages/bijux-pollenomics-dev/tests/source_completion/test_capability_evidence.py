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


def test_supported_dimension_cannot_hide_review_requirement(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = deepcopy(documents)
    stage["capability_materialization_audit"]["rows"][0]["human_review_required"] = (
        False
    )
    with pytest.raises(ValueError, match="review requirement differs"):
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


def _taxon_documents(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    root, contract, stage = deepcopy(documents)
    capability = contract["capability_contract"]
    capability["dimensions"][1] = "taxon_identity"
    for source in capability["sources"]:
        for field in ("support_by_dimension", "evidence_paths_by_dimension"):
            source[field]["taxon_identity"] = source[field].pop("numeric_chronology")
    for row in stage["capability_materialization_audit"]["rows"]:
        if row["dimension"] == "numeric_chronology":
            row["dimension"] = "taxon_identity"
    return root, contract, stage


@pytest.mark.parametrize("prior_reason", [False, True])
def test_source_without_taxa_reports_absence_without_inventing_taxonomy(
    documents: tuple[Path, dict[str, Any], dict[str, Any]], prior_reason: bool
) -> None:
    root, contract, stage = _taxon_documents(documents)
    broad_category = '{"source":"a","land_use_category":"Forest"}\n'
    (root / "data/a.json").write_text(broad_category)
    cell = stage["capability_materialization_audit"]["rows"][1]
    cell["reason_codes"] = ["source_dimension_unsupported"]
    if prior_reason:
        cell["reason_codes"].append("not_provided_by_source")
    original = deepcopy(stage)
    report = derive(root, contract, stage)
    absence = next(
        row
        for row in report["rows"]
        if row["source_key"] == "a" and row["dimension"] == "taxon_identity"
    )
    assert absence["reason_codes"] == [
        "source_dimension_unsupported",
        "not_provided_by_source",
    ]
    assert absence["support"] == "unsupported"
    assert absence["materialization"] == "not_applicable"
    assert absence["coverage_metrics"] == {"records": None}
    assert absence["present_evidence_paths"] == absence["missing_evidence_paths"] == []
    assert not absence["human_review_required"]
    assert stage == original
    assert (root / "data/a.json").read_text() == broad_category
    assert report["source_count"] == 2 and report["audit_row_count"] == 4
    assert report["support_counts"] == {"partial": 2, "supported": 1, "unsupported": 1}
    assert report["materialization_counts"] == {
        "complete": 1,
        "missing": 1,
        "not_applicable": 1,
        "partial": 1,
    }
    assert not {"accepted_taxon_concept_id", "source_taxon_id", "taxa"} & absence.keys()


@pytest.mark.parametrize("support", ["supported", "partial"])
def test_missing_taxon_files_do_not_report_source_absence(
    documents: tuple[Path, dict[str, Any], dict[str, Any]], support: str
) -> None:
    root, contract, stage = _taxon_documents(documents)
    contract["capability_contract"]["sources"][1]["support_by_dimension"][
        "taxon_identity"
    ] = support
    cell = stage["capability_materialization_audit"]["rows"][3]
    cell["support"] = support
    cell["coverage_metrics"] = {"records": None}
    cell["reason_codes"] = ["governed_dimension_evidence_missing"]
    report = derive(root, contract, stage)
    missing = next(
        row
        for row in report["rows"]
        if row["source_key"] == "b" and row["dimension"] == "taxon_identity"
    )
    assert missing["support"] == support
    assert missing["materialization"] == "missing"
    assert missing["coverage_metrics"] == {"records": None}
    assert missing["reason_codes"] == ["governed_dimension_evidence_missing"]
    assert missing["missing_evidence_paths"] == ["docs/missing.json"]
    assert missing["human_review_required"]


@pytest.mark.parametrize("support", ["supported", "partial"])
def test_taxon_source_absence_cannot_be_asserted_for_capable_source(
    documents: tuple[Path, dict[str, Any], dict[str, Any]], support: str
) -> None:
    root, contract, stage = _taxon_documents(documents)
    contract["capability_contract"]["sources"][1]["support_by_dimension"][
        "taxon_identity"
    ] = support
    cell = stage["capability_materialization_audit"]["rows"][3]
    cell["support"] = support
    cell["reason_codes"] = ["not_provided_by_source"]
    with pytest.raises(
        ValueError, match="Taxon absence contradicts declared source capability"
    ):
        derive(root, contract, stage)


def test_unsupported_non_taxon_dimension_keeps_its_own_reason(
    documents: tuple[Path, dict[str, Any], dict[str, Any]],
) -> None:
    root, contract, stage = documents
    stage["capability_materialization_audit"]["rows"][1]["reason_codes"] = [
        "source_dimension_unsupported"
    ]
    report = derive(root, contract, stage)
    numeric = next(
        row
        for row in report["rows"]
        if row["source_key"] == "a" and row["dimension"] == "numeric_chronology"
    )
    assert numeric["reason_codes"] == ["source_dimension_unsupported"]
