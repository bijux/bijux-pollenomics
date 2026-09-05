from __future__ import annotations

from typing import cast
import unittest

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from tests.support.neotoma import download_row


class NeotomaObservationSemanticsTests(unittest.TestCase):
    def test_distinguishes_zero_source_null_and_unreported_values(self) -> None:
        row = download_row()
        site = cast(dict[str, object], row["site"])
        unit = cast(dict[str, object], site["collectionunit"])
        dataset = cast(dict[str, object], unit["dataset"])
        samples = cast(list[dict[str, object]], dataset["samples"])
        datum = cast(list[dict[str, object]], samples[0]["datum"])
        source_null = dict(datum[0])
        source_null["taxonid"] = 1948
        source_null["variablename"] = "Source null"
        source_null["value"] = None
        unreported = dict(datum[0])
        unreported["taxonid"] = 1949
        unreported["variablename"] = "Unreported value"
        del unreported["value"]
        datum.extend((source_null, unreported))

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )

        observations = cast(list[dict[str, object]], payload["observations"])
        by_name = {
            cast(str, observation["source_reported_name"]): observation
            for observation in observations
        }
        self.assertEqual(by_name["Poaceae (Cerealia-type)"]["source_value"], 0)
        self.assertEqual(
            by_name["Poaceae (Cerealia-type)"]["detection_status"],
            "reported_value",
        )
        self.assertIsNone(by_name["Source null"]["source_value"])
        self.assertEqual(
            by_name["Source null"]["detection_status"], "source_null"
        )
        self.assertIsNone(by_name["Unreported value"]["source_value"])
        self.assertEqual(
            by_name["Unreported value"]["detection_status"],
            "not_provided_by_source",
        )


if __name__ == "__main__":
    unittest.main()
