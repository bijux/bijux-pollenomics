from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.neotoma.collection import (
    collect_neotoma_data,
)


class NeotomaCollectionWorkflowTests(unittest.TestCase):
    def test_collect_neotoma_data_preserves_full_inventory_and_retained_subset(
        self,
    ) -> None:
        inventory_rows = [
            {
                "site": {
                    "siteid": 20,
                    "sitename": "Inside Nordic",
                    "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                    "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                }
            },
            {
                "site": {
                    "siteid": 30,
                    "sitename": "Outside Nordic",
                    "geography": '{"type":"Point","coordinates":[40.0,60.0]}',
                    "datasets": [{"datasetid": 301, "datasettype": "pollen"}],
                }
            },
        ]
        matched_inventory_rows = [inventory_rows[0]]
        download_rows: list[dict[str, object]] = []
        rows: list[dict[str, object]] = []

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "neotoma"
            with (
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_inventory_rows",
                    return_value=inventory_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.filter_neotoma_dataset_inventory_rows",
                    return_value=matched_inventory_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.extract_neotoma_dataset_ids",
                    return_value=[201],
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_download_rows",
                    return_value=download_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.build_neotoma_site_rows_from_downloads",
                    return_value=rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.normalize_neotoma_rows",
                    return_value=[],
                ),
            ):
                collect_neotoma_data(
                    output_root=output_root,
                    country_boundaries={"Sweden": {"features": []}},
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            inventory_payload = json.loads(
                (
                    output_root / "raw" / "neotoma_pollen_dataset_inventory.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual(inventory_payload["queried_row_count"], 2)
        self.assertEqual(inventory_payload["retained_row_count"], 1)
        self.assertEqual(inventory_payload["retained_dataset_count"], 1)
        self.assertEqual(
            inventory_payload["endpoint"],
            "https://api.neotomadb.org/v2.0/data/datasets",
        )
        self.assertEqual(
            [item["site"]["siteid"] for item in inventory_payload["rows"]], [20, 30]
        )
        self.assertEqual(
            [item["site"]["siteid"] for item in inventory_payload["retained_rows"]],
            [20],
        )

    def test_collect_neotoma_data_writes_download_coverage_summary(self) -> None:
        inventory_rows = [
            {
                "site": {
                    "siteid": 20,
                    "sitename": "Inside Nordic",
                    "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                    "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                }
            }
        ]
        download_rows = [
            {
                "site": {
                    "siteid": 20,
                    "collectionunit": {
                        "dataset": {"datasetid": 201, "datasettype": "pollen"}
                    },
                }
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "neotoma"
            with (
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_inventory_rows",
                    return_value=inventory_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.filter_neotoma_dataset_inventory_rows",
                    return_value=inventory_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.extract_neotoma_dataset_ids",
                    return_value=[201],
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.fetch_neotoma_dataset_download_rows",
                    return_value=download_rows,
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.build_neotoma_site_rows_from_downloads",
                    return_value=[],
                ),
                patch(
                    "bijux_pollenomics.collection.sources.neotoma.collection.normalize_neotoma_rows",
                    return_value=[],
                ),
            ):
                collect_neotoma_data(
                    output_root=output_root,
                    country_boundaries={"Sweden": {"features": []}},
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            manifest_payload = json.loads(
                (
                    output_root
                    / "raw"
                    / "neotoma_pollen_dataset_downloads"
                    / "manifest.json"
                ).read_text(encoding="utf-8")
            )
        self.assertEqual(manifest_payload["requested_dataset_ids"], [201])
        self.assertEqual(manifest_payload["downloaded_dataset_ids"], [201])
        self.assertEqual(
            manifest_payload["archive_dir"], "raw/neotoma_pollen_dataset_downloads"
        )
