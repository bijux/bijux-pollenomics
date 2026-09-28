"""Outcome-free EMPD2–NFI public refusal contract."""

from __future__ import annotations

import csv
from hashlib import sha256
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion import empd2_nfi_pairing
from bijux_pollenomics_dev.source_completion.empd2_nfi_pairing import (
    COMMON_GAPS,
    NFI_LOCATION_FIELDS,
    SOURCE_FIELDS,
    SOURCE_INPUTS,
    build,
    decision_rows,
    public_rows,
    review_inputs,
)

REPOSITORY = Path(__file__).resolve().parents[4]


def test_tracked_guide_and_refusal_fields() -> None:
    guide, expected = SOURCE_INPUTS["slu-calibration-guide.pdf"]
    assert sha256((REPOSITORY / guide).read_bytes()).hexdigest() == expected
    assert "nfi_tree_measurement_values_and_units" in COMMON_GAPS
    assert "reviewed_nonnull_benchmark_minimum_and_thresholds" in COMMON_GAPS


def test_local_review_inputs_remain_source_bound_when_present() -> None:
    if any(not (REPOSITORY / path).is_file() for path, _ in SOURCE_INPUTS.values()):
        pytest.skip("original review reports are optional local source inputs")
    projection, dossier, spatial = review_inputs(REPOSITORY)
    assert projection["candidate_count"] == 16
    assert projection["admitted_pair_count"] == 0
    assert dossier["selected_lead_count"] == 16
    assert (
        spatial["thresholds_descriptive_only"]["1000"][
            "candidate_plot_year_sample_pairs"
        ]
        == 53
    )
    assert spatial["worksheet_access"].endswith(
        "no tree measurements displayed or scored"
    )


def test_missing_rows_and_positive_admission_refused() -> None:
    projection = {"candidate_count": 16, "admitted_pair_count": 0}
    dossier = {"selected_lead_count": 16}
    with pytest.raises(ValueError, match="denominator changed"):
        decision_rows(projection, dossier, [])
    projection["admitted_pair_count"] = 1
    with pytest.raises(ValueError, match="denominator changed"):
        decision_rows(projection, dossier, [])


def test_existing_destination_refused_before_private_source_access(
    tmp_path: Path,
) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(ValueError, match="Absent output destination required"):
        build(
            REPOSITORY, tmp_path / "private.sqlite3", tmp_path / "private.xlsx", output
        )


def test_public_projection_excludes_source_plot_location_and_key() -> None:
    source_row: dict[str, object] = {
        "candidate_id": "empd2-nfi:sample:nfi-tract-plot-year",
        "empd2_sample": "sample",
        "nfi_source_sha256": "a" * 64,
        "nfi_tract": "tract",
        "nfi_plot": "plot",
        "nfi_year": "year",
        "nfi_inventory_date_source_native": "date",
        "nfi_easting_sweref99tm": 500000.0,
        "nfi_northing_sweref99tm": 7000000.0,
        "nfi_longitude_wgs84": 15.0,
        "nfi_latitude_wgs84": 63.0,
    }
    source_row.update(
        {field: "refused" for field in SOURCE_FIELDS if field not in source_row}
    )
    public = public_rows([source_row])[0]
    assert NFI_LOCATION_FIELDS.isdisjoint(public)
    assert "tract" not in str(public)
    assert "plot-year" not in str(public)
    assert len(str(public["nfi_row_identity_sha256"])) == 64


def test_governed_zero_pair_ledger_matches_current_producer() -> None:
    root = REPOSITORY / "docs/report/validation/empd2-nfi-pairing"
    report = json.loads((root / "report.json").read_text())
    ledger = (root / "pairs.csv").read_bytes()
    with (root / "pairs.csv").open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    producer = Path(empd2_nfi_pairing.__file__)
    assert (
        report["input_sha256"]["producer"] == sha256(producer.read_bytes()).hexdigest()
    )
    assert report["pairs_csv"] == {
        "bytes": len(ledger),
        "sha256": sha256(ledger).hexdigest(),
    }
    for path, digest in SOURCE_INPUTS.values():
        assert report["input_sha256"][path.as_posix()] == digest
    assert len(rows) == report["denominators"]["current_benchmark_refusals"] == 16
    assert report["denominators"]["measured_pairs_admitted"] == 0
    assert all(row["scientific_admission"] == "false" for row in rows)
    assert all(
        row["current_benchmark_decision"] == "refused_missing_pair_evidence"
        for row in rows
    )
    assert all(NFI_LOCATION_FIELDS.isdisjoint(row) for row in rows)
