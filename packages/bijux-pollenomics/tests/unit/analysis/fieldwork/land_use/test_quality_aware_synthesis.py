from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics.analysis.fieldwork.land_use.models import _Target
from bijux_pollenomics.analysis.fieldwork.land_use.synthesis import build_synthesis


def _feature(*, quality_class: str, time_start_bp: int) -> dict[str, object]:
    return {
        "properties": {
            "record_id": f"cell:{time_start_bp}",
            "parent_grid_record_id": "cell",
            "time_start_bp": time_start_bp,
            "time_end_bp": time_start_bp + 100,
            "time_mean_bp": time_start_bp + 50,
            "time_label": f"{time_start_bp}-{time_start_bp + 100} BP",
            "quality_class": quality_class,
            "reconstruction_values": {
                "ET": 0.0,
                "ST": 0.0,
                "OL": 0.0,
                "AL": 0.0,
                "GL": 0.0,
                "Cerealia.t": 0.0,
                "Secale": 0.0,
            },
        }
    }


def _build(features: list[dict[str, object]]) -> dict[str, object]:
    target = _Target(
        requested_name="Lake",
        registry_name="Lake",
        latitude=56.0,
        longitude=13.0,
        target_class="registered_lake",
        lake_decision="include_lake_review",
        decision_reason="Governed.",
        coordinate_source="Registry.",
    )
    return build_synthesis(
        context_root=Path("/unused"),
        lake_report=SimpleNamespace(assessments=()),
        human_localities=(),
        animal_localities=(),
        load_features=lambda path: features if "landclim" in str(path) else [],
        synthesis_targets=lambda report: (target,),
        target_landclim_features=lambda selected, rows: rows,
        target_row=lambda *args, **kwargs: {
            "landclim_coverage_posture": "covered_by_governed_grid"
        },
        overlapping_geojson_context=lambda **kwargs: {
            "record_count": 1,
            "locality_count": 1,
        },
        overlapping_human_context=lambda **kwargs: {
            "sample_count": 2,
            "locality_count": 1,
        },
        overlapping_animal_context=lambda **kwargs: {
            "sample_count": 3,
            "locality_count": 1,
        },
        number=lambda value: round(float(value), 6),
        cross_proxy_posture=lambda **kwargs: "pollen_archaeology_human_animal_context",
        dataset_id="937075",
        context_radius_km=20,
    )


def test_no_pollen_quality_retains_chronology_and_nulls_every_modeled_value() -> None:
    payload = _build([_feature(quality_class="no_pollen_data", time_start_bp=100)])

    row = payload["rows"][0]  # type: ignore[index]
    assert row["quality_class"] == "no_pollen_data"
    assert row["time_start_bp"] == 100
    assert row["time_end_bp"] == 200
    assert all(
        row[key] is None
        for key in (
            "forest_cover",
            "evergreen_tree_cover",
            "summergreen_tree_cover",
            "open_land_cover",
            "agricultural_land_cover",
            "grassland_cover",
            "cereal_type_pollen_cover",
            "rye_pollen_cover",
        )
    )
    assert row["cross_proxy_posture"] == "archaeology_human_animal_context"


@pytest.mark.parametrize("quality_class", ("high", "low"))
def test_available_quality_preserves_legitimate_zeroes(quality_class: str) -> None:
    payload = _build([_feature(quality_class=quality_class, time_start_bp=0)])

    row = payload["rows"][0]  # type: ignore[index]
    assert row["quality_class"] == quality_class
    assert all(
        row[key] == 0.0
        for key in (
            "forest_cover",
            "evergreen_tree_cover",
            "summergreen_tree_cover",
            "open_land_cover",
            "agricultural_land_cover",
            "grassland_cover",
            "cereal_type_pollen_cover",
            "rye_pollen_cover",
        )
    )
    assert row["cross_proxy_posture"] == "pollen_archaeology_human_animal_context"


@pytest.mark.parametrize("missing_value", (None, False, float("nan")))
def test_available_quality_refuses_missing_or_nonfinite_modeled_values(
    missing_value: object,
) -> None:
    feature = _feature(quality_class="high", time_start_bp=0)
    feature["properties"]["reconstruction_values"]["OL"] = missing_value  # type: ignore[index]

    with pytest.raises(ValueError, match="LandClim OL must be a finite numeric value"):
        _build([feature])


def test_rows_are_ordered_oldest_to_present_with_explicit_interval_semantics() -> None:
    payload = _build(
        [
            _feature(quality_class="high", time_start_bp=0),
            _feature(quality_class="low", time_start_bp=100),
        ]
    )

    assert payload["temporal_direction"] == "oldest_to_present"
    assert payload["interval_semantics"] == "[younger_bp, older_bp]"
    assert [row["time_start_bp"] for row in payload["rows"]] == [100, 0]  # type: ignore[index]
