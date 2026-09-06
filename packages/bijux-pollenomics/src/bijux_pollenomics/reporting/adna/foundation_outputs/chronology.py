"""Animal foundation chronology responsibilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ....adna.projects.evidence.chronology import (
    ADNA_CHRONOLOGY_EVIDENCE_CLASSES,
    ADNA_CHRONOLOGY_NORMALIZATION_STATUSES,
    ADNA_CHRONOLOGY_PRECISION_POSTURES,
    ADNA_CHRONOLOGY_STRENGTHS,
    build_sample_chronology_provenance_rows,
    build_sample_chronology_review_rows,
)
from .repository import _load_json_if_present


def build_animal_sample_chronology_review(
    *,
    data_root: Path,
) -> dict[str, Any]:
    """Publish one reader-facing chronology review across all governed animal sample rows."""
    rows = list(build_sample_chronology_review_rows(data_root))
    provenance_rows = list(build_sample_chronology_provenance_rows(data_root))
    strength_counts = dict.fromkeys(ADNA_CHRONOLOGY_STRENGTHS, 0)
    evidence_counts = dict.fromkeys(ADNA_CHRONOLOGY_EVIDENCE_CLASSES, 0)
    precision_counts = dict.fromkeys(ADNA_CHRONOLOGY_PRECISION_POSTURES, 0)
    normalization_counts = dict.fromkeys(ADNA_CHRONOLOGY_NORMALIZATION_STATUSES, 0)
    comparability_counts: dict[str, int] = {}
    for row in rows:
        strength_counts[str(row.get("chronology_strength", ""))] += 1
        evidence_counts[str(row.get("chronology_evidence_class", ""))] += 1
        precision_counts[str(row.get("chronology_precision_posture", ""))] += 1
        normalization_counts[str(row.get("chronology_normalization_status", ""))] += 1
    for row in provenance_rows:
        posture = _temporal_row_posture(row, semantics_key="temporal_semantics")
        comparability_counts[posture] = comparability_counts.get(posture, 0) + 1
    return {
        "schema_version": "animal-sample-chronology-review.v1",
        "row_count": len(rows),
        "strength_counts": strength_counts,
        "evidence_counts": evidence_counts,
        "precision_counts": precision_counts,
        "normalization_counts": normalization_counts,
        "comparability_counts": comparability_counts,
        "direct_links": {
            "sample_chronology_review": "data/adna/governance/source_library/sample_chronology_review.json",
            "sample_chronology_provenance_review": "data/adna/governance/source_library/sample_chronology_provenance_review.json",
            "temporal_semantics_docs": "docs/public/pollenomics-data/evidence/temporal-semantics.md",
        },
        "rows": rows,
    }


def build_animal_temporal_comparison_review(
    *,
    data_root: Path,
    report_root: Path,
) -> dict[str, Any]:
    """Publish one cross-family review of direct and contextual time semantics."""
    animal_rows = list(build_sample_chronology_provenance_rows(data_root))
    sead_payload = _load_json_if_present(
        data_root / "sead" / "review" / "temporal_review.json"
    )
    sead_rows = (
        [row for row in sead_payload.get("rows", []) if isinstance(row, dict)]
        if isinstance(sead_payload, dict)
        else []
    )
    family_rows = [
        {
            "family_key": "animal_adna",
            "display_name": "Animal aDNA chronology",
            "row_count": len(animal_rows),
            "comparability_counts": _comparability_counts_from_temporal_rows(
                animal_rows,
                semantics_key="temporal_semantics",
            ),
            "comparison_policy": (
                "Animal rows only support interval comparison when sample-owned chronology survives publication without false precision."
            ),
        },
        {
            "family_key": "sead_context",
            "display_name": "SEAD archaeology context",
            "row_count": len(sead_rows),
            "comparability_counts": dict(
                sead_payload.get("comparability_posture_counts", {})
                if isinstance(sead_payload, dict)
                else {}
            ),
            "comparison_policy": (
                "SEAD rows remain site-level archaeology context even when numeric spans are available."
            ),
        },
    ]
    unsafe_findings: list[str] = []
    if any(
        _temporal_row_posture(row, semantics_key="temporal_semantics")
        == "contextual_label_only"
        for row in animal_rows
    ):
        unsafe_findings.append(
            "Animal broad-period chronology rows remain visible in governance outputs and must not be treated as sample-owned numeric dates."
        )
    if any(
        str(row.get("comparability_posture", "")).strip()
        == "mixed_interval_and_context"
        for row in sead_rows
    ):
        unsafe_findings.append(
            "SEAD rows that mix numeric spans with cultural or geologic labels remain contextual archaeology evidence, not direct event dates."
        )
    published_feature_findings = _published_temporal_feature_findings(report_root)
    unsafe_findings.extend(published_feature_findings)
    return {
        "schema_version": "animal-temporal-comparison-review.v1",
        "row_count": len(family_rows),
        "family_rows": family_rows,
        "unsafe_comparison_findings": unsafe_findings,
        "published_feature_guard_findings": published_feature_findings,
        "direct_links": {
            "animal_provenance_review": "data/adna/governance/source_library/sample_chronology_provenance_review.json",
            "sead_temporal_review": "data/sead/review/temporal_review.json",
            "publication_report_root": "docs/report/",
        },
    }


def _temporal_row_posture(row: dict[str, Any], *, semantics_key: str) -> str:
    semantics = row.get(semantics_key, {})
    if not isinstance(semantics, dict):
        return "unresolved"
    return str(semantics.get("comparability_posture", "")).strip() or "unresolved"


def _comparability_counts_from_temporal_rows(
    rows: list[dict[str, Any]],
    *,
    semantics_key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        posture = _temporal_row_posture(row, semantics_key=semantics_key)
        counts[posture] = counts.get(posture, 0) + 1
    return counts


def _published_temporal_feature_findings(report_root: Path) -> list[str]:
    findings: list[str] = []
    for path in sorted(Path(report_root).rglob("*animal_localities.geojson")):
        payload = _load_json_if_present(path)
        features = payload.get("features", [])
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if not isinstance(properties, dict):
                continue
            feature_id = str(properties.get("feature_id", "")).strip() or path.name
            semantics = properties.get("temporal_semantics", {})
            if not isinstance(semantics, dict) or not semantics:
                findings.append(
                    f"{feature_id}: missing temporal semantics in {path.name}"
                )
                continue
            posture = str(semantics.get("comparability_posture", "")).strip()
            if posture in {"contextual_label_only", "unresolved"} and any(
                properties.get(field) is not None
                for field in ("time_start_bp", "time_end_bp", "time_mean_bp")
            ):
                findings.append(
                    f"{feature_id}: contextual-only chronology still exposes numeric time fields in {path.name}"
                )
    for path in sorted(Path(report_root).rglob("*environmental_sites.geojson")):
        payload = _load_json_if_present(path)
        features = payload.get("features", [])
        if not isinstance(features, list):
            continue
        for feature in features:
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties", {})
            if not isinstance(properties, dict):
                continue
            record_id = str(properties.get("record_id", "")).strip() or path.name
            semantics = properties.get("temporal_semantics", {})
            if not isinstance(semantics, dict) or not semantics:
                findings.append(
                    f"{record_id}: missing temporal semantics in {path.name}"
                )
    return findings
