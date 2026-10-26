"""Analytical native-count support controls without sequence-arrival assumptions."""

from __future__ import annotations

from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.nordic.sequence_support import (
    DEPTH_UNIT,
    _decimal,
    _index,
    _revision,
    scope_support,
)


def _sample(sid: str, depth: object, age: object) -> dict[str, Any]:
    return {
        "sample_id": sid,
        "source_depth": depth,
        "source_age_bp": age,
        "age_type": "Calendar years BP",
        "chronology_id": "chronology-a",
        "age_status": "resolved_source_age",
    }


def test_selected_boundary_is_distinct_from_captured_owner_boundary() -> None:
    samples = [
        _sample("top", 1, -52),
        _sample("middle", 3, 100),
        _sample("bottom", 10, 500),
    ]
    native = {"top": [0], "middle": [3, 2]}
    selected = scope_support(samples[:2], native)
    captured = scope_support(samples, native)
    assert selected["positive_at_bottom"] is True
    assert captured["positive_at_bottom"] is False
    assert captured["deepest_positive_sample_id"] == "middle"
    assert captured["top_sample_id"] == "top"
    assert captured["reported_count_total"] == 5
    assert captured["positive_samples"] == 1
    assert captured["reported_zero_only_samples"] == 1
    assert captured["missing_measurement_samples"] == 1
    assert captured["maximum_adjacent_depth_gap_native"] == "7"
    assert captured["age_order_status"] == "resolved_source_point_age_order"
    assert DEPTH_UNIT == "native_depth_unit_not_explicit_in_payload"


def test_native_input_order_cannot_change_sequence_boundary() -> None:
    samples = [_sample("a", 2, -1), _sample("b", 5, 200), _sample("c", 9, 500)]
    counts = {"a": [1], "c": [4]}
    assert scope_support(samples, counts) == scope_support(samples[::-1], counts)


@pytest.mark.parametrize("depth", [None, True, "NaN", "Infinity", "not a depth"])
def test_missing_invalid_or_nonfinite_depth_refuses_without_dropping_sample(
    depth: object,
) -> None:
    result = scope_support(
        [_sample("a", depth, 0), _sample("b", 2, 1)], {"a": [5], "b": [0]}
    )
    assert result["sample_count"] == 2 and result["reported_count_total"] == 5
    assert result["depth_boundary_status"] == "refused"
    assert result["positive_at_top"] is None and result["positive_at_bottom"] is None
    assert "missing_or_invalid_depth" in result["reason_codes"]


def test_duplicate_depth_and_age_reversal_are_separate_refusals() -> None:
    duplicate = scope_support([_sample("a", 1, 0), _sample("b", 1, 1)], {"a": [2]})
    assert duplicate["depth_boundary_status"] == "refused"
    assert "duplicate_depth" in duplicate["reason_codes"]
    reversal = scope_support([_sample("a", 1, 100), _sample("b", 2, -10)], {"b": [2]})
    assert reversal["depth_boundary_status"] == "resolved_native_depth_order"
    assert reversal["positive_at_bottom"] is True
    assert reversal["age_order_status"] == "refused"
    assert "age_reversal_with_depth" in reversal["reason_codes"]


def test_invalid_count_is_neither_missing_nor_reported_zero() -> None:
    result = scope_support(
        [_sample("a", 1, 0), _sample("b", 2, 1)], {"a": [None], "b": [0]}
    )
    assert result["invalid_measurement_samples"] == 1
    assert result["reported_zero_only_samples"] == 1
    assert result["missing_measurement_samples"] == 0
    assert result["positive_samples"] == 0
    assert result["positive_at_bottom"] is None


def test_no_reported_positive_never_becomes_a_biological_absence() -> None:
    result = scope_support([_sample("a", 1, 0)], {})
    assert result["missing_measurement_samples"] == 1
    assert result["positive_samples"] == 0
    assert result["deepest_positive_sample_id"] is None
    assert "biological_absence" not in result
    assert (
        scope_support([_sample("a", 1, 0)], {"a": []})["missing_measurement_samples"]
        == 1
    )


@pytest.mark.parametrize("invalid", [-1, True, 0.5])
def test_unvalidated_count_cannot_enter_support(invalid: Any) -> None:
    with pytest.raises(ValueError, match="validated integers"):
        scope_support([_sample("a", 1, 0)], {"a": [invalid]})


def test_unresolved_or_mixed_chronology_keeps_depth_count_evidence() -> None:
    a, b = _sample("a", 1, 0), _sample("b", 2, None)
    b.update(
        age_status="refused_missing_ambiguous_or_invalid_source_age", chronology_id=None
    )
    result = scope_support([a, b], {"a": [1], "b": [2]})
    assert result["depth_boundary_status"] == "resolved_native_depth_order"
    assert result["positive_at_top"] is True and result["positive_at_bottom"] is True
    assert result["age_order_status"] == "refused"
    assert set(result["reason_codes"].split(";")) == {
        "unresolved_source_age",
        "mixed_source_chronology_or_age_basis",
    }


def test_native_ownership_collision_is_refused() -> None:
    with pytest.raises(ValueError, match="Duplicate native identity"):
        _index([{"sample_id": "a"}, {"sample_id": "a"}], "sample_id")
    with pytest.raises(ValueError, match="nonempty"):
        scope_support([], {})
    assert _decimal("-52.5") is not None


@pytest.mark.parametrize("dirty_helper", [False, True])
def test_source_revision_guard_binds_the_consumed_count_predicate(
    monkeypatch: pytest.MonkeyPatch, dirty_helper: bool
) -> None:
    commands: list[list[str]] = []

    def run(command: list[str], **_: Any) -> subprocess.CompletedProcess[str]:
        commands.append(command)
        if dirty_helper and "diff" in command:
            raise subprocess.CalledProcessError(1, command)
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(
        subprocess, "check_output", lambda *a, **kw: "source-revision\n"
    )
    monkeypatch.setattr(subprocess, "run", run)
    repository = Path(__file__).resolve().parents[5]
    if dirty_helper:
        with pytest.raises(subprocess.CalledProcessError):
            _revision(repository)
    else:
        assert _revision(repository) == "source-revision"
    assert len(commands) == 2
    for command in commands:
        assert command[-2:] == [
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/nordic/sequence_support.py",
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/nordic_direct_pollen.py",
        ]
