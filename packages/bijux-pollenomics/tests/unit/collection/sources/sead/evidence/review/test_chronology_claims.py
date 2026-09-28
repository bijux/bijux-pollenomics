"""Gold age-type and source-value checks for the pinned SEAD claim review."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.sead.evidence.normalization.chronology_policy import (
    sead_claim_age_policy,
)
from bijux_pollenomics.collection.sources.sead.evidence.review.chronology_claims import (
    PINNED_CLAIM_INDEX_SHA256,
    build_sead_chronology_age_review,
    review_claim_age_basis,
    write_sead_chronology_age_review,
)

ROOT = next(
    parent
    for parent in Path(__file__).parents
    if (parent / "configs/pytest.ini").is_file()
)
RUN = "sead-full-evidence-39bfff6a-ce80714e"
RAW = ROOT / "data/sead/raw/acquisitions" / RUN
NORMALIZED = ROOT / "data/sead/normalized/acquisitions" / RUN


def _gold_claim(
    kind: str,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], str, str, str]:
    index = json.loads((NORMALIZED / "chronology_claims.json").read_text())
    part = json.loads((NORMALIZED / "chronology_claims/claims-00001.json").read_text())
    claim = next(row for row in part["claims"] if row["claim_type"] == kind)
    table = claim["source_table"]
    rows = json.loads((RAW / f"payloads/{table}.json").read_text())["rows"]
    native = next(
        row
        for row in rows
        if str(
            row[
                {
                    "dating_range": "analysis_dating_range_id",
                    "relative_period": "relative_date_id",
                }[kind]
            ]
        )
        == claim["source_record_id"]
    )
    age_type = json.loads((RAW / "payloads/tbl_age_types.json").read_text())["rows"][0]
    return (
        claim,
        native,
        age_type,
        index["table_payload_sha256"][table],
        index["source_build_id"],
        index["acquisition_manifest_sha256"],
    )


def test_pinned_age_review_accounts_for_every_claim_and_source_basis() -> None:
    report, rows = build_sead_chronology_age_review(ROOT / "data")
    assert len(rows) == report["claim_count"] == 25_109
    assert report["input_hashes"]["claim_index_sha256"] == PINNED_CLAIM_INDEX_SHA256
    assert report["age_type_authority"]["age_type_id"] == 1
    assert report["age_type_authority"]["age_type"] == "AD"
    assert report["reviewed_age_basis_counts"] == {
        "ad_calendar_year_negative_bp_refused": 60,
        "ad_calendar_year_open_ended_from_context": 1_094,
        "ad_calendar_year_to_1950_bp": 13_170,
        "analysis_entity_age_basis_unspecified": 641,
        "geochronology_calibration_posture_unknown": 87,
        "relative_period_requires_governed_mapping": 10_057,
    }
    assert len(report["gold_examples"]) == 8
    assert report["review_posture"]["scientific_chronology_admission_approved"] is False
    assert report["review_posture"]["event_propagation_approved"] is False
    assert all(row["propagation_eligibility"] == "refused" for row in rows)


@pytest.mark.parametrize(
    ("native_type", "unit", "calibration", "status", "transformation"),
    [
        (
            "cal BP",
            "years_bp",
            "calibrated",
            "comparable",
            "sead-cal-bp-canonical-interval-v1",
        ),
        (
            "calibrated years bp",
            "years_bp",
            "calibrated",
            "comparable",
            "sead-cal-bp-canonical-interval-v1",
        ),
        (
            "calendar years before present",
            "years_bp",
            "calibrated",
            "comparable",
            "sead-cal-bp-canonical-interval-v1",
        ),
        (
            "AD",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "CE",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "anno domini",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "common era",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "BC",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "BCE",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "before christ",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        (
            "before common era",
            "calendar_year",
            "not_applicable",
            "comparable",
            "sead-calendar-year-to-cal-bp-1950-v1",
        ),
        ("unreviewed radiometric basis", "unknown", "unknown", "unresolved", None),
    ],
)
def test_age_type_policy_gold_branches_are_explicit(
    native_type: str,
    unit: str,
    calibration: str,
    status: str,
    transformation: str | None,
) -> None:
    result = sead_claim_age_policy(
        "dating_range",
        {"age_type": native_type, "time_start_bp": 100, "time_end_bp": 200},
    )
    assert result["source_age_unit"] == unit
    assert result["calibration_status"] == calibration
    assert result["comparability_status"] == status
    assert result["transformation_id"] == transformation
    assert (result["younger_bp"], result["older_bp"]) == (
        (None, None) if status == "unresolved" else (100, 200)
    )


def test_direct_public_review_refuses_changed_native_ad_value() -> None:
    claim, native, age_type, payload_sha, build_id, manifest_sha = _gold_claim(
        "dating_range"
    )
    native = dict(native)
    native["low_value"] += 1
    with pytest.raises(ValueError, match="native age field changed"):
        review_claim_age_basis(
            claim,
            native,
            age_type=age_type,
            source_payload_sha256=payload_sha,
            source_build_id=build_id,
            acquisition_manifest_sha256=manifest_sha,
        )


def test_direct_public_review_refuses_bad_calendar_conversion() -> None:
    claim, native, age_type, payload_sha, build_id, manifest_sha = _gold_claim(
        "dating_range"
    )
    claim = dict(claim)
    claim["source_age_value"] = dict(claim["source_age_value"])
    claim["source_age_value"]["time_start_bp"] += 1
    with pytest.raises(ValueError, match="AD conversion differs"):
        review_claim_age_basis(
            claim,
            native,
            age_type=age_type,
            source_payload_sha256=payload_sha,
            source_build_id=build_id,
            acquisition_manifest_sha256=manifest_sha,
        )


def test_direct_public_review_refuses_contextual_numeric_upgrade() -> None:
    claim, native, age_type, payload_sha, build_id, manifest_sha = _gold_claim(
        "relative_period"
    )
    claim = dict(claim)
    claim["younger_bp"] = 4_350
    with pytest.raises(
        ValueError, match="contextual age gained unsupported numeric status"
    ):
        review_claim_age_basis(
            claim,
            native,
            age_type=age_type,
            source_payload_sha256=payload_sha,
            source_build_id=build_id,
            acquisition_manifest_sha256=manifest_sha,
        )


def test_writer_retains_every_review_and_refuses_existing_destination(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "review"
    report = write_sead_chronology_age_review(ROOT / "data", destination)
    monkeypatch.chdir(ROOT)
    relative_destination = tmp_path / "relative-review"
    write_sead_chronology_age_review(Path("data"), relative_destination)
    with (destination / "claims.csv").open(newline="") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == report["claim_review_csv"]["row_count"] == 25_109
    assert json.loads((destination / "report.json").read_text()) == report
    assert (destination / "report.json").read_bytes() == (
        relative_destination / "report.json"
    ).read_bytes()
    assert (destination / "claims.csv").read_bytes() == (
        relative_destination / "claims.csv"
    ).read_bytes()
    assert b"\r" not in (destination / "claims.csv").read_bytes()
    with pytest.raises(ValueError, match="must be absent"):
        write_sead_chronology_age_review(ROOT / "data", destination)
