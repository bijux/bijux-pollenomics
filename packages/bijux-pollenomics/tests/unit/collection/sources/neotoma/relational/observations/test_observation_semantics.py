from __future__ import annotations

from typing import cast
import unittest

from bijux_pollenomics.analysis.lra.materialization.counts import assess_count
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
        self.assertEqual(by_name["Source null"]["detection_status"], "source_null")
        self.assertIsNone(by_name["Unreported value"]["source_value"])
        self.assertEqual(
            by_name["Unreported value"]["detection_status"],
            "not_provided_by_source",
        )

    def test_same_variable_preserves_count_percentage_concentration_and_influx(
        self,
    ) -> None:
        row = download_row()
        site = cast(dict[str, object], row["site"])
        unit = cast(dict[str, object], site["collectionunit"])
        dataset = cast(dict[str, object], unit["dataset"])
        samples = cast(list[dict[str, object]], dataset["samples"])
        datum = cast(list[dict[str, object]], samples[0]["datum"])
        original = datum[0]
        expected = {
            "NISP": 9007199254740993,
            "percent": 12.5,
            "grains/cm3": 3.75,
            "grains/cm²/yr": 8.5,
        }
        datum[:] = [
            {**original, "units": source_unit, "value": value}
            for source_unit, value in expected.items()
        ]

        payload = build_neotoma_relational_snapshot(
            [row], source_snapshot_id="sha256:fixture", build_id="fixture-build"
        )
        observations = cast(list[dict[str, object]], payload["observations"])
        variables = cast(list[dict[str, object]], payload["variables"])
        self.assertEqual(len(observations), 4)
        self.assertEqual(len(variables), 1)
        self.assertEqual(
            {observation["sample_id"] for observation in observations},
            {f"neotoma:sample:{samples[0]['sampleid']}"},
        )
        self.assertEqual(
            {observation["variable_id"] for observation in observations},
            {"neotoma:variable:1947"},
        )
        self.assertEqual(
            {observation["aggregation_key"] for observation in observations},
            {f"neotoma:exact-unit:{source_unit}" for source_unit in expected},
        )
        by_unit = {
            cast(str, observation["source_unit"]): observation
            for observation in observations
        }
        for source_unit, value in expected.items():
            with self.subTest(source_unit=source_unit):
                observation = by_unit[source_unit]
                self.assertEqual(observation["source_value"], value)
                self.assertIs(type(observation["source_value"]), type(value))
                self.assertEqual(
                    observation["source_payload"],
                    {**original, "units": source_unit, "value": value},
                )
                self.assertIsNone(observation["source_denominator"])
                self.assertEqual(
                    observation["denominator_status"], "not_provided_by_source"
                )
                assessment = assess_count(observation)
                if source_unit == "NISP":
                    self.assertEqual(assessment.status, "count_candidate")
                    self.assertEqual(assessment.exact_count, 9007199254740993)
                else:
                    self.assertIsNone(assessment.exact_count)
                    self.assertEqual(assessment.reason, "source_unit_is_not_count")


if __name__ == "__main__":
    unittest.main()
