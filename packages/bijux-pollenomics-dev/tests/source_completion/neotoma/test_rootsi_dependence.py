"""Partial count correspondence cannot become independent or equivalent evidence."""

from copy import deepcopy
import csv
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.source_completion import rootsi_landclim_overlap as overlap
from bijux_pollenomics_dev.source_completion.neotoma import rootsi_dependence as subject


@pytest.fixture
def reports(tmp_path: Path) -> Path:
    """Use small controlled reports, never copies of the private workbooks."""
    pins = {}
    for i, (name, schema, count_field) in enumerate(subject.NATIVE_REPORTS):
        value = {
            "schema_version": schema,
            "lra_admitted_samples": 0,
            "rootsi_archive_member": f"rootsi/{i}.xls",
            "neotoma_dataset_id": 100 + i,
            "neotoma_site_id": 200 + i,
            "samples": 10,
            "input_sha256": {
                "rootsi_workbook": str(i + 1) * 64,
                "neotoma_raw_part": "a" * 64,
            },
            count_field: {
                "explicit_agreement": 7,
                "explicit_difference": 2,
                "absent_source_workbook_positive": 3,
            },
            "age_model_identity": "not established",
        }
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
        pins[name] = hashlib.sha256(path.read_bytes()).hexdigest()
    findings = []
    for i in (3, 4):
        findings.append(
            {
                "workbook_member": f"rootsi/{i}.xls",
                "workbook_sha256": str(i + 1) * 64,
                "neotoma_dataset_id": 100 + i,
                "neotoma_site_id": 200 + i,
                "workbook_sample_rows": 10,
                "neotoma_sample_rows": 10,
                "paired_depth_rows": 10,
                "historical_landclim_input_authenticated": False,
                "lra_admitted_samples": 0,
                "selected_count_cell_status": {
                    "explicit_agreement": 7,
                    "absent_source_zero": 5,
                    "absent_source_positive": 3,
                },
                "unmatched_age_rows": [
                    {"workbook_sheet_row": 6, "workbook_age_label": 3910.8}
                ],
                "workbook_age_column": False,
            }
        )
    path = tmp_path / subject.CHRONOLOGY_REPORT
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "rootsi-neotoma-chronology-witness.v1",
                "findings": findings,
            }
        )
    )
    pins[subject.CHRONOLOGY_REPORT] = hashlib.sha256(path.read_bytes()).hexdigest()
    lock = tmp_path / "reports/source-lock.json"
    lock.parent.mkdir(parents=True)
    lock.write_text(json.dumps({"sources": pins}))
    return tmp_path


def candidates() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for i in range(79):
        row = dict.fromkeys(overlap.FIELDS, "")
        row.update(
            typed_workbook_member=f"rootsi/{i}.xls",
            typed_workbook_sha256=str(i + 1) * 64 if i < 5 else "f" * 64,
            publication_sequence=f"sequence:{i}",
            site_record_id=f"937075:sequence:{i}",
            independent_ground_truth="refused_candidate_overlap",
        )
        rows.append(dict(row))
    return rows


def test_exact_member_and_bytes_join_preserves_all_partial_evidence(
    reports: Path,
) -> None:
    rows = candidates()
    witnesses = subject.load_witnesses(reports)
    result = subject.dependence_rows(rows, witnesses)
    assert len(result) == 79
    assert all(
        row["independent_corroboration_admitted"] == "false"
        and row["physical_core_equivalence_admitted"] == "false"
        for row in result
    )
    assert all(
        row["independent_ground_truth"] == "refused_candidate_overlap" for row in result
    )
    assert len([row for row in result if row["neotoma_dataset_id"]]) == 5
    assert all(
        row["neotoma_dataset_id"] == ""
        and row["count_statuses_json"] == ""
        and row["neotoma_dependence_posture"]
        == "not_assessed_by_selected_count_witnesses"
        for row in result[5:]
    )
    assert json.loads(str(result[1]["count_statuses_json"]))["explicit_difference"] == 2
    assert (
        json.loads(str(result[1]["count_statuses_json"]))[
            "absent_source_workbook_positive"
        ]
        == 3
    )
    assert json.loads(str(result[3]["count_statuses_json"]))["absent_source_zero"] == 5
    assert (
        json.loads(str(result[3]["witness_limits_json"]))["unmatched_age_rows"][0][
            "workbook_age_label"
        ]
        == 3910.8
    )
    assert (
        json.loads(str(result[4]["witness_limits_json"]))["workbook_age_column"]
        is False
    )
    assert (
        result[3]["count_witness_locator"] == subject.CHRONOLOGY_REPORT + "#/findings/0"
    )
    assert all(
        {k: row[k] for k in overlap.FIELDS} == original
        for row, original in zip(result, rows, strict=True)
    )


def test_display_sequence_names_cannot_establish_or_prevent_a_join(
    reports: Path,
) -> None:
    rows = candidates()
    rows[0]["publication_sequence"] = "unrelated display name"
    rows[6]["publication_sequence"] = rows[1]["publication_sequence"]
    result = subject.dependence_rows(rows, subject.load_witnesses(reports))
    assert result[0]["neotoma_dataset_id"] == "neotoma:dataset:100"
    assert result[6]["neotoma_dataset_id"] == ""


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "duplicate_member",
        "missing_member",
        "independence",
        "row_count",
        "witness_count",
        "duplicate_witness",
        "duplicate_native",
        "path",
    ],
)
def test_changed_or_ambiguous_member_ownership_refuses(
    reports: Path, change: str
) -> None:
    rows = candidates()
    witnesses = list(subject.load_witnesses(reports))
    if change == "hash":
        rows[0]["typed_workbook_sha256"] = "b" * 64
    elif change == "duplicate_member":
        rows[1]["typed_workbook_member"] = rows[0]["typed_workbook_member"]
    elif change == "missing_member":
        rows[0]["typed_workbook_member"] = "rootsi/unassessed.xls"
    elif change == "independence":
        rows[0]["independent_ground_truth"] = "admitted"
    elif change == "row_count":
        rows.pop()
    elif change == "witness_count":
        witnesses.pop()
    elif change == "duplicate_witness":
        witnesses[1] = witnesses[0]
    elif change == "duplicate_native":
        witnesses[1] = replace(
            witnesses[1],
            dataset_id=witnesses[0].dataset_id,
            site_id=witnesses[0].site_id,
        )
    else:
        rows[0]["typed_workbook_member"] = "rootsi/../elsewhere.xls"
    with pytest.raises(ValueError):
        subject.dependence_rows(rows, witnesses)


@pytest.mark.parametrize("change", ["missing_pin", "changed_report", "symlink"])
def test_selected_numeric_reports_require_existing_integrity_authority(
    reports: Path, change: str
) -> None:
    name = subject.NATIVE_REPORTS[0][0]
    path = reports / name
    if change == "missing_pin":
        lock = reports / "reports/source-lock.json"
        value = json.loads(lock.read_text())
        del value["sources"][name]
        lock.write_text(json.dumps(value))
    elif change == "changed_report":
        path.write_bytes(path.read_bytes() + b" ")
    else:
        target = path.with_suffix(".original")
        path.rename(target)
        path.symlink_to(target)
    with pytest.raises((ValueError, ReportRebuildError)):
        subject.load_witnesses(reports)


def test_unrelated_source_lock_edits_do_not_cascade(reports: Path) -> None:
    expected = subject.load_witnesses(reports)
    lock = reports / "reports/source-lock.json"
    value = json.loads(lock.read_text())
    value["maintained_paths"] = ["README.md"]
    value["sources"]["unrelated-numeric.json"] = "b" * 64
    lock.write_text(json.dumps(value, indent=2))
    assert subject.load_witnesses(reports) == expected


@pytest.mark.parametrize(
    "field,bad",
    [
        ("neotoma_dataset_id", True),
        ("neotoma_site_id", 0),
        ("samples", None),
        ("lra_admitted_samples", 1),
        ("schema_version", "another-profile"),
    ],
)
def test_rebound_report_cannot_promote_native_scope(
    reports: Path, field: str, bad: object
) -> None:
    name = subject.NATIVE_REPORTS[0][0]
    path = reports / name
    value = json.loads(path.read_text())
    value[field] = bad
    path.write_text(json.dumps(value))
    lock = reports / "reports/source-lock.json"
    pins = json.loads(lock.read_text())
    pins["sources"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    lock.write_text(json.dumps(pins))
    with pytest.raises(ValueError):
        subject.load_witnesses(reports)


def test_opt_in_adds_one_csv_without_changing_existing_reports(
    reports: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Exercise the existing owner with controlled metadata and witness inputs."""
    root = reports
    metadata = root / overlap.RAW_METADATA
    metadata.parent.mkdir(parents=True)
    metadata.write_bytes(b"controlled publication metadata")
    receipt = root / overlap.SOURCE_RECEIPT
    receipt.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "937075",
                        "doi": overlap.DOI,
                        "files": [metadata.name],
                    }
                ]
            }
        )
    )
    candidate = root / overlap.ROOTSI
    candidate.mkdir(parents=True)
    for name in overlap.EXPECTED_CANDIDATE_SHA256:
        (candidate / name).write_text(
            "{}\n" if name.endswith((".json", ".jsonl")) else "column\n"
        )
    sites = root / overlap.SITES
    sites.parent.mkdir(parents=True)
    sites.write_text("column\n")
    manifest: dict[str, Any] = {
        "sources": {
            "publication_inventory": {
                "workbook_sha256": hashlib.sha256(metadata.read_bytes()).hexdigest(),
                "receipt_sha256": hashlib.sha256(receipt.read_bytes()).hexdigest(),
            }
        },
        "output_contract": {"matching_profile": "controlled metadata"},
    }
    monkeypatch.setattr(
        overlap, "verify_candidate_inputs", lambda _: deepcopy(manifest)
    )
    monkeypatch.setattr(overlap, "reconcile", lambda *_: candidates())
    old = root / "artifacts/original"
    extra = root / "artifacts/dependence"
    overlap.build(root, old)
    overlap.build(root, extra, neotoma_dependence=True)
    for name in ("overlap.csv", "report.json"):
        assert (old / name).read_bytes() == (extra / name).read_bytes()
    assert {p.name for p in extra.iterdir()} == {
        "overlap.csv",
        "report.json",
        "neotoma-dependence.csv",
    }
    with (extra / "neotoma-dependence.csv").open(newline="") as handle:
        result = list(csv.DictReader(handle))
    assert (
        len(result) == 79
        and sum(bool(row["neotoma_dataset_id"]) for row in result) == 5
    )
    assert (extra / "neotoma-dependence.csv").stat().st_size < 1024**2


def test_cli_passes_only_explicit_dependence_option(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls = []
    monkeypatch.setattr(
        overlap, "build", lambda *args, **kwargs: calls.append((args, kwargs))
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "overlap",
            "--repository",
            str(tmp_path),
            "--output",
            str(tmp_path / "artifacts/result"),
            "--neotoma-dependence",
        ],
    )
    overlap.main()
    assert calls[0][1] == {"neotoma_dependence": True}
