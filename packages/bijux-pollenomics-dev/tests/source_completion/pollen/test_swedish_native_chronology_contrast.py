"""Keep same-core chronology contrasts separate from source-age repair."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

PRODUCER = (
    Path(__file__).resolve().parents[5]
    / "reports/science/swedish-native-chronology-contrast/qualify.py"
)


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "swedish_native_chronology_contrast", PRODUCER
    )
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("point,index", [(0, 0), (100, 1), (200, None), (-45, None)])
def test_source_window_boundaries(point: float, index: int | None) -> None:
    assert module().point_window(point, [0, 100, 200]) == index


@pytest.mark.parametrize("point", [True, "100", float("nan"), float("inf")])
def test_invalid_age_value_refused(point: object) -> None:
    with pytest.raises(ValueError):
        module().point_window(point, [0, 100, 200])


def sample() -> dict[str, Any]:
    return {
        "typed_calibrated_source_ages": [
            {
                "native_chronology_id": 7,
                "source_age_type": "Calibrated radiocarbon years BP",
                "source_point_age": 7,
                "source_younger_age": -41,
                "source_older_age": 60,
                "window_index": 0,
            }
        ],
        "strict_unique_literal_parameter_counts": {
            "Betula": {"count": 5},
            "Poaceae": {"count": 0},
        },
    }


def test_raw_signed_bounds_preserved_without_changing_point_eligibility() -> None:
    source = sample()
    index, age, refusal = module().select(source, 7, [0, 100, 200])
    assert (index, refusal) == (0, None)
    assert age["source_younger_age"] == -41
    assert age == source["typed_calibrated_source_ages"][0]


def test_missing_taxon_does_not_become_observed_zero() -> None:
    source = sample()
    source["strict_unique_literal_parameter_counts"].pop("Poaceae")
    assert (
        module().select(source, 7, [0, 100, 200])[2]
        == "literal_panel_missing_or_ambiguous"
    )


def test_zero_panel_does_not_become_a_reconstruction() -> None:
    source = sample()
    source["strict_unique_literal_parameter_counts"]["Betula"]["count"] = 0
    assert module().select(source, 7, [0, 100, 200])[2] == "explicit_allzero_panel"


def test_wrong_chronology_is_missing_without_substitution() -> None:
    assert (
        module().select(sample(), 8, [0, 100, 200])[2]
        == "named_calibrated_age_missing_or_ambiguous"
    )


def test_raw_source_window_disagreement_is_refused() -> None:
    source = sample()
    source["typed_calibrated_source_ages"][0]["window_index"] = 1
    with pytest.raises(ValueError, match="witness differs"):
        module().select(source, 7, [0, 100, 200])


def test_changed_custody_is_refused_before_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="custody differs"):
        module().qualify(tmp_path)
