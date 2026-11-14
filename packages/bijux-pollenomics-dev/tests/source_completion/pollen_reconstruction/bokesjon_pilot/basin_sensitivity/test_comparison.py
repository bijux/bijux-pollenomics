"""Profile sensitivity uses percentage points and preserves refusal and clipping."""

from importlib import import_module
from typing import Any

import pytest


def implementation() -> Any:
    try:
        return import_module(
            "bijux_pollenomics_dev.source_completion.pollen_reconstruction."
            "bokesjon_pilot.basin_sensitivity.workflow"
        )
    except ModuleNotFoundError:
        pytest.fail("The bounded profile sensitivity comparison is missing")


def row(name: str, first: float, signed: float | None = None) -> dict[str, Any]:
    return {
        "profile": name,
        "status": "generated",
        "signed_cover": [
            [
                first if signed is None else signed,
                1 - (first if signed is None else signed),
            ],
            [0.2, 0.8],
        ],
        "clipped_cover": [[first, 1 - first], [0.2, 0.8]],
    }


def test_pairwise_span_cannot_hide_opposite_baseline_differences() -> None:
    rows = [
        row("modern_1_5_ha", 0.41),
        row("modern_1_6_ha", 0.59),
        row("metadata_80_m", 0.5),
    ]
    result = implementation().compare_profiles(rows)
    assert result["clipped_span_pp"][0] == pytest.approx([18, 18])
    assert result["within_tolerance"] is False
    assert result["tolerance_percentage_points"] == 10


def test_ten_percentage_points_is_inclusive() -> None:
    rows = [
        row("modern_1_5_ha", 0.4),
        row("modern_1_6_ha", 0.5),
        row("metadata_80_m", 0.5),
    ]
    assert implementation().compare_profiles(rows)["within_tolerance"] is True


def test_signed_instability_remains_visible_after_clipping() -> None:
    rows = [
        row("modern_1_5_ha", 0, -0.1),
        row("modern_1_6_ha", 0, -0.4),
        row("metadata_80_m", 0, -0.2),
    ]
    result = implementation().compare_profiles(rows)
    assert result["clipped_span_pp"][0] == [0, 0]
    assert result["signed_span_pp"][0] == pytest.approx([30, 30])
    assert result["clipping_masks_larger_span"] is True


def test_refused_profile_never_becomes_zero_cover_or_robustness() -> None:
    rows = [
        row("modern_1_5_ha", 0.5),
        row("modern_1_6_ha", 0.5),
        {"profile": "metadata_80_m", "status": "refused", "reason_code": "zero_mass"},
    ]
    result = implementation().compare_profiles(rows)
    assert result["status"] == "unavailable_refused_profile"
    assert result["within_tolerance"] is None
    assert result["refused_profiles"] == ["metadata_80_m"]


def test_wrong_source_revision_stops_before_creating_study_output(
    tmp_path: Any,
) -> None:
    from pathlib import Path

    repository = next(
        p for p in Path(__file__).resolve().parents if (p / "uv.lock").is_file()
    )
    with pytest.raises(ValueError, match="revision"):
        implementation().run(repository, tmp_path / "run", source_sha="0" * 40)
    assert not (tmp_path / "run").exists()


@pytest.mark.parametrize(
    "kind", ["nonfinite", "zero_clipped_mass", "duplicate_profile"]
)
def test_invalid_cover_or_incomplete_population_cannot_pass_sensitivity(
    kind: str,
) -> None:
    rows = [
        row("modern_1_5_ha", 0.4),
        row("modern_1_6_ha", 0.5),
        row("metadata_80_m", 0.5),
    ]
    if kind == "nonfinite":
        rows[0]["signed_cover"][0][0] = float("nan")
    elif kind == "zero_clipped_mass":
        rows[0]["clipped_cover"][0] = [0.0, 0.0]
    else:
        rows[0]["profile"] = "modern_1_6_ha"
    with pytest.raises(ValueError):
        implementation().compare_profiles(rows)
