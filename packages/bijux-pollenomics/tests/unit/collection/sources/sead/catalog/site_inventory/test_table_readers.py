from __future__ import annotations

from typing import cast
import unittest

import pytest

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


def test_exact_string_foreign_key_matches_native_integer_request_without_rewriting() -> (
    None
):
    source = {"sample_id": "9007199254740993", "site_id": "1"}
    reader = MappingSeadTableReader({"tbl_samples": [source]})

    assert reader.rows_by_ids(
        "tbl_samples",
        select="sample_id,site_id",
        filter_field="site_id",
        ids=[1],
        order_by=("sample_id",),
    ) == [{"sample_id": "9007199254740993", "site_id": "1"}]
    assert source == {"sample_id": "9007199254740993", "site_id": "1"}


@pytest.mark.parametrize(
    "identifier", [True, 1.9, 1.0, float("inf"), float("nan"), 0, -1]
)
def test_mapping_reader_refuses_coerced_request_identities(identifier: object) -> None:
    reader = MappingSeadTableReader({"tbl_sites": [{"site_id": 1}]})
    with pytest.raises(ValueError):
        reader.rows_by_ids(
            "tbl_sites",
            select="site_id",
            filter_field="site_id",
            ids=cast(list[int], [identifier]),
            order_by=("site_id",),
        )


@pytest.mark.parametrize(
    "identifier", [True, 1.9, 1.0, float("inf"), float("nan"), 0, -1]
)
def test_mapping_reader_refuses_nonnull_invalid_source_foreign_keys(
    identifier: object,
) -> None:
    reader = MappingSeadTableReader(
        {"tbl_samples": [{"sample_id": 10, "site_id": identifier}]}
    )
    with pytest.raises(ValueError):
        reader.rows_by_ids(
            "tbl_samples",
            select="sample_id,site_id",
            filter_field="site_id",
            ids=[1],
            order_by=("sample_id",),
        )


def test_mixed_native_and_string_keys_sort_numerically_without_merging() -> None:
    reader = MappingSeadTableReader(
        {
            "tbl_samples": [
                {"sample_id": "9007199254740993", "site_id": 1},
                {"sample_id": 9007199254740992, "site_id": "1"},
                {"sample_id": 7, "site_id": None},
            ]
        }
    )
    assert reader.rows_by_ids(
        "tbl_samples",
        select="sample_id,site_id",
        filter_field="site_id",
        ids=[1],
        order_by=("sample_id",),
    ) == [
        {"sample_id": 9007199254740992, "site_id": "1"},
        {"sample_id": "9007199254740993", "site_id": 1},
    ]


if __name__ == "__main__":
    unittest.main()
