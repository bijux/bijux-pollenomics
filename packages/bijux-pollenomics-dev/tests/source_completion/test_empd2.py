"""Candidate screening keeps count failures and source-native ages observable."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3

import pytest

from bijux_pollenomics_dev.source_completion.empd2 import screen_empd2


def _fixture(tmp_path: Path) -> tuple[Path, str, Path, str]:
    source = tmp_path / "candidate.sqlite3"
    db = sqlite3.connect(source)
    db.execute(
        "CREATE TABLE metadata (samplename TEXT, country TEXT, longitude REAL, "
        "latitude REAL, agebp, ageuncertainty TEXT, ispercent INTEGER, "
        "isdigitised INTEGER)"
    )
    db.execute('CREATE TABLE p_counts (samplename TEXT, var_ INTEGER, "count")')
    db.executemany(
        "INSERT INTO metadata VALUES (?,?,?,?,?,?,?,?)",
        [
            ("good", "Sweden", 20.0, 60.0, 0, "A", 0, 0),
            ("fraction", "Sweden", 21.0, 61.0, "NULL", "B", 0, 0),
            ("percent", "Norway", 22.0, 62.0, None, "C", 1, 0),
            ("zero", "Denmark", 10.0, 56.0, None, "A", 0, 0),
            ("missing", "Finland", 25.0, 64.0, None, "A", 0, 0),
            ("outside", "Germany", 10.0, 50.0, None, "A", 0, 0),
        ],
    )
    db.executemany(
        "INSERT INTO p_counts VALUES (?,?,?)",
        [
            ("good", 1, 4),
            ("fraction", 1, 49.5),
            ("percent", 1, 5),
            ("zero", 1, 0),
            ("outside", 1, 6),
        ],
    )
    db.commit()
    db.close()
    overlap = tmp_path / "overlap.jsonl"
    overlap.write_text(
        json.dumps(
            {
                "empd_samplename": "good",
                "empd_country": "Sweden",
                "identity_decision": "unresolved_hypothesis",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    return (
        source,
        hashlib.sha256(source.read_bytes()).hexdigest(),
        overlap,
        hashlib.sha256(overlap.read_bytes()).hexdigest(),
    )


def test_nordic_screen_preserves_count_and_identity_refusals(tmp_path: Path) -> None:
    source, source_hash, overlap, overlap_hash = _fixture(tmp_path)
    result = screen_empd2(
        source, source_hash, overlap_review=overlap, overlap_sha256=overlap_hash
    )
    assert result["source_metadata_rows_all_countries"] == 6
    assert result["nordic_sample_count"] == 5
    assert result["scientific_admission"] == "candidate_only"
    assert result["measured_vegetation_reference_count"] == 0
    assert result["country_counts"]["Sweden"] == {
        "metadata_samples": 2,
        "count_rows": 2,
        "invalid_count_rows": 1,
        "mechanical_count_candidates": 1,
        "unresolved_overlap_samples": 1,
    }
    rows = {row["source_sample_name"]: row for row in result["samples"]}
    assert rows["good"]["source_agebp"] == 0
    assert rows["good"]["mechanical_count_candidate"] is True
    assert rows["good"]["review_reason_codes"] == ["cross_source_identity_unresolved"]
    assert rows["fraction"]["source_agebp"] == "NULL"
    assert rows["fraction"]["invalid_count_rows"][0]["source_count"] == 49.5
    assert "invalid_count_value" in rows["fraction"]["review_reason_codes"]
    assert rows["percent"]["review_reason_codes"] == ["source_percent_flag_not_zero"]
    assert rows["zero"]["review_reason_codes"] == ["no_positive_integer_count"]
    assert rows["missing"]["review_reason_codes"] == [
        "no_count_rows",
        "no_positive_integer_count",
    ]


def test_digest_and_unresolved_overlap_are_required(tmp_path: Path) -> None:
    source, source_hash, overlap, overlap_hash = _fixture(tmp_path)
    with pytest.raises(ValueError, match="source_digest_mismatch"):
        screen_empd2(source, "0" * 64)
    with pytest.raises(ValueError, match="overlap_digest_mismatch"):
        screen_empd2(
            source, source_hash, overlap_review=overlap, overlap_sha256="0" * 64
        )
    overlap.write_text(
        json.dumps(
            {
                "empd_samplename": "good",
                "empd_country": "Sweden",
                "identity_decision": "same",
            }
        )
        + "\n"
    )
    changed_hash = hashlib.sha256(overlap.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="unreviewed_overlap_decision"):
        screen_empd2(
            source, source_hash, overlap_review=overlap, overlap_sha256=changed_hash
        )


def test_cross_country_sample_collision_refuses_count_ownership(tmp_path: Path) -> None:
    source, _, _, _ = _fixture(tmp_path)
    db = sqlite3.connect(source)
    db.execute(
        "INSERT INTO metadata VALUES (?,?,?,?,?,?,?,?)",
        ("good", "Germany", 10.0, 50.0, None, "A", 0, 0),
    )
    db.commit()
    db.close()
    source_hash = hashlib.sha256(source.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="invalid_or_duplicate_source_sample_identity"):
        screen_empd2(source, source_hash)


def test_overlap_country_mismatch_refuses_leakage_group(tmp_path: Path) -> None:
    source, source_hash, overlap, _ = _fixture(tmp_path)
    overlap.write_text(
        json.dumps(
            {
                "empd_samplename": "good",
                "empd_country": "Norway",
                "identity_decision": "unresolved_hypothesis",
            }
        )
        + "\n"
    )
    overlap_hash = hashlib.sha256(overlap.read_bytes()).hexdigest()
    with pytest.raises(ValueError, match="overlap_country_disagrees_with_source"):
        screen_empd2(
            source, source_hash, overlap_review=overlap, overlap_sha256=overlap_hash
        )
