from __future__ import annotations

import unittest
from typing import cast

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)

from tests.support.neotoma import download_row


class NeotomaSampleSemanticsTests(unittest.TestCase):
    def test_projects_depth_thickness_and_analyst_as_joinable_fields(self) -> None:
        payload = build_neotoma_relational_snapshot(
            [download_row()],
            source_snapshot_id="sha256:fixture",
            build_id="fixture-build",
        )

        samples = cast(list[dict[str, object]], payload["samples"])
        sample = samples[0]
        self.assertEqual(sample["source_analysis_unit_name"], "10 cm")
        self.assertIsNone(sample["source_sample_name"])
        self.assertIsNone(sample["source_igsn"])
        self.assertEqual(sample["source_depth"], 10)
        self.assertEqual(sample["source_thickness"], 1)
        self.assertEqual(sample["source_sample_analysts"], [{"contactid": 42}])

    def test_preserves_zero_depth_without_inventing_missing_thickness(self) -> None:
        row = download_row()
        site = cast(dict[str, object], row["site"])
        unit = cast(dict[str, object], site["collectionunit"])
        dataset = cast(dict[str, object], unit["dataset"])
        samples = cast(list[dict[str, object]], dataset["samples"])
        samples[0]["depth"] = 0
        samples[0]["thickness"] = None

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        sample = cast(list[dict[str, object]], payload["samples"])[0]
        self.assertEqual(sample["source_depth"], 0)
        self.assertIsNone(sample["source_thickness"])


if __name__ == "__main__":
    unittest.main()
