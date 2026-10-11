"""Projection rows retain observed basin evidence without conversion."""

from __future__ import annotations

import math

import pytest

from bijux_pollenomics_dev.taxa_review.lra_prerequisites.projection import (
    _basin_rows,
    _country_denominators,
)


def _sites(area: object = 125.0) -> dict[str, object]:
    return {
        "site_rows": [
            {
                "site_id": "site:1",
                "country_code": "SE",
                "candidate_sample_count": 4,
                "source_area": area,
                "source_locator": {"surface": "sites", "row_index": 1},
            }
        ]
    }


def _lake(value: object = 2.5) -> dict[str, object]:
    return {
        "source_rows": [
            {
                "site_id": "site:1",
                "source_parameter_id": 3,
                "source_parameter_code": "Area",
                "source_parameter_label": "Surface area (ha)",
                "source_value": value,
                "source_row_locator": {"page": "lakeparameters.json", "row_index": 2},
            }
        ]
    }


def test_native_and_lake_area_are_distinct_candidate_geometry_rows() -> None:
    row = _basin_rows(_sites(), _lake())[0]
    lake, native = sorted(
        row["candidate_basin_evidence"], key=lambda item: item["source_field"]
    )
    assert lake["source_field"] == "lakeparameters.value:3"
    assert lake["source_value"] == 2.5
    assert lake["source_unit"] == "Surface area (ha)"
    assert lake["source_domain"] == "area"
    assert native["source_field"] == "sites.source_payload.area"
    assert native["source_value"] == 125.0
    assert native["source_unit"] is None
    assert native["source_domain"] == "area"
    assert row["support_evidence"] == []
    assert row["basin_disposition"] == "not_evaluated"


@pytest.mark.parametrize("value", [0, -1])
def test_nonpositive_evidence_is_exposed_but_not_marked_positive(value: int) -> None:
    rows = _basin_rows(_sites(value), {"source_rows": []})
    assert rows[0]["candidate_basin_evidence"][0]["value_status"] == "nonpositive"


def test_nonfinite_evidence_cannot_enter_canonical_projection() -> None:
    with pytest.raises(ValueError, match="nonfinite"):
        _basin_rows(_sites(math.nan), {"source_rows": []})


def test_country_denominators_preserve_zero_denmark_and_refuse_unassigned() -> None:
    source_counts = {
        "DK": (0, 0),
        "FI": (1, 1),
        "NO": (2, 1),
        "SE": (3, 2),
        "UNASSIGNED": (1, 1),
    }
    screen = {
        "country_denominators": {
            country: {"screen_candidate_samples": counts[0]}
            for country, counts in source_counts.items()
        }
    }
    sites = {
        "country_denominators": {
            country: {
                "candidate_samples": counts[0],
                "candidate_source_sites": counts[1],
            }
            for country, counts in source_counts.items()
        }
    }
    chronology = [
        {"country_code": country}
        for country, counts in source_counts.items()
        for _ in range(counts[0])
    ]
    basins = [
        {"country_code": country}
        for country, counts in source_counts.items()
        for _ in range(counts[1])
    ]
    result = _country_denominators(screen, sites, chronology, basins)
    assert result["DK"] == {
        "chronology_samples": 0,
        "basin_sites": 0,
        "coverage_status": "no_necessary_candidates",
    }
    assert result["UNASSIGNED"] == {
        "chronology_samples": 1,
        "basin_sites": 1,
        "coverage_status": "refused_unassigned_country",
    }
    assert sum(row["chronology_samples"] for row in result.values()) == 7
    assert sum(row["basin_sites"] for row in result.values()) == 5
