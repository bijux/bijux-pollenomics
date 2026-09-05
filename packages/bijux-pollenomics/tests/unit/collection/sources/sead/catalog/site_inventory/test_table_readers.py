from __future__ import annotations

import unittest

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
    MappingSeadTableReader,
)


class MappingSeadTableReaderTests(unittest.TestCase):
    def test_projects_filters_and_orders_admitted_rows(self) -> None:
        reader = MappingSeadTableReader(
            {
                "tbl_samples": [
                    {"sample_id": 3, "site_id": 9, "ignored": "third"},
                    {"sample_id": 1, "site_id": 8, "ignored": "first"},
                    {"sample_id": 2, "site_id": 9, "ignored": "second"},
                ]
            }
        )

        rows = reader.rows_by_ids(
            "tbl_samples",
            select="sample_id,site_id",
            filter_field="site_id",
            ids=[9],
            order_by=("sample_id",),
        )

        self.assertEqual(
            rows,
            [
                {"sample_id": 2, "site_id": 9},
                {"sample_id": 3, "site_id": 9},
            ],
        )

    def test_rejects_missing_tables_and_projection_fields(self) -> None:
        reader = MappingSeadTableReader({"tbl_samples": [{"sample_id": 1}]})

        with self.assertRaisesRegex(ValueError, "table is unavailable"):
            reader.all_rows(
                "tbl_sites",
                select="site_id",
                order_by=("site_id",),
            )
        with self.assertRaisesRegex(ValueError, "misses projected fields"):
            reader.all_rows(
                "tbl_samples",
                select="sample_id,site_id",
                order_by=("sample_id",),
            )


if __name__ == "__main__":
    unittest.main()
