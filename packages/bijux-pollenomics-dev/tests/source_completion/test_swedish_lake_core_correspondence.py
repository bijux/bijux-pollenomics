"""Keep native source labels and count mass separate in lake correspondence."""

from __future__ import annotations

import pytest

from bijux_pollenomics_dev.source_completion.swedish_lake_core_correspondence import (
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
