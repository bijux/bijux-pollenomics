from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.neotoma.collection import (
    build_neotoma_download_archive_parts,
)


class NeotomaArchiveTests(unittest.TestCase):
    def test_build_neotoma_download_archive_parts_splits_rows_into_stable_part_files(
        self,
    ) -> None:
        rows = [
            {"site": {"siteid": 20, "collectionunit": {"dataset": {"datasetid": 201}}}},
            {"site": {"siteid": 21, "collectionunit": {"dataset": {"datasetid": 202}}}},
            {"site": {"siteid": 22, "collectionunit": {"dataset": {"datasetid": 203}}}},
        ]

        parts = build_neotoma_download_archive_parts(rows, rows_per_part=2)

        self.assertEqual(
            [part["filename"] for part in parts], ["part-001.json", "part-002.json"]
        )
        self.assertEqual([part["row_count"] for part in parts], [2, 1])
        self.assertEqual(parts[0]["downloaded_dataset_ids"], [201, 202])
        self.assertEqual(parts[1]["downloaded_dataset_ids"], [203])
