from __future__ import annotations

from typing import cast
import unittest

import pytest

from bijux_pollenomics.reporting.rendering import (
    build_sample_geojson_feature,
    serialize_sample_record,
)


from ..fixtures.aadr import sample_record


pytestmark = pytest.mark.generated_artifacts


class CountryReportTests(unittest.TestCase):
    def test_sample_serialization_contract_stays_aligned_between_csv_and_geojson(
        self,
    ) -> None:
        sample = sample_record(
            genetic_id="SE1",
            locality="Uppsala",
            political_entity="Sweden",
            datasets=("1240k", "ho"),
        )

        csv_payload = serialize_sample_record(sample)
        geojson_feature = build_sample_geojson_feature(sample)
        properties = cast(dict[str, object], geojson_feature["properties"])
        geometry = cast(dict[str, object], geojson_feature["geometry"])

        self.assertEqual(csv_payload["genetic_id"], properties["genetic_id"])
        self.assertEqual(csv_payload["locality"], properties["locality"])
        self.assertEqual(
            csv_payload["political_entity"],
            properties["political_entity"],
        )
        self.assertEqual(csv_payload["datasets"], properties["datasets"])
        self.assertEqual(
            csv_payload["date_stddev_bp"],
            properties["date_stddev_bp"],
        )
        self.assertEqual(csv_payload["time_start_bp"], properties["time_start_bp"])
        self.assertEqual(csv_payload["time_end_bp"], properties["time_end_bp"])
        self.assertEqual(csv_payload["time_label"], properties["time_label"])
        self.assertEqual(
            geometry["coordinates"],
            [sample.longitude, sample.latitude],
        )
