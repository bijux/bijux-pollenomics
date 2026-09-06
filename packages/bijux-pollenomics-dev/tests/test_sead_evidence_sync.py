"""Tests for manifest-driven public SEAD evidence synchronization."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.docs.sead_evidence_sync import (
    DEFAULT_TARGETS,
    END_MARKER,
    START_MARKER,
    SeadEvidenceSyncError,
    load_sead_evidence_facts,
    render_sead_evidence_block,
    synchronize_sead_evidence,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _fixture_repository(root: Path) -> None:
    run_id = "sead-test-run"
    build_id = "sha256:test-build"
    evidence_root = root / "data/sead/normalized/acquisitions" / run_id
    raw_root = root / "data/sead/raw/acquisitions" / run_id
    _write_json(
        root / "data/source_fact_ownership_registry.json",
        {
            "schema_version": "source-fact-ownership-registry.v1",
            "row_count": 1,
            "rows": [
                {
                    "fact_key": "sead_archaeology_context",
                    "governing_surface_path": str(
                        evidence_root.relative_to(root)
                        / "evidence_materialization_manifest.json"
                    ),
                }
            ],
        },
    )
    _write_json(
        evidence_root / "evidence_materialization_manifest.json",
        {
            "source_run_id": run_id,
            "build_id": build_id,
            "source_table_count": 61,
            "chronology_claim_count": 9,
            "observation_count": 8,
            "eligible_event_count": 0,
            "refused_event_count": 8,
        },
    )
    _write_json(
        raw_root / "admission.json",
        {
            "run_id": run_id,
            "build_id": build_id,
            "table_counts": {f"table_{index}": 0 for index in range(61)},
            "country_accounting": {
                "bbox_site_count": 12,
                "admitted_site_count": 10,
                "review_site_count": 1,
                "unassigned_site_count": 1,
                "country_counts": {"SE": 4, "DK": 3, "NO": 2, "FI": 1},
            },
        },
    )
    _write_json(
        evidence_root / "chronology_claims.json",
        {
            "source_run_id": run_id,
            "source_build_id": build_id,
            "claim_count": 9,
            "comparability_counts": {
                "comparable": 4,
                "context_only": 3,
                "unresolved": 2,
            },
        },
    )
    _write_json(
        evidence_root / "source_native_observations.json",
        {"source_run_id": run_id, "build_id": build_id, "observation_count": 8},
    )
    _write_json(
        evidence_root / "observation_relation_index.json",
        {
            "source_run_id": run_id,
            "build_id": build_id,
            "taxon_relation_count": 6,
            "dimension_relation_count": 5,
        },
    )
    _write_json(
        evidence_root / "evidence_events.json",
        {
            "source_run_id": run_id,
            "observation_denominator": 8,
            "eligible_event_count": 0,
            "refused_event_count": 8,
            "refusal_reason_counts": {"source_classification_not_accepted": 8},
        },
    )
    _write_json(
        root / "docs/report/regions/nordic/nordic_map_publication_contract.json",
        {
            "detail_projection": {
                "sources": {
                    "sead": {
                        "source_run_id": run_id,
                        "build_id": build_id,
                        "source_feature_count": 17,
                        "assigned_site_count": 10,
                        "source_claim_denominator": 9,
                        "source_observation_denominator": 8,
                        "source_event_refusal_denominator": 8,
                        "country_site_counts": {
                            "Sweden": 4,
                            "Denmark": 3,
                            "Norway": 2,
                            "Finland": 1,
                        },
                        "propagation_status": "refused",
                        "propagation_reason_code": "source_classification_not_accepted",
                    }
                }
            }
        },
    )
    for target in DEFAULT_TARGETS:
        path = root / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"before\n{START_MARKER}\nstale\n{END_MARKER}\nafter\n", encoding="utf-8"
        )


def test_live_public_sead_evidence_blocks_match_governed_artifacts() -> None:
    facts = load_sead_evidence_facts(REPOSITORY_ROOT)
    expected = render_sead_evidence_block(facts)
    for relative in DEFAULT_TARGETS:
        assert expected in (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")


def test_public_sead_claims_reject_superseded_snapshot_denominators() -> None:
    superseded = (
        "2,172",
        "27,002",
        "26,556",
        "9,380",
        "10,379",
        "9,149",
        "1,230",
        "2,007",
        "1,267",
        "1,268",
    )
    for path in sorted((REPOSITORY_ROOT / "docs/public").rglob("*.md")):
        paragraphs = path.read_text(encoding="utf-8").split("\n\n")
        for paragraph in paragraphs:
            if "SEAD" not in paragraph and "sead" not in paragraph:
                continue
            for obsolete in superseded:
                assert obsolete not in paragraph, (
                    f"{path.relative_to(REPOSITORY_ROOT)} contains obsolete "
                    f"SEAD denominator {obsolete}"
                )


def test_sync_replaces_only_governed_blocks_and_then_reaches_fixed_point(
    tmp_path: Path,
) -> None:
    _fixture_repository(tmp_path)
    assert synchronize_sead_evidence(tmp_path, check=False) == DEFAULT_TARGETS
    assert synchronize_sead_evidence(tmp_path, check=True) == ()
    for relative in DEFAULT_TARGETS:
        text = (tmp_path / relative).read_text(encoding="utf-8")
        assert text.startswith("before\n")
        assert text.endswith("\nafter\n")
        assert "| source tables | 61 |" in text
        assert "| assigned four-country sites | 10 | SE 4, DK 3, NO 2, FI 1 |" in text
        assert "| eligible / refused propagation events | 0 / 8 |" in text


def test_check_rejects_stale_blocks(tmp_path: Path) -> None:
    _fixture_repository(tmp_path)
    with pytest.raises(SeadEvidenceSyncError, match="blocks are stale"):
        synchronize_sead_evidence(tmp_path, check=True)


def test_identity_drift_fails_closed(tmp_path: Path) -> None:
    _fixture_repository(tmp_path)
    contract_path = (
        tmp_path / "docs/report/regions/nordic/nordic_map_publication_contract.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["detail_projection"]["sources"]["sead"]["build_id"] = "sha256:other"
    _write_json(contract_path, contract)
    with pytest.raises(SeadEvidenceSyncError, match="identities diverge"):
        load_sead_evidence_facts(tmp_path)


def test_denominator_drift_fails_closed(tmp_path: Path) -> None:
    _fixture_repository(tmp_path)
    chronology_path = (
        tmp_path
        / "data/sead/normalized/acquisitions/sead-test-run/chronology_claims.json"
    )
    chronology = json.loads(chronology_path.read_text(encoding="utf-8"))
    chronology["comparability_counts"]["unresolved"] = 3
    _write_json(chronology_path, chronology)
    with pytest.raises(SeadEvidenceSyncError, match="comparability does not reconcile"):
        load_sead_evidence_facts(tmp_path)
