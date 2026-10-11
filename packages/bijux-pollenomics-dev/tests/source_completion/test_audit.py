from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.audit import (
    build_source_audit,
    summarize_source_audit,
)
from bijux_pollenomics_dev.source_completion.evidence import (
    EvidenceReader,
    indexed_rows,
)
from bijux_pollenomics_dev.source_completion.manifests import audit_neotoma, audit_sead


def write_json(root: Path, path: str, value: object) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    write_json(
        tmp_path,
        "data/source_family_contracts.json",
        {
            "rows": [
                {
                    "source_key": "pollen",
                    "display_name": "Pollen",
                    "domain_group": "pollen_context",
                    "evidence_role": "primary_context",
                    "layer_contracts": {
                        "raw": {
                            "repository_path": "data/pollen/raw",
                            "example_artifacts": ["data/pollen/raw/input.json"],
                        }
                    },
                }
            ]
        },
    )
    write_json(tmp_path, "data/pollen/raw/input.json", {"rows": []})
    write_json(
        tmp_path,
        "data/source_family_evidence_stage_matrix.json",
        {
            "rows": [
                {
                    "source_key": "pollen",
                    "raw_status": "present",
                    "normalized_status": "missing",
                    "reviewed_status": "missing",
                    "published_status": "missing",
                    "authority_status": "refused",
                }
            ],
            "capability_materialization_audit": {
                "rows": [
                    {
                        "source_key": "pollen",
                        "dimension": "taxa",
                        "support": "supported",
                        "materialization": "complete",
                        "human_review_required": True,
                        "evidence_paths": [],
                    }
                ]
            },
        },
    )
    write_json(
        tmp_path,
        "data/country_dimension_coverage.json",
        {
            "cell_count": 4,
            "cells": [
                {
                    "source_family": "pollen",
                    "country_code": code,
                    "country_dimension": "source_reported",
                    "availability_status": "not_queried",
                    "counts": {"observations": None},
                }
                for code in ("SE", "DK", "NO", "FI")
            ],
        },
    )
    for name in (
        "source_fact_ownership_registry",
        "source_spatiotemporal_posture_registry",
    ):
        write_json(tmp_path, f"data/{name}.json", {"rows": []})
    return tmp_path


def test_file_presence_never_upgrades_refused_semantics(repository: Path) -> None:
    result = build_source_audit(repository)
    assert result["accounting_checks_pass"] is True
    assert result["full_source_confirmation"] is False
    row = result["source_rows"][0]
    assert (
        row["materialization_layers"][0]["contract_examples"][0]["presence"]
        == "present"
    )
    assert row["source_stage_record"]["authority_status"] == "refused"
    assert row["qualified_review_dimensions"] == ["taxa"]
    assert row["country_availability_records"][0]["counts"]["observations"] is None


def test_compact_summary_retains_refusal_and_content_identity(repository: Path) -> None:
    full = build_source_audit(repository)
    summary = summarize_source_audit(full)
    assert summary["full_audit_sha256"] == full["audit_sha256"]
    assert summary["input_closure_sha256"] == full["input_closure_sha256"]
    assert summary["source_rows"][0]["authority_status"] == "refused"
    assert summary["source_rows"][0]["nordic_publication_availability"] == {}
    assert summary["full_source_confirmation"] is False


def test_changed_source_invalidates_content_address(repository: Path) -> None:
    first = build_source_audit(repository)
    assert first == build_source_audit(repository)
    write_json(repository, "data/pollen/raw/input.json", {"rows": [1]})
    changed = build_source_audit(repository)
    assert changed["input_closure_sha256"] != first["input_closure_sha256"]
    assert changed["audit_sha256"] != first["audit_sha256"]


def test_capability_presence_drift_is_a_failed_accounting_check(
    repository: Path,
) -> None:
    path = repository / "data/source_family_evidence_stage_matrix.json"
    payload = json.loads(path.read_text())
    capability = payload["capability_materialization_audit"]["rows"][0]
    capability["evidence_paths"] = ["data/pollen/raw/gone.json"]
    capability["present_evidence_paths"] = ["data/pollen/raw/gone.json"]
    path.write_text(json.dumps(payload))
    result = build_source_audit(repository)
    assert result["accounting_checks_pass"] is False
    assert (
        result["accounting_findings"][0]["reason_code"]
        == "capability_evidence_presence_drift"
    )


def test_missing_country_is_visible_without_fabricating_zero(repository: Path) -> None:
    path = repository / "data/country_dimension_coverage.json"
    payload = json.loads(path.read_text())
    payload["cells"].pop()
    payload["cell_count"] -= 1
    path.write_text(json.dumps(payload))
    result = build_source_audit(repository)
    assert result["accounting_checks_pass"] is False
    assert result["accounting_findings"][0]["country_codes"] == ["FI"]


def test_duplicate_registry_id_is_refused() -> None:
    with pytest.raises(ValueError, match="Duplicate"):
        indexed_rows({"rows": [{"id": 1}, {"id": 1}]}, "id")


def test_paths_cannot_escape_repository(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes"):
        EvidenceReader(tmp_path).read_bytes("../secret.json")


def test_read_set_detects_mid_audit_change(tmp_path: Path) -> None:
    write_json(tmp_path, "a.json", {"a": 1})
    reader = EvidenceReader(tmp_path)
    reader.json("a.json")
    write_json(tmp_path, "a.json", {"a": 2})
    with pytest.raises(ValueError, match="changed during"):
        reader.json("a.json")


def test_read_set_detects_mid_audit_disappearance(tmp_path: Path) -> None:
    write_json(tmp_path, "a.json", {"a": 1})
    reader = EvidenceReader(tmp_path)
    reader.json("a.json")
    (tmp_path / "a.json").unlink()
    with pytest.raises(ValueError, match="changed during"):
        reader.json("a.json")


def test_missing_neotoma_raw_manifest_is_an_accounting_error(tmp_path: Path) -> None:
    write_json(
        tmp_path,
        "data/neotoma/relational/manifest.json",
        {
            "source_snapshot_id": "pinned",
            "surfaces": {},
        },
    )
    reader = EvidenceReader(tmp_path)
    audit_neotoma(reader)
    assert reader.issues[0]["reason_code"] == "raw_download_manifest_missing"


def test_missing_sead_raw_and_native_index_are_accounting_errors(
    tmp_path: Path,
) -> None:
    path = "data/sead/normalized/acquisitions/pinned/evidence_materialization_manifest.json"
    write_json(
        tmp_path,
        path,
        {
            "files": [],
            "eligible_event_count": 0,
            "refused_event_count": 1,
            "observation_count": 1,
        },
    )
    reader = EvidenceReader(tmp_path)
    audit_sead(reader, path)
    assert {row["reason_code"] for row in reader.issues} == {
        "sead_acquisition_manifest_missing",
        "sead_native_observation_index_missing",
    }


def test_missing_historical_manifest_digest_is_explicit(tmp_path: Path) -> None:
    write_json(tmp_path, "a.json", {"a": 1})
    reader = EvidenceReader(tmp_path)
    reader.verify("a.json", {})
    assert reader.verifications["a.json"]["manifest_digest_available"] is False
    assert reader.verifications["a.json"]["observed_sha256"]
    assert reader.json("a.json") == {"a": 1}


def test_neotoma_missing_parts_and_id_disagreement_are_not_count_success(
    tmp_path: Path,
) -> None:
    path = "data/neotoma/relational/manifest.json"
    write_json(
        tmp_path,
        path,
        {
            "source_snapshot_id": "pinned",
            "surfaces": {
                "datasets": {
                    "id_field": "dataset_id",
                    "row_count": 1,
                    "part_count": 1,
                    "parts": [{"path": "missing.json", "row_count": 1}],
                }
            },
        },
    )
    write_json(
        tmp_path,
        "data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json",
        {
            "requested_dataset_count": 1,
            "requested_dataset_ids": [1],
            "downloaded_dataset_count": 1,
            "downloaded_dataset_ids": [1],
        },
    )
    reader = EvidenceReader(tmp_path)
    result = audit_neotoma(reader)
    assert result["requests"]["downloaded_not_normalized"] == [1]
    assert result["surfaces"][0]["observed_row_count"] == 0
    assert {issue["reason_code"] for issue in reader.issues} == {
        "manifest_file_missing",
        "relational_surface_count_mismatch",
        "dataset_request_identity_mismatch",
    }


def test_neotoma_duplicate_identity_survives_as_error(tmp_path: Path) -> None:
    base = "data/neotoma/relational/"
    write_json(
        tmp_path,
        base + "manifest.json",
        {
            "source_snapshot_id": "pinned",
            "surfaces": {
                "datasets": {
                    "id_field": "dataset_id",
                    "row_count": 2,
                    "part_count": 1,
                    "parts": [{"path": "part.json", "row_count": 2}],
                }
            },
        },
    )
    write_json(
        tmp_path,
        base + "part.json",
        {
            "row_count": 2,
            "rows": [
                {"dataset_id": "dataset:1", "source_dataset_id": 1},
                {"dataset_id": "dataset:1", "source_dataset_id": 1},
            ],
        },
    )
    reader = EvidenceReader(tmp_path)
    result = audit_neotoma(reader)
    assert result["surfaces"][0]["distinct_identity_count"] == 1
    assert result["surfaces"][0]["duplicate_ids"] == ["dataset:1"]
    assert reader.issues[0]["reason_code"] == "relational_duplicate_identity"


def test_manifest_wrong_hash_is_reported(tmp_path: Path) -> None:
    write_json(tmp_path, "part.json", {"rows": []})
    reader = EvidenceReader(tmp_path)
    reader.verify("part.json", {"sha256": "0" * 64, "byte_count": 1})
    assert len(reader.issues) == 2
    assert {row["field"] for row in reader.issues} == {"sha256", "byte_count"}
