from __future__ import annotations

import unittest
from unittest.mock import Mock

from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.service import (
    populate_sead_site_inventory_from_reader,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.source_data.table_readers import (
    SeadTableReader,
)
from bijux_pollenomics.collection.sources.sead.catalog.site_inventory.temporal import (
    _ce_year_to_bp,
)


class SeadChronologyAcquisitionTests(unittest.TestCase):
    def test_common_era_conversion_preserves_post_1950_signed_bp(self) -> None:
        self.assertEqual(_ce_year_to_bp(1950), 0)
        self.assertEqual(_ce_year_to_bp(2004), -54)

    def test_acquisition_preserves_the_entity_parent_chain_on_each_claim(self) -> None:
        site_rows = [
            {"site_id": 6468, "site_uuid": "uuid-6468"},
            {"site_id": 6469, "site_uuid": "uuid-6469"},
            {"site_id": 6470, "site_uuid": "uuid-6470"},
        ]

        def rows_by_ids(table_name: str, **_: object) -> list[dict[str, object]]:
            return {
                "tbl_sample_groups": [
                    {"sample_group_id": 10, "site_id": 6468},
                    {"sample_group_id": 11, "site_id": 6469},
                ],
                "tbl_physical_samples": [
                    {"physical_sample_id": 20, "sample_group_id": 10},
                    {"physical_sample_id": 21, "sample_group_id": 11},
                ],
                "tbl_analysis_entities": [
                    {
                        "analysis_entity_id": 30,
                        "physical_sample_id": 20,
                        "dataset_id": 40,
                    },
                    {
                        "analysis_entity_id": 31,
                        "physical_sample_id": 21,
                        "dataset_id": 41,
                    },
                ],
                "tbl_analysis_values": [
                    {"analysis_value_id": 35, "analysis_entity_id": 30}
                ],
                "tbl_age_types": [
                    {"age_type_id": 2, "age_type": "AD", "description": ""}
                ],
                "tbl_dating_uncertainty": [],
                "tbl_relative_ages": [
                    {
                        "relative_age_id": 80,
                        "relative_age_name": "Neolithic",
                        "cal_age_younger": 4000,
                        "cal_age_older": 6000,
                    }
                ],
                "tbl_methods": [],
                "tbl_datasets": [
                    {"dataset_id": 40, "dataset_name": "Pollen", "biblio_id": None},
                    {
                        "dataset_id": 41,
                        "dataset_name": "Archaeology",
                        "biblio_id": None,
                    },
                ],
                "tbl_site_references": [],
                "tbl_sample_group_references": [],
                "tbl_relative_age_refs": [],
                "tbl_biblio": [],
            }[table_name]

        def all_rows(table_name: str, **_: object) -> list[dict[str, object]]:
            return {
                "tbl_analysis_entity_ages": [
                    {
                        "analysis_entity_age_id": 31,
                        "analysis_entity_id": 30,
                        "age": 500,
                    }
                ],
                "tbl_geochronology": [
                    {"geochron_id": 32, "analysis_entity_id": 30, "age": 1200}
                ],
                "tbl_dendro_dates": [
                    {
                        "dendro_date_id": 33,
                        "analysis_entity_id": 30,
                        "age_older": 1754,
                        "age_younger": None,
                        "age_type_id": 2,
                    }
                ],
                "tbl_analysis_dating_ranges": [
                    {
                        "analysis_dating_range_id": 34,
                        "analysis_value_id": 35,
                        "low_value": 1754,
                        "high_value": None,
                        "age_type_id": 2,
                    }
                ],
                "tbl_relative_dates": [
                    {
                        "relative_date_id": 45,
                        "analysis_entity_id": 30,
                        "relative_age_id": 80,
                    },
                    {
                        "relative_date_id": 46,
                        "analysis_entity_id": 31,
                        "relative_age_id": 80,
                    },
                ],
            }[table_name]

        reader = Mock(spec=SeadTableReader)
        reader.rows_by_ids.side_effect = rows_by_ids
        reader.all_rows.side_effect = all_rows
        summary = populate_sead_site_inventory_from_reader(site_rows, reader=reader)

        for row_key in (
            "dating_range_rows",
            "relative_period_rows",
            "analysis_entity_age_rows",
            "geochronology_rows",
            "dendro_date_rows",
        ):
            claim_row = site_rows[0][row_key][0]
            self.assertEqual(claim_row["sample_group_id"], 10)
            self.assertEqual(claim_row["physical_sample_id"], 20)
            self.assertEqual(claim_row["analysis_entity_id"], 30)
            self.assertEqual(claim_row["dataset_id"], 40)

        contextual_claim = site_rows[1]["relative_period_rows"][0]
        self.assertEqual(contextual_claim["sample_group_id"], 11)
        self.assertEqual(contextual_claim["physical_sample_id"], 21)
        self.assertEqual(contextual_claim["analysis_entity_id"], 31)
        self.assertEqual(contextual_claim["dataset_id"], 41)
        self.assertEqual(site_rows[0]["dating_range_rows"][0]["age_type_id"], 2)
        self.assertEqual(site_rows[0]["dendro_date_rows"][0]["age_type_id"], 2)
        self.assertEqual(summary["numeric_interval_row_count"], 1)
        self.assertEqual(summary["contextual_only_site_count"], 1)
        self.assertEqual(summary["unresolved_site_count"], 1)


if __name__ == "__main__":
    unittest.main()
