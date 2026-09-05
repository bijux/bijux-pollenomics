from __future__ import annotations

import unittest
from unittest.mock import patch

from bijux_pollenomics.collection.sources.sead.catalog.fields import (
    populate_sead_site_inventory_fields,
)
from bijux_pollenomics.collection.sources.sead.evidence.normalization import (
    normalize_sead_chronology_claims,
)


class SeadChronologyClaimTests(unittest.TestCase):
    def test_claims_remain_source_rows_with_entity_lineage(self) -> None:
        claims = normalize_sead_chronology_claims(
            [
                {
                    "site_id": 6468,
                    "site_uuid": "uuid-6468",
                    "dating_range_rows": [
                        {
                            "analysis_dating_range_id": 34,
                            "analysis_value_id": 35,
                            "analysis_entity_id": 30,
                            "physical_sample_id": 20,
                            "sample_group_id": 10,
                            "dataset_id": 40,
                            "age_type": "AD",
                            "low_value": 1950,
                            "high_value": None,
                            "time_start_bp": 0,
                            "time_end_bp": 0,
                        },
                        {
                            "analysis_dating_range_id": 36,
                            "analysis_value_id": 37,
                            "analysis_entity_id": 31,
                            "physical_sample_id": 21,
                            "sample_group_id": 10,
                            "dataset_id": 41,
                            "age_type": "AD",
                            "low_value": 1750,
                            "high_value": 1700,
                            "time_start_bp": 200,
                            "time_end_bp": 250,
                        },
                        {
                            "analysis_dating_range_id": 38,
                            "analysis_value_id": 39,
                            "analysis_entity_id": 31,
                            "physical_sample_id": 21,
                            "sample_group_id": 10,
                            "dataset_id": 41,
                            "age_type": "AD",
                            "low_value": 1750,
                            "high_value": 1700,
                            "time_start_bp": 200,
                            "time_end_bp": 250,
                        },
                    ],
                }
            ],
            provenance_record_id="sead-capture-2026-09-04",
            build_id="build-123",
        )

        self.assertEqual(len(claims), 3)
        self.assertEqual(
            [claim["chronology_claim_id"] for claim in claims],
            [
                "sead:uuid-6468:dating_range:34",
                "sead:uuid-6468:dating_range:36",
                "sead:uuid-6468:dating_range:38",
            ],
        )
        self.assertEqual(claims[1]["younger_bp"], claims[2]["younger_bp"])
        self.assertEqual(claims[1]["older_bp"], claims[2]["older_bp"])
        first = claims[0]
        self.assertEqual(first["subject_type"], "analysis_entity")
        self.assertEqual(first["subject_id"], "30")
        self.assertEqual(first["sample_group_id"], 10)
        self.assertEqual(first["physical_sample_id"], 20)
        self.assertEqual(first["dataset_id"], 40)
        self.assertEqual(first["younger_bp"], 0)
        self.assertEqual(first["older_bp"], 0)
        self.assertEqual(first["comparability_status"], "comparable")
        self.assertEqual(first["chronology_eligibility"], "eligible")
        self.assertEqual(first["propagation_eligibility"], "refused")
        self.assertEqual(
            first["propagation_reason_codes"],
            ["observation_link_not_materialized"],
        )
        self.assertEqual(first["publication_role"], "chronology_display_only")
        self.assertEqual(first["reason_codes"], [])
        self.assertEqual(
            [part["table"] for part in first["source_relation_path"]],
            [
                "tbl_sites",
                "tbl_sample_groups",
                "tbl_physical_samples",
                "tbl_analysis_entities",
                "tbl_datasets",
                "tbl_analysis_values",
                "tbl_analysis_dating_ranges",
            ],
        )

    def test_context_and_ungoverned_age_types_cannot_become_numeric(self) -> None:
        claims = normalize_sead_chronology_claims(
            [
                {
                    "site_id": 6468,
                    "site_uuid": "uuid-6468",
                    "relative_period_rows": [
                        {
                            "relative_date_id": 45,
                            "analysis_entity_id": 30,
                            "relative_age_label": "Neolithic",
                            "time_start_bp": 4000,
                            "time_end_bp": 6000,
                        }
                    ],
                    "dating_range_rows": [
                        {
                            "analysis_dating_range_id": 34,
                            "analysis_entity_id": 30,
                            "age_type": "possibly cal-ish BP",
                            "time_start_bp": 200,
                            "time_end_bp": 800,
                        }
                    ],
                    "geochronology_rows": [
                        {
                            "geochron_id": 32,
                            "analysis_entity_id": 30,
                            "age": 1200,
                            "time_start_bp": 1150,
                            "time_end_bp": 1250,
                        }
                    ],
                }
            ],
            provenance_record_id="sead-capture-2026-09-04",
            build_id="build-123",
        )

        by_type = {claim["claim_type"]: claim for claim in claims}
        relative = by_type["relative_period"]
        self.assertEqual(relative["comparability_status"], "context_only")
        self.assertIsNone(relative["younger_bp"])
        self.assertIsNone(relative["older_bp"])
        self.assertIn(
            "relative_period_requires_governed_mapping", relative["reason_codes"]
        )
        unsupported = by_type["dating_range"]
        self.assertEqual(unsupported["comparability_status"], "unresolved")
        self.assertIsNone(unsupported["younger_bp"])
        self.assertIn("age_type_not_governed", unsupported["reason_codes"])
        geochronology = by_type["geochronology"]
        self.assertEqual(geochronology["comparability_status"], "context_only")
        self.assertIn(
            "geochronology_calibration_posture_unknown",
            geochronology["reason_codes"],
        )

    def test_missing_entity_lineage_is_reason_coded(self) -> None:
        claim = normalize_sead_chronology_claims(
            [
                {
                    "site_id": 6468,
                    "site_uuid": "uuid-6468",
                    "dating_range_rows": [
                        {
                            "analysis_dating_range_id": 34,
                            "analysis_value_id": 35,
                            "age_type": "AD",
                            "time_start_bp": 196,
                            "time_end_bp": 196,
                        }
                    ],
                }
            ],
            provenance_record_id="sead-capture-2026-09-04",
            build_id="build-123",
        )[0]

        self.assertEqual(claim["subject_type"], "analysis_value")
        self.assertEqual(claim["comparability_status"], "comparable")
        self.assertEqual(claim["chronology_eligibility"], "refused")
        self.assertEqual(claim["propagation_eligibility"], "refused")
        self.assertIn("missing_analysis_entity_lineage", claim["reason_codes"])

    def test_invalid_numeric_endpoints_are_refused_without_crashing(self) -> None:
        rows = [
            {
                "site_id": 6468,
                "site_uuid": "uuid-6468",
                "dating_range_rows": [
                    {
                        "analysis_dating_range_id": record_id,
                        "analysis_entity_id": 30,
                        "age_type": "cal BP",
                        "time_start_bp": start,
                        "time_end_bp": end,
                    }
                    for record_id, start, end in (
                        (1, -1, 10),
                        (2, float("nan"), 10),
                        (3, float("inf"), 10),
                        (4, False, 10),
                    )
                ],
            }
        ]

        claims = normalize_sead_chronology_claims(
            rows,
            provenance_record_id="sead-capture-2026-09-04",
            build_id="build-123",
        )

        self.assertEqual(len(claims), 4)
        self.assertEqual(
            [claim["comparability_status"] for claim in claims],
            ["refused", "refused", "refused", "refused"],
        )
        self.assertIn("negative_bp", claims[0]["reason_codes"])
        self.assertIn(
            "missing_or_invalid_canonical_interval", claims[1]["reason_codes"]
        )
        self.assertIn(
            "missing_or_invalid_canonical_interval", claims[2]["reason_codes"]
        )
        self.assertIn(
            "missing_or_invalid_canonical_interval", claims[3]["reason_codes"]
        )

    def test_claims_require_build_and_provenance_identity(self) -> None:
        with self.assertRaisesRegex(ValueError, "provenance record ID"):
            normalize_sead_chronology_claims(
                [], provenance_record_id="", build_id="build-123"
            )
        with self.assertRaisesRegex(ValueError, "build ID"):
            normalize_sead_chronology_claims(
                [], provenance_record_id="capture-123", build_id=""
            )


class SeadChronologyAcquisitionTests(unittest.TestCase):
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

        with (
            patch(
                "bijux_pollenomics.collection.sources.sead.catalog.fields.fetch_sead_rows_by_ids",
                side_effect=rows_by_ids,
            ),
            patch(
                "bijux_pollenomics.collection.sources.sead.catalog.fields.fetch_sead_rows",
                side_effect=all_rows,
            ),
        ):
            summary = populate_sead_site_inventory_fields(
                site_rows, fetch_json_fn=lambda *_: []
            )

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
