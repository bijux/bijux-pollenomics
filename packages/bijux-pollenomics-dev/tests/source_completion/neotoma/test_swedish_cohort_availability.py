"""Prior-processing metadata prevents GARASEL from becoming an untouched target."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path
import runpy
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[5]
PRODUCER = (
    ROOT / "docs/report/source-relations/neotoma/swedish-cohort-availability/replay.py"
)
_CROSSWALK = "data/landclim/review/rootsi-candidate-inputs/rootsi-crosswalk.csv"
_CENSUS = "reports/science/publication-correspondence/rootsi-feature-census/report.json"


def _inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    row = {
        "rootsi_sequence_label_raw": "GARASEL",
        "rootsi_site_name_raw": "Garaselet (Byskeälven)",
        "rootsi_source_locator": "rootsi/Metadata table_SWE_climate.xlsx!25",
        "rootsi_latitude_raw": "65.333332999999996",
        "rootsi_longitude_raw": "19.933333000000001",
        "typed_workbook_member": "rootsi/GARASEL.xls",
        "typed_workbook_sha256": "f" * 64,
        "typed_workbook_bytes": "19968",
    }
    crosswalk = root / _CROSSWALK
    crosswalk.parent.mkdir(parents=True)
    with crosswalk.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    evidence = {
        "crosswalk": {
            "path": _CROSSWALK,
            "sha256": sha256(crosswalk.read_bytes()).hexdigest(),
        }
    }
    census = {
        "canonical_crosswalk": evidence["crosswalk"],
        "source_commit": "a" * 40,
        "workbooks": [
            {
                "archive_member": row["typed_workbook_member"],
                "sha256": row["typed_workbook_sha256"],
                "bytes": 19968,
                "metadata_source_locator": row["rootsi_source_locator"],
                "status": "computed",
                "value_origin": "decoded cached values; literal/formula origin unavailable",
                "sheet": "Sheet1",
            }
        ],
    }
    path = root / _CENSUS
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(census))
    evidence["census"] = {
        "path": _CENSUS,
        "sha256": sha256(path.read_bytes()).hexdigest(),
    }
    return {"prior_processing_evidence": evidence}, census


def test_metadata_evidence_never_opens_target_workbook_or_cells(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    producer = runpy.run_path(str(PRODUCER))
    declared, _ = _inputs(tmp_path)
    opened: list[Path] = []
    original = Path.open

    def metadata_only(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path.suffix.lower() not in {".xls", ".xlsx"}
        assert path.name != "cells.jsonl"
        opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", metadata_only)
    result = producer["_garasel_prior_processing"](tmp_path, declared)
    assert set(opened) == {tmp_path / _CROSSWALK, tmp_path / _CENSUS}
    assert result["workbook_member"] == "rootsi/GARASEL.xls"
    assert result["target_measurement_values_opened_by_this_check"] is False
    assert result["fitting_or_tuning_exposure"] == "not_established_by_these_records"


@pytest.mark.parametrize("selected_age", [False, True])
@pytest.mark.parametrize(
    "licence", [None, "https://creativecommons.org/licenses/by/4.0/"]
)
def test_age_or_rights_repair_cannot_restore_untouched_status(
    tmp_path: Path, selected_age: bool, licence: str | None
) -> None:
    producer = runpy.run_path(str(PRODUCER))
    declared, _ = _inputs(tmp_path)
    exposure = producer["_garasel_prior_processing"](tmp_path, declared)
    lead = {
        "core_handle": "GARASEL",
        "selected_sample_age_sequence_identified": selected_age,
        "profile_license": licence,
        "decision": "metadata_lead_only_core_alias_and_selected_age_model_unresolved",
    }
    before = dict(lead)
    result = producer["_prior_processing_facet"](lead, exposure)
    assert lead == before
    assert result["decision"] == "refused_as_untouched_prior_numeric_source_processing"
    assert result["untouched_confirmation_eligible"] is False
    assert result["untouched_status_restored_by_age_or_rights_repair"] is False
    assert result["selected_sample_age_sequence_identified"] is selected_age
    assert result["profile_license"] == licence


@pytest.mark.parametrize(
    "handle", ["ADRAN", "HAKULLA5", "LEVEANIE", "NDRAKET", "VUOLEPAL"]
)
def test_other_candidate_dispositions_and_fields_are_unchanged(handle: str) -> None:
    producer = runpy.run_path(str(PRODUCER))
    lead = {
        "core_handle": handle,
        "decision": "existing_disposition",
        "selected_sample_age_sequence_identified": False,
    }
    assert producer["_prior_processing_facet"](lead, {}) is lead


@pytest.mark.parametrize(
    "field,value",
    [
        ("sha256", "0" * 64),
        ("bytes", 19969),
        ("status", "not_run"),
        ("value_origin", "headers only"),
        ("metadata_source_locator", "other!2"),
    ],
)
def test_inconsistent_or_uncomputed_exposure_does_not_fall_back_to_fresh_lead(
    tmp_path: Path, field: str, value: object
) -> None:
    producer = runpy.run_path(str(PRODUCER))
    declared, census = _inputs(tmp_path)
    census["workbooks"][0][field] = value
    path = tmp_path / _CENSUS
    path.write_text(json.dumps(census))
    declared["prior_processing_evidence"]["census"]["sha256"] = sha256(
        path.read_bytes()
    ).hexdigest()
    with pytest.raises(ValueError, match="numeric-processing evidence differs"):
        producer["_garasel_prior_processing"](tmp_path, declared)


def test_metadata_drift_missing_identity_and_missing_exposure_are_refused(
    tmp_path: Path,
) -> None:
    producer = runpy.run_path(str(PRODUCER))
    declared, _ = _inputs(tmp_path)
    (tmp_path / _CROSSWALK).write_text("changed metadata")
    with pytest.raises(ValueError, match="metadata identity changed"):
        producer["_garasel_prior_processing"](tmp_path, declared)
    with pytest.raises(ValueError, match="evidence is unavailable"):
        producer["_prior_processing_facet"]({"core_handle": "GARASEL"}, {})
