from __future__ import annotations

from typing import cast
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.neotoma.collection import (
    fetch_neotoma_dataset_inventory_rows,
)


class NeotomaInventoryTests(unittest.TestCase):
    def test_fetch_neotoma_dataset_inventory_rows_reads_dataset_inventory_rows(
        self,
    ) -> None:
        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            return_value={
                "data": [
                    {
                        "site": {
                            "siteid": 20,
                            "sitename": "Agerods Mosse",
                            "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                            "datasets": [
                                {"datasetid": 201, "datasettype": "pollen"},
                                {"datasetid": 202, "datasettype": "pollen"},
                            ],
                        }
                    }
                ]
            },
        ):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))
        site = cast(dict[str, object], rows[0]["site"])
        datasets = cast(list[dict[str, object]], site["datasets"])

        self.assertEqual(len(rows), 1)
        self.assertEqual(site["siteid"], 20)
        self.assertEqual(
            [dataset["datasetid"] for dataset in datasets],
            [201, 202],
        )

    def test_fetch_neotoma_dataset_inventory_rows_uses_wide_bbox_inventory_limit(
        self,
    ) -> None:
        observed_params: list[dict[str, str]] = []

        def fake_fetch_json(
            url: str, params: dict[str, str] | None = None, **_: object
        ) -> object:
            self.assertEqual(url, "https://api.neotomadb.org/v2.0/data/datasets")
            self.assertIsNotNone(params)
            observed_params.append(dict(params or {}))
            return {
                "data": [
                    {
                        "site": {
                            "siteid": 20,
                            "sitename": "Agerods Mosse",
                            "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                            "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                        }
                    }
                ]
            }

        with patch(
            "bijux_pollenomics.collection.sources.neotoma.collection.fetch_json",
            side_effect=fake_fetch_json,
        ):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(observed_params), 1)
        self.assertEqual(observed_params[0]["limit"], "400")
        self.assertEqual(observed_params[0]["offset"], "0")
        self.assertEqual(observed_params[0]["datasettype"], "pollen")
