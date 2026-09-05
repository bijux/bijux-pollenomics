from __future__ import annotations

from typing import cast
import unittest

from bijux_pollenomics.collection.contracts.models import ContextPointRecord
from bijux_pollenomics.collection.sources.landclim import (
    build_landclim_spatiotemporal_review,
)
from bijux_pollenomics.collection.sources.landclim.time_windows import (
    _require_uncertainty_pair,
)


class LandClimTemporalEvidenceTests(unittest.TestCase):
    def test_model_estimates_require_exact_non_negative_uncertainty(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing=\\['Picea'\\]"):
            _require_uncertainty_pair(
                {"Picea": 0.2},
                {},
                dataset_id="900966",
                record_id="GC1:0-100 BP",
            )
        with self.assertRaisesRegex(ValueError, "standard_errors=\\['Picea'\\]"):
            _require_uncertainty_pair(
                {"Picea": 0.2},
                {"Picea": -0.01},
                dataset_id="900966",
                record_id="GC1:0-100 BP",
            )

    def test_spatiotemporal_review_links_windows_and_bibliography_by_dataset(
        self,
    ) -> None:
        record = ContextPointRecord(
            source="LandClim",
            layer_key="landclim-pollen-sites",
            layer_label="LandClim pollen site sequences",
            category="Pollen sequence",
            country="Sweden",
            record_id="937075:lake-one",
            name="Lake One",
            latitude=59.5,
            longitude=17.5,
            geometry_type="Point",
            subtitle="Site sequence",
            description="One governed sequence",
            source_url="https://doi.org/10.1594/PANGAEA.937075",
            record_count=1,
            popup_rows=(),
            time_start_bp=0,
            time_end_bp=100,
            time_mean_bp=50,
            time_label="0-100 BP",
            temporal_semantics={"comparability_posture": "numeric_interval"},
        )
        temporal_grid: dict[str, object] = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": None,
                    "properties": {
                        "dataset_id": "937075",
                        "parent_grid_record_id": "GC001",
                        "time_start_bp": 0,
                        "time_end_bp": 100,
                        "time_label": "0-100 BP",
                        "bibliography_reference_keys": [
                            "githumbi-et-al-2022",
                            "sugita-2007-reveals",
                        ],
                    },
                }
            ],
        }
        bibliography: dict[str, object] = {
            "reference_count": 2,
            "datasets": [
                {
                    "dataset_id": "937075",
                    "label": "LandClim II",
                    "doi": "https://doi.org/10.1594/PANGAEA.937075",
                    "citation": "Fyfe et al. (2021)",
                    "related_reference_keys": [
                        "githumbi-et-al-2022",
                        "sugita-2007-reveals",
                    ],
                }
            ],
        }

        review = build_landclim_spatiotemporal_review(
            [record], temporal_grid, bibliography
        )

        self.assertEqual(review["numeric_site_interval_count"], 1)
        self.assertEqual(review["numeric_temporal_grid_feature_count"], 1)
        self.assertTrue(review["all_temporal_grid_rows_have_bibliography_links"])
        rows = cast(list[dict[str, object]], review["rows"])
        self.assertEqual(rows[0]["temporal_window_count"], 1)
        self.assertEqual(rows[0]["temporal_grid_cell_count"], 1)
        self.assertTrue(rows[0]["bibliography_linkage_complete"])


if __name__ == "__main__":
    unittest.main()
