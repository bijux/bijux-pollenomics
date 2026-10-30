"""Preserve the recorded GARASEL exposure without reopening observations."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_cohort as subject,
)

ROOT = next(
    p
    for p in Path(__file__).resolve().parents
    if (p / "configs/ci/report-ownership.json").is_file()
)


def current_reports() -> tuple[dict[str, Any], dict[str, Any]]:
    historical = ROOT / Path(subject.CAPTURE).parent / "publication/report.json"
    return json.loads(historical.read_bytes()), json.loads(
        (ROOT / subject.REPORT).read_bytes()
    )


def copy_exposure_metadata(root: Path) -> dict[str, Any]:
    declaration = Path(subject.REPORT).with_name("sources.json")
    declared: dict[str, Any] = json.loads((ROOT / declaration).read_bytes())
    for relative in [
        declaration,
        *[Path(pin["path"]) for pin in declared["prior_processing_evidence"].values()],
    ]:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, path)
    return declared


def test_current_refusal_reads_only_declared_exposure_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical, current = current_reports()
    declaration = ROOT / Path(subject.REPORT).with_name("sources.json")
    declared = json.loads(declaration.read_bytes())
    expected = {
        declaration,
        *[ROOT / pin["path"] for pin in declared["prior_processing_evidence"].values()],
    }
    opened = set()
    original = Path.open

    def metadata_only(path: Path, *args: Any, **kwargs: Any) -> Any:
        assert path in expected
        assert path.suffix.lower() not in {".xls", ".xlsx"}
        assert path.name != "cells.jsonl"
        opened.add(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", metadata_only)
    subject.validate_current_report(ROOT, historical, current)
    assert opened == expected


@pytest.mark.parametrize(
    "defect",
    [
        "old_population",
        "current_population",
        "current_source_identity",
        "current_cross_archive_coordinate",
        "other_lead_disposition",
        "other_lead_added_field",
        "missing_lead",
        "new_top_level_field",
        "garasel_original_field",
        "garasel_old_decision",
        "garasel_missing_proof",
        "garasel_extra_field",
        "untouched_eligible",
        "untouched_after_repair",
        "numeric_false_flag",
        "claimed_workbook_read",
        "claimed_tuning",
        "claimed_census_commit",
        "claimed_workbook_identity",
        "claimed_sheet",
    ],
)
def test_current_addition_cannot_rewrite_science_or_restore_freshness(
    defect: str,
) -> None:
    historical, current = current_reports()
    garasel = current["epd_metadata_screen"]["named_leads"][1]
    if defect == "old_population":
        historical["neotoma_inventory"]["records"] = 103
    elif defect == "current_population":
        current["neotoma_inventory"]["records"] = 103
    elif defect == "current_source_identity":
        current["private_source_manifest_sha256"] = "0" * 64
    elif defect == "current_cross_archive_coordinate":
        current["cross_archive_leads"][0]["pangaea_latitude_longitude"][0] += 1
    elif defect == "other_lead_disposition":
        current["epd_metadata_screen"]["named_leads"][0]["decision"] = "admitted"
    elif defect == "other_lead_added_field":
        current["epd_metadata_screen"]["named_leads"][0]["new_field"] = True
    elif defect == "missing_lead":
        current["epd_metadata_screen"]["named_leads"].pop()
    elif defect == "new_top_level_field":
        current["freshness_admitted"] = True
    elif defect == "garasel_original_field":
        garasel["selected_sample_age_sequence_identified"] = True
    elif defect == "garasel_old_decision":
        garasel["decision"] = historical["epd_metadata_screen"]["named_leads"][1][
            "decision"
        ]
    elif defect == "garasel_missing_proof":
        del garasel["prior_source_processing"]
    elif defect == "garasel_extra_field":
        garasel["new_field"] = True
    elif defect == "untouched_eligible":
        garasel["untouched_confirmation_eligible"] = True
    elif defect == "untouched_after_repair":
        garasel["untouched_status_restored_by_age_or_rights_repair"] = True
    elif defect == "numeric_false_flag":
        garasel["untouched_confirmation_eligible"] = 0
    elif defect == "claimed_workbook_read":
        garasel["prior_source_processing"][
            "target_measurement_values_opened_by_this_check"
        ] = True
    elif defect == "claimed_tuning":
        garasel["prior_source_processing"]["fitting_or_tuning_exposure"] = "established"
    elif defect == "claimed_census_commit":
        garasel["prior_source_processing"]["completed_census_source_commit"] = "0" * 40
    elif defect == "claimed_workbook_identity":
        garasel["prior_source_processing"]["workbook_sha256"] = "0" * 64
    else:
        garasel["prior_source_processing"]["sheet"] = "unrelated"
    with pytest.raises(ReportRebuildError):
        subject.validate_current_report(ROOT, historical, current)


@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "changed_bytes",
        "wrong_source_path",
        "uncomputed",
        "different_value_origin",
        "different_census_commit",
        "different_sheet",
        "different_locator",
        "different_byte_count",
        "crosswalk_disagreement",
        "duplicate_workbook",
    ],
)
def test_current_proof_requires_actual_completed_metadata(
    tmp_path: Path, defect: str
) -> None:
    declared = copy_exposure_metadata(tmp_path)
    historical, current = current_reports()
    pin = declared["prior_processing_evidence"]["census"]
    path = tmp_path / pin["path"]
    census = json.loads(path.read_bytes())
    entry = next(
        row
        for row in census["workbooks"]
        if row["archive_member"] == "rootsi/GARASEL.xls"
    )
    if defect == "missing":
        path.unlink()
    elif defect == "changed_bytes":
        path.write_bytes(path.read_bytes() + b"\n")
    elif defect == "wrong_source_path":
        pin["path"] = "data/private/unowned.json"
    else:
        if defect == "uncomputed":
            entry["status"] = "not_run"
        elif defect == "different_value_origin":
            entry["value_origin"] = "headers only"
        elif defect == "different_census_commit":
            census["source_commit"] = "0" * 40
        elif defect == "different_sheet":
            entry["sheet"] = "unrelated"
        elif defect == "different_locator":
            entry["metadata_source_locator"] = (
                "rootsi/Metadata table_SWE_climate.xlsx!26"
            )
        elif defect == "different_byte_count":
            entry["bytes"] = 19969
        elif defect == "crosswalk_disagreement":
            census["canonical_crosswalk"]["sha256"] = "0" * 64
        else:
            census["workbooks"].append(deepcopy(entry))
        path.write_text(json.dumps(census))
        pin["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    declaration = tmp_path / Path(subject.REPORT).with_name("sources.json")
    declaration.write_text(json.dumps(declared))
    current["epd_metadata_screen"]["named_leads"][1]["prior_source_processing"][
        "evidence_inputs"
    ] = declared["prior_processing_evidence"]
    with pytest.raises(ReportRebuildError):
        subject.validate_current_report(tmp_path, historical, current)
