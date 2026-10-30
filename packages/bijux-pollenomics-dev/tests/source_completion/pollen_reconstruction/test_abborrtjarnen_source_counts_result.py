"""Controlled checks and explicit saved-result observation for source counts."""

from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path

import pytest

from .abborrtjarnen_source_counts.independent_controls import (
    AXIS,
    COLUMNS,
    native_control,
    original_control,
    producer_control_result,
)
from .abborrtjarnen_source_counts.independent_result import check_comparison
from .abborrtjarnen_source_counts.independent_sources import (
    depth_pairs,
    literal_count,
    native_samples,
    original_rows,
)


@pytest.mark.parametrize(
    "token,status,value",
    [
        ("", "blank", None),
        ("  ", "blank", None),
        ("0.00", "zero", 0),
        ("2", "positive", 2),
        ("1.5", "invalid", None),
        ("-1", "invalid", None),
        ("NaN", "invalid", None),
        ("<1", "invalid", None),
    ],
)
def test_literal_zero_blank_positive_and_invalid_are_distinct(
    token: str, status: str, value: int | None
) -> None:
    assert literal_count(token) == (status, value)


def test_exact_depth_join_and_missing_slot_do_not_invent_a_reported_zero() -> None:
    description, header, original = original_rows(original_control(), COLUMNS)
    native = native_samples(json.dumps(native_control()).encode(), AXIS)
    pairs = depth_pairs(original, native)
    assert header[0] == "Depth sed [m]" and "Juniperus-type" in description
    assert [(a.depth_m, b.sample_id) for a, b in pairs] == [
        (Fraction(101, 100), 10),
        (Fraction(51, 50), 20),
    ]
    assert original[0].physical_line == 13 and original[1].physical_line == 14
    assert pairs[0][1].values[1] == 0
    assert pairs[1][1].values[1] is None
    assert literal_count(pairs[1][0].tokens[1]) == ("zero", 0)


@pytest.mark.parametrize("token", ["", "2", "oops", "1.5", "-2"])
def test_absent_native_slot_retains_its_original_literal(token: str) -> None:
    _, _, original = original_rows(original_control(token), COLUMNS)
    native = native_samples(json.dumps(native_control()).encode(), AXIS)
    row, sample = depth_pairs(original, native)[1]
    assert sample.values[1] is None and row.tokens[1] == token
    assert literal_count(token)[0] == (
        "blank" if not token else "positive" if token == "2" else "invalid"
    )


def test_nonbinary_decimal_depths_cannot_be_coalesced_into_one_owner() -> None:
    body = original_control().replace(b"1.01", b"1.010000000000000001")
    _, _, original = original_rows(body, COLUMNS)
    native = native_samples(json.dumps(native_control()).encode(), AXIS)
    with pytest.raises(ValueError, match="depth populations"):
        depth_pairs(original, native)


@pytest.mark.parametrize(
    "fault",
    [
        "original_depth",
        "native_depth",
        "sample_id",
        "taxon_id",
        "floating_taxon_id",
        "name",
        "duplicate_count",
        "bool_count",
    ],
)
def test_ambiguous_source_owners_and_measurements_refuse(fault: str) -> None:
    original = original_control()
    native = deepcopy(native_control())
    samples = native["data"][0]["site"]["collectionunit"]["dataset"]["samples"]
    if fault == "original_depth":
        original = original.replace(b"1.02", b"1.010")
    elif fault == "native_depth":
        samples[0]["depth"] = samples[1]["depth"]
    elif fault == "sample_id":
        samples[0]["sampleid"] = samples[1]["sampleid"]
    elif fault == "taxon_id":
        samples[0]["datum"][0]["taxonid"] = 999
    elif fault == "floating_taxon_id":
        samples[0]["datum"][0]["taxonid"] = 29.0
    elif fault == "name":
        samples[0]["datum"][0]["variablename"] = "Another Betula"
    elif fault == "duplicate_count":
        samples[0]["datum"].append(samples[0]["datum"][0])
    else:
        samples[0]["datum"][0]["value"] = True
    with pytest.raises(ValueError):
        _, _, source = original_rows(original, COLUMNS)
        target = native_samples(json.dumps(native).encode(), AXIS)
        depth_pairs(source, target)


@pytest.mark.parametrize(
    "absent_token", ["0.00", "3", "", "1.5", "oops", "NaN", "-1", "Infinitude"]
)
def test_saved_comparison_preserves_literal_states(absent_token: str) -> None:
    original = original_control(absent_token)
    native = native_control()
    result = producer_control_result(original, native)
    assert (
        check_comparison(
            result,
            original,
            json.dumps(native).encode(),
            expected_samples=2,
            expected_reported=9,
        )["slots_checked"]
        == 10
    )
    for key in ("original_status", "original_token", "native_value"):
        changed = deepcopy(result)
        changed["absence_candidates"][0][key] = "altered"
        with pytest.raises(ValueError, match="absence_candidates"):
            check_comparison(
                changed,
                original,
                json.dumps(native).encode(),
                expected_samples=2,
                expected_reported=9,
            )


def test_any_reported_conflict_withholds_absent_native_candidates() -> None:
    original = original_control().replace(b"1.01\t2\t", b"1.01\t9\t")
    native = native_control()
    result = producer_control_result(original, native)
    assert result["absence_candidates"] == []
    assert (
        check_comparison(
            result,
            original,
            json.dumps(native).encode(),
            expected_samples=2,
            expected_reported=9,
        )["reported_disagreements"]
        == 1
    )
    result["candidate_classification_status"] = "enabled_reported_counts_match"
    with pytest.raises(ValueError):
        check_comparison(
            result,
            original,
            json.dumps(native).encode(),
            expected_samples=2,
            expected_reported=9,
        )


def test_changed_source_bytes_refuse_old_identity(tmp_path: Path) -> None:
    import hashlib

    from .abborrtjarnen_source_counts.independent_checks import (
        METADATA,
        NATIVE,
        ORIGINAL,
        pinned_bodies,
    )

    pins = {}
    for relative in (ORIGINAL, NATIVE, METADATA):
        body = b"controlled source"
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(body)
        pins[relative] = {
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    assert len(pinned_bodies(tmp_path, pins)) == 3
    (tmp_path / ORIGINAL).write_bytes(b"controlled sourcf")
    with pytest.raises(ValueError, match="source identity changed"):
        pinned_bodies(tmp_path, pins)


if __name__ == "__main__":
    from .abborrtjarnen_source_counts.independent_checks import main

    main(Path(__file__))
