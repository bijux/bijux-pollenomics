"""Neotoma atlas projection fixtures."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from bijux_pollenomics.reporting.map_document.evidence_projection import (
    neotoma as neotoma_projection,
)

from .common import _write_json


def _neotoma_fixture(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    relational = root / "neotoma" / "relational"
    build_id = "sha256:" + "b" * 64
    snapshot_id = "sha256:" + "c" * 64
    surfaces: dict[str, object] = {}
    surface_rows: dict[str, list[dict[str, object]]] = {
        "sites": [
            {
                "site_id": "neotoma:site:10",
                "country_code": "SE",
                "country_decision_status": "assigned",
            }
        ],
        "collection_units": [
            {
                "site_id": "neotoma:site:10",
                "collection_unit_id": "neotoma:collection-unit:20",
                "source_collection_unit_id": 20,
                "source_payload": {"collunittype": "Core", "location": None},
            }
        ],
        "datasets": [
            {
                "site_id": "neotoma:site:10",
                "dataset_id": "neotoma:dataset:30",
                "collection_unit_id": "neotoma:collection-unit:20",
                "source_dataset_id": 30,
                "source_payload": {"datasettype": "pollen", "doi": []},
            }
        ],
        "samples": [
            {
                "site_id": "neotoma:site:10",
                "sample_id": "neotoma:sample:40",
                "collection_unit_id": "neotoma:collection-unit:20",
                "dataset_id": "neotoma:dataset:30",
                "source_sample_id": 40,
                "source_analysis_unit_id": 41,
                "source_analysis_unit_name": "12 cm",
                "source_sample_name": None,
                "source_igsn": None,
                "source_depth": 12,
                "source_thickness": None,
                "source_sample_analysts": [{"contactid": 42}],
                "source_payload": {"depth": 12, "thickness": None},
            }
        ],
        "age_claims": [
            {
                "site_id": "neotoma:site:10",
                "chronology_claim_id": "neotoma:age-claim:40:1",
                "subject_type": "sample",
                "subject_id": "neotoma:sample:40",
                "source_record_id": "neotoma:sample:40",
                "chronology_id": "neotoma:chronology:20:1",
                "chronology_name": "Default",
                "collection_unit_id": "neotoma:collection-unit:20",
                "dataset_id": "neotoma:dataset:30",
                "source_age_type": "Calibrated radiocarbon years BP",
                "source_age_unit": "year",
                "source_age_value": 125.5,
                "source_age_younger": None,
                "source_age_older": None,
                "younger_bp": 125.5,
                "older_bp": 125.5,
                "calibration_status": "calibrated",
                "comparability_status": "comparable",
                "admission_reason": None,
                "refusal_reason": None,
                "is_default_chronology": True,
                "provenance_record_id": snapshot_id,
                "source_relation_path": "neotoma:dataset:30/neotoma:sample:40/ages/1",
            }
        ],
        "variables": [
            {
                "variable_id": "neotoma:variable:50",
                "source_taxon_id": 50,
                "source_reported_name": "Triticum",
                "source_semantics": [{"source_element": "pollen"}],
                "source_units": ["NISP"],
            }
        ],
        "observations": [
            {
                "site_id": "neotoma:site:10",
                "observation_id": "neotoma:observation:40:50:1",
                "sample_id": "neotoma:sample:40",
                "variable_id": "neotoma:variable:50",
                "source_value": 3,
                "source_unit": "NISP",
                "source_denominator": None,
                "denominator_status": "not_provided_by_source",
                "detection_status": "reported_value",
                "source_context": None,
                "source_taxon_id": 50,
                "source_reported_name": "Triticum",
                "source_ecological_group": "CROP",
                "source_element": "pollen",
                "source_element_type": "pollen",
                "aggregation_key": "neotoma:exact-unit:NISP",
                "unit_family": "count",
            }
        ],
    }
    for name, rows in surface_rows.items():
        relative = f"surfaces/{name}/part-00001.json"
        payload = _write_json(
            relational / relative,
            {"row_count": len(rows), "rows": rows},
        )
        surfaces[name] = {
            "row_count": len(rows),
            "parts": [
                {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()}
            ],
        }
    manifest = {
        "source_snapshot_id": snapshot_id,
        "build_id": build_id,
        "materialization_sha256": "d" * 64,
        "surfaces": surfaces,
    }
    monkeypatch.setattr(
        neotoma_projection,
        "read_validated_neotoma_relational_manifest",
        lambda _root: manifest,
    )
