"""Compare radius outputs without replacing historical numerical expectations."""

from __future__ import annotations

from copy import deepcopy
import csv
import io
from typing import Any

JsonObject = dict[str, Any]
SOURCE_KEYS = {
    "producer_sha256",
    "experiment_sha256",
    "source_report_sha256",
    "prediction_manifest_sha256",
    "predictions_sha256",
    "preparations_sha256",
}


def typed_equal(left: object, right: object) -> bool:
    """JSON equality includes scalar types and ordered arrays."""
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        assert isinstance(right, dict)
        return left.keys() == right.keys() and all(
            typed_equal(left[k], right[k]) for k in left
        )
    if isinstance(left, list):
        assert isinstance(right, list)
        return len(left) == len(right) and all(
            typed_equal(a, b) for a, b in zip(left, right, strict=True)
        )
    return bool(left == right)


def qualify_outputs(
    frozen: JsonObject,
    scored: JsonObject,
    scores: bytes,
    original_frozen: JsonObject,
    original_scored: JsonObject,
    original_scores: bytes,
    source: dict[str, str],
    prediction_rows: list[JsonObject],
    freeze_sha256: str,
) -> JsonObject:
    """Permit named identity metadata only; preserve every old scientific value."""
    assert set(source) == SOURCE_KEYS and all(
        isinstance(v, str) and len(v) == 64 for v in source.values()
    )
    assert frozen["source"] == source and scored["source"] == source
    assert frozen["outcomes_opened"] is False and frozen["factors"] == [0.8, 1.0, 1.2]
    assert len(prediction_rows) == 42
    identity = {
        (r["fold_id"], r["record_id"], r["baseline"]): r for r in prediction_rows
    }
    assert len(identity) == 42
    assert len({r["record_id"] for r in prediction_rows}) == 14
    assert all(
        len(r["pollen_fraction"]) == 30 and len(r["vegetation_fraction"]) == 30
        for r in prediction_rows
    )
    assert all(r["record_id"] != "author:BECKHAM" for r in prediction_rows)
    expected = deepcopy(original_frozen)
    expected["source"] = source
    assert len(expected["rows"]) == len(frozen["rows"]) == 126
    seen = set()
    for row in expected["rows"]:
        key = row["fold_id"], row["record_id"], row["method"]
        original = identity[key]
        row["published_prediction_sha256"] = original["prediction_manifest_sha256"]
        token = (*key, row["radius_factor"])
        assert token not in seen and row["radius_factor"] in [0.8, 1.0, 1.2]
        seen.add(token)
        assert (
            row["modeled_radius_m"] == row["original_radius_m"] * row["radius_factor"]
        )
        assert 0 < row["modeled_radius_m"] < 500
        assert len(row["pollen_fraction"]) == 30
        if row["radius_factor"] == 1.0:
            assert typed_equal(row["pollen_fraction"], original["pollen_fraction"])
    assert seen == {(*key, factor) for key in identity for factor in [0.8, 1.0, 1.2]}
    assert typed_equal(frozen, expected), "Frozen scientific value/type/order changed"
    expected_report = deepcopy(original_scored)
    expected_report["source"] = source
    expected_report["prediction_freeze_sha256"] = freeze_sha256
    assert typed_equal(scored, expected_report), (
        "Scored scientific value/type/order changed"
    )
    for count_key, value in [
        ("eligible_sites", 15),
        ("scored_sites", 14),
        ("prediction_rows", 126),
        ("scored_rows", 126),
    ]:
        assert type(scored[count_key]) is int and scored[count_key] == value
    assert scored["refused_site"] == "author:BECKHAM"
    assert scores == original_scores, "Historical scores CSV must remain byte exact"
    rows = list(csv.DictReader(io.StringIO(scores.decode())))
    assert len(rows) == 126 and len({r["record_id"] for r in rows}) == 14
    assert all(
        r["record_id"] != "author:BECKHAM" and int(r["observed_count"]) > 0
        for r in rows
    )
    assert {(r["record_id"], r["method"], float(r["radius_factor"])) for r in rows} == {
        (r["record_id"], r["method"], r["radius_factor"]) for r in frozen["rows"]
    }
    return {
        "all_historical_scientific_values_types_and_orders_exact": True,
        "scores_CSV_byte_exact": True,
        "frozen_rows": 126,
        "scored_sites": 14,
        "eligible_sites": 15,
        "refused_site": "author:BECKHAM",
        "training_attempts": 195,
        "training_completed": 192,
        "training_refused": 3,
        "new_fit_optimizer_R_or_Nordic_admission": False,
        "scope": "Actual fixed-vegetation forward radius sensitivity at three declared factors on fourteen prior-exposed English development sites. Source metadata names the genuine complete source run; all historical numeric values remain exact. Original factor-one forward exactness and scoring tolerance 1e-15 remain enforced by the unchanged producer. No cross-epoch tolerance or replacement expectation is introduced.",
    }


def canonical_pins(rows: list[JsonObject]) -> list[JsonObject]:
    """Order custody records by path, independently of filesystem enumeration."""
    assert all(set(row) == {"path", "sha256", "bytes"} for row in rows)
    assert all(
        isinstance(row["path"], str)
        and isinstance(row["sha256"], str)
        and type(row["bytes"]) is int
        for row in rows
    )
    assert len(rows) == len({row["path"] for row in rows})
    return sorted(rows, key=lambda row: str(row["path"]))


def validate_pin_population(
    current: list[JsonObject], expected: list[JsonObject]
) -> None:
    """Normalize only unordered custody; byte/hash drift remains a refusal."""
    assert canonical_pins(current) == canonical_pins(expected)
