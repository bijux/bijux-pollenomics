"""Literal parameter coverage preserves missing values and authority differences."""

from __future__ import annotations

from typing import Any

import pytest


def test_nominal_reference_parameter_and_missing_uncertainty_stay_distinct() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    native = {
        "taxon_axis": [
            {"native_label": "Poaceae", "taxon_id": 1, "known_NISP_sum": 10},
            {"native_label": "Ulmus", "taxon_id": 2, "known_NISP_sum": 5},
            {"native_label": "Cerealia-type", "taxon_id": 3, "known_NISP_sum": 3},
        ]
    }
    lc = [
        {
            "Plant taxa/Pollen-morphological types": "Poaceae",
            "PPE (SD)": "1 (0)",
            "FSP (m/s)": "0.035",
        }
    ]
    eu = [
        {
            "taxon": "Poaceae",
            "dataset_version": "v1",
            "region": "Europe",
            "rpp": "1",
            "rpp_se": "",
            "fall_speed_m_s": "0.035",
            "n_estimates": "14",
        },
        {
            "taxon": "Ulmus",
            "dataset_version": "v1",
            "region": "Europe",
            "rpp": "",
            "rpp_se": "",
            "fall_speed_m_s": "0.032",
            "n_estimates": "0",
        },
        {
            "taxon": "Cerealia",
            "dataset_version": "v1",
            "region": "Europe",
            "rpp": "3",
            "rpp_se": "0.5",
            "fall_speed_m_s": "0.069",
            "n_estimates": "6",
        },
    ]
    result = parameter_coverage(native, lc, eu)
    rows = {r["native_label"]: r for r in result["native_taxa"]}
    poaceae = rows["Poaceae"]["europe_2020"][0]
    assert poaceae["nominal_rpp_fsp_available"] is True
    assert poaceae["uncertainty_available"] is False
    assert poaceae["rpp_se"] == ""
    assert rows["Ulmus"]["europe_2020"][0]["nominal_rpp_fsp_available"] is False
    assert rows["Cerealia-type"]["europe_2020"] == []
    assert result["scientific_admission"] is False
    assert (
        result["native_taxa"][0]["landclim"][0]["uncertainty_semantics"]
        == "source_label_SD"
    )
    assert poaceae["uncertainty_semantics"] == "compiled_mean_SE"


def test_author_lookup_routes_are_witnesses_and_mass_accounting_not_admission() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    native = {
        "taxon_axis": [
            {"native_label": "Alnus", "taxon_id": 1, "known_NISP_sum": 20},
            {"native_label": "Sorbus", "taxon_id": 2, "known_NISP_sum": 3},
            {"native_label": "Cerealia-type", "taxon_id": 3, "known_NISP_sum": 4},
        ]
    }
    result = parameter_coverage(
        native,
        [],
        [],
        author_lookup_rows=[
            {"oldvar": "Alnus", "RPP.LANDCLIMII": "Alnus glutinosa"},
            {"oldvar": "Sorbus", "RPP.LANDCLIMII": "zz.do not use"},
        ],
    )
    assert result["author_lookup_mass"] == {
        "known_native_nisp": 27,
        "assigned_candidate_nisp": 20,
        "author_excluded_nisp": 3,
        "unmapped_nisp": 4,
    }
    assert result["native_taxa"][0]["landclim"] == []
    assert result["native_taxa"][0]["author_lookup_candidate"] == "Alnus glutinosa"
    assert result["scientific_admission"] is False


def test_conflicting_author_lookup_cannot_choose_a_favorable_route() -> None:
    import pytest

    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    with pytest.raises(ValueError, match="Conflicting"):
        parameter_coverage(
            {"taxon_axis": []},
            [],
            [],
            author_lookup_rows=[
                {"oldvar": "Quercus", "RPP.LANDCLIMII": "Quercus deciduous"},
                {"oldvar": "Quercus", "RPP.LANDCLIMII": "Quercus evergreen"},
            ],
        )


def european_row() -> dict[str, Any]:
    return {
        "taxon": "Ulmus",
        "region": "Europe",
        "dataset_version": "v1",
        "n_estimates": "2",
        "rpp": "1.2",
        "rpp_se": "0.1",
        "fall_speed_m_s": "0.032",
    }


@pytest.mark.parametrize(
    "field,value",
    [
        ("region", "Northern Hemisphere"),
        ("region", "Asia"),
        ("region", ""),
        ("dataset_version", "v3"),
        ("dataset_version", ""),
        ("n_estimates", "0.5"),
        ("n_estimates", "-1"),
        ("n_estimates", "NaN"),
        ("n_estimates", ""),
        ("n_estimates", 2),
        ("n_estimates", True),
    ],
)
def test_european_reference_schema_refuses_incompatible_authority(
    field: str, value: Any
) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    row = european_row()
    row[field] = value
    with pytest.raises(ValueError):
        parameter_coverage({"taxon_axis": []}, [], [row])


@pytest.mark.parametrize("field", ["region", "dataset_version", "n_estimates"])
def test_required_reference_metadata_cannot_be_omitted(field: str) -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    row = european_row()
    del row[field]
    with pytest.raises(ValueError):
        parameter_coverage({"taxon_axis": []}, [], [row])


def test_duplicate_version_taxon_cannot_supply_competing_productivities() -> None:
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    row = european_row()
    alternative = {**row, "rpp": "2.4"}
    with pytest.raises(ValueError, match="[Dd]uplicate"):
        parameter_coverage({"taxon_axis": []}, [], [row, alternative])


def test_versions_remain_separate_and_zero_estimate_count_preserves_missingness() -> (
    None
):
    from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.taxa import (
        parameter_coverage,
    )

    missing = {
        **european_row(),
        "n_estimates": "0",
        "rpp": "",
        "rpp_se": "",
        "fall_speed_m_s": "0.032",
    }
    alternate = {**european_row(), "dataset_version": "v2"}
    result = parameter_coverage({"taxon_axis": []}, [], [missing, alternate])
    rows = result["europe_2020_reference_rows"]
    assert rows[0]["n_estimates"] == "0"
    assert rows[0]["rpp"] == rows[0]["rpp_se"] == ""
    assert rows[0]["nominal_rpp_fsp_available"] is False
    assert rows[0]["uncertainty_available"] is False
    assert rows[1]["nominal_rpp_fsp_available"] is True
