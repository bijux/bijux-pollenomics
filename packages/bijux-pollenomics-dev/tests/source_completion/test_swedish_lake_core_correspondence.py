"""Keep native source labels and count mass separate in lake correspondence."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.source_completion.swedish_lake_core_correspondence import (
    _native_series_summary,
    _raw_count_summary,
)


def test_native_nisp_partition_keeps_mixed_labels_and_noncount_units() -> None:
    datums = [
        {"element": "pollen", "elementtype": "pollen", "units": "NISP", "value": 12},
        {
            "element": "pollen/spore",
            "elementtype": "pollen/spore",
            "units": "NISP",
            "value": 3,
        },
        {"element": "volume", "elementtype": "volume", "units": "cm3", "value": 2},
    ]
    result = _raw_count_summary(datums)
    assert result["pollen_observations"] == 1
    assert result["pollen_count"] == 12
    assert result["other_nisp_observations"] == 1
    assert result["other_nisp_count"] == 3
    assert result["non_nisp_observations"] == 1
    assert result["original_nisp_element_labels"] == {
        "pollen/pollen": {"observations": 1, "count_sum": 12},
        "pollen/spore/pollen/spore": {"observations": 1, "count_sum": 3},
    }
    assert result["non_nisp_unit_counts"] == {"cm3": 1}
    with pytest.raises(ValueError, match="exact nonnegative integer"):
        _raw_count_summary([{**datums[0], "value": 12.5}])


def test_native_series_retains_count_mass_and_age_claim_coverage() -> None:
    pollen = {
        "element": "pollen",
        "elementtype": "pollen",
        "units": "NISP",
        "value": 12,
    }
    spore = {"element": "spore", "elementtype": "spore", "units": "NISP", "value": 3}
    volume = {"element": "volume", "elementtype": "volume", "units": "cm3", "value": 2}
    age = {
        "age": 125.5,
        "chronologyname": "LANDCLIM",
        "agetype": "Calibrated radiocarbon years BP",
    }
    samples = [
        {"sampleid": 1, "datum": [pollen, spore, volume], "ages": [age]},
        {"sampleid": 2, "datum": [{**pollen, "value": 0}], "ages": []},
        {"sampleid": 3, "datum": [{**pollen, "value": 5}], "ages": [age, age]},
    ]
    result = _native_series_summary(samples)
    assert result["native_samples"] == 3
    assert result["samples_with_pollen_nisp"] == 2
    assert result["pure_pollen_nisp"] == 17
    assert result["other_nisp"] == 3
    assert result["non_nisp_observations"] == 1
    assert result["samples_without_age_claim"] == 1
    assert result["samples_with_multiple_age_claims"] == 1
    assert result["samples_with_single_age_claim"] == 1
    assert result["single_age_claim_range"] == [125.5, 125.5]
    assert result["single_age_chronology_names"] == {"LANDCLIM": 1}
    assert result["chronology_selection"] == "not_evaluated"
    mixed = _native_series_summary(
        [samples[0], {**samples[1], "ages": [{**age, "agetype": "uncalibrated BP"}]}]
    )
    assert mixed["single_age_claim_range"] is None
    with pytest.raises(ValueError, match="repeats a sample ID"):
        _native_series_summary([samples[0], samples[0]])
    with pytest.raises(ValueError, match="finite and numeric"):
        _native_series_summary([{**samples[0], "ages": [{**age, "age": float("nan")}]}])
