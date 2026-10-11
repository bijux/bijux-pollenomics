"""A pinned lakeparameter capture exposes source values without LRA admission."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.materialization.models import canonical_bytes
from bijux_pollenomics.analysis.lra.materialization.neotoma.lakeparameters import (
    assess_neotoma_lakeparameters,
)
from bijux_pollenomics.analysis.lra.materialization.neotoma.site_evidence import (
    NeotomaSiteEvidence,
)


def _input(tmp_path: Path) -> tuple[NeotomaSiteEvidence, Path, str]:
    sites = {
        "schema_version": "neotoma-candidate-site-evidence.v1",
        "source_snapshot_id": "source:snapshot",
        "raw_manifest_sha256": "a" * 64,
        "lra_admission_status": "refused",
        "denominators": {"lra_accepted_samples": 0, "candidate_source_sites": 2},
        "country_denominators": {"SE": {}, "NO": {}},
        "site_rows": [
            {
                "site_id": "neotoma:site:1",
                "country_code": "SE",
                "source_site_name": "Lake",
            },
            {
                "site_id": "neotoma:site:2",
                "country_code": "NO",
                "source_site_name": "Mire",
            },
        ],
    }
    site_bytes = canonical_bytes(sites)
    evidence = NeotomaSiteEvidence(site_bytes, hashlib.sha256(site_bytes).hexdigest())
    root = tmp_path / "capture"
    pages = root / "capture-pages"
    pages.mkdir(parents=True)
    rows = [
        {"siteid": 1, "lakeparameterid": 3, "value": 2.5},
        {"siteid": 999, "lakeparameterid": 3, "value": 8},
    ]
    types = [
        {
            "lakeparameterid": 3,
            "lakeparametercode": "Area",
            "lakeparameter": "Surface area (ha)",
        }
    ]
    records = []
    for name, table, limit, content_rows in (
        ("lakeparameters-000.json", "lakeparameters", 1000, rows),
        ("lakeparametertypes.json", "lakeparametertypes", 100, types),
    ):
        content = canonical_bytes({"status": "success", "data": content_rows})
        (pages / name).write_bytes(content)
        records.append(
            {
                "path": name,
                "url": f"https://api.neotomadb.org/v2.0/data/dbtables/{table}?limit={limit}&offset=0",
                "offset": 0,
                "bytes": len(content),
                "sha256": hashlib.sha256(content).hexdigest(),
                "rows": len(content_rows),
            }
        )
    capture = {
        "schema_version": "neotoma-live-lakeparameter-custody.v1",
        "source_consistency": "live_paginated_not_transactional_snapshot",
        "candidate_site_report_sha256": evidence.result_digest,
        "basin_admission_status": "not_evaluated",
        "pages": records,
        "table_rows": 2,
        "type_rows": 1,
        "candidate_site_ids": 2,
        "candidate_site_ids_with_parameter_rows": 1,
        "candidate_parameter_rows": 1,
        "candidate_rows": [rows[0]],
        "parameter_types": types,
    }
    capture_bytes = canonical_bytes(capture)
    (root / "capture.json").write_bytes(capture_bytes)
    return evidence, root, hashlib.sha256(capture_bytes).hexdigest()


def test_source_parameter_is_observed_only_with_row_lineage(tmp_path: Path) -> None:
    evidence, root, digest = _input(tmp_path)
    result = assess_neotoma_lakeparameters(evidence, root, digest).as_dict()
    assert result["candidate_source_sites"] == 2
    assert result["candidate_sites_with_observed_parameter_rows"] == 1
    assert result["candidate_sites_without_observed_parameter_rows"] == 1
    assert result["absence_interpretation"] == "not_certified_by_live_offset_pagination"
    assert result["lra_admitted_samples"] == 0
    assert result["source_rows"] == [
        {
            "site_id": "neotoma:site:1",
            "country_code": "SE",
            "source_site_name": "Lake",
            "source_parameter_id": 3,
            "source_parameter_code": "Area",
            "source_parameter_label": "Surface area (ha)",
            "source_value": 2.5,
            "source_row_locator": {
                "page": "lakeparameters-000.json",
                "page_sha256": json.loads((root / "capture.json").read_text())["pages"][
                    0
                ]["sha256"],
                "row_index": 0,
            },
            "basin_admission_status": "not_reviewed",
        }
    ]


def test_capture_pin_and_source_bytes_are_required(tmp_path: Path) -> None:
    evidence, root, digest = _input(tmp_path)
    with pytest.raises(ValueError, match="pinned input"):
        assess_neotoma_lakeparameters(evidence, root, "0" * 64)
    path = root / "capture-pages" / "lakeparameters-000.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="page bytes"):
        assess_neotoma_lakeparameters(evidence, root, digest)


def test_summary_cannot_hide_or_invent_source_rows(tmp_path: Path) -> None:
    evidence, root, _ = _input(tmp_path)
    path = root / "capture.json"
    capture = json.loads(path.read_text())
    capture["candidate_rows"] = []
    altered = canonical_bytes(capture)
    path.write_bytes(altered)
    with pytest.raises(ValueError, match="summary differs"):
        assess_neotoma_lakeparameters(
            evidence, root, hashlib.sha256(altered).hexdigest()
        )


def test_full_source_capture_can_project_larger_same_source_cohort(
    tmp_path: Path,
) -> None:
    original, root, capture_digest = _input(tmp_path)
    (root / "site-evidence.json").write_bytes(original.canonical_json)
    current_sites = original.as_dict()
    current_sites["denominators"]["candidate_source_sites"] = 3
    current_sites["site_rows"].append(
        {
            "site_id": "neotoma:site:999",
            "country_code": "SE",
            "source_site_name": "Additional lake",
        }
    )
    current_bytes = canonical_bytes(current_sites)
    current = NeotomaSiteEvidence(
        current_bytes, hashlib.sha256(current_bytes).hexdigest()
    )
    result = assess_neotoma_lakeparameters(current, root, capture_digest).as_dict()
    assert result["capture_site_evidence_sha256"] == original.result_digest
    assert result["site_evidence_sha256"] == current.result_digest
    assert result["candidate_source_sites"] == 3
    assert result["candidate_sites_with_observed_parameter_rows"] == 2
    assert result["lra_admitted_samples"] == 0

    (root / "site-evidence.json").write_bytes(b"{}")
    with pytest.raises(ValueError, match="Original capture site review digest"):
        assess_neotoma_lakeparameters(current, root, capture_digest)
