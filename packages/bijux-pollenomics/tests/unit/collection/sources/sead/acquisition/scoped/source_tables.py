"""Relational source-table fixture for scoped SEAD acquisition."""

from __future__ import annotations


def _source_tables() -> dict[str, list[dict[str, object]]]:
    sites = [
        {
            "site_id": site_id,
            "site_name": f"site-{site_id}",
            "national_site_identifier": f"national-{site_id}",
            "latitude_dd": 55.0 + site_id,
            "longitude_dd": 10.0 + site_id,
            "altitude": site_id,
            "site_description": f"description-{site_id}",
            "site_uuid": f"uuid-{site_id}",
        }
        for site_id in range(1, 6)
    ]
    sites.append(
        {
            "site_id": 99,
            "site_name": "outside-bbox",
            "national_site_identifier": "outside",
            "latitude_dd": 40.0,
            "longitude_dd": 40.0,
            "altitude": 0,
            "site_description": "outside",
            "site_uuid": "uuid-99",
        }
    )
    return {
        "tbl_sites": sites,
        "tbl_sample_groups": [
            {"sample_group_id": 11, "site_id": 1, "sample_group_name": "g1"},
            {"sample_group_id": 12, "site_id": 2, "sample_group_name": "g2"},
            {"sample_group_id": 13, "site_id": 3, "sample_group_name": "g3"},
            {"sample_group_id": 15, "site_id": 5, "sample_group_name": "excluded"},
            {"sample_group_id": 999, "site_id": 999, "sample_group_name": "global"},
        ],
        "tbl_physical_samples": [
            {"physical_sample_id": 21, "sample_group_id": 11},
            {"physical_sample_id": 22, "sample_group_id": 12},
            {"physical_sample_id": 23, "sample_group_id": 13},
            {"physical_sample_id": 25, "sample_group_id": 15},
            {"physical_sample_id": 999, "sample_group_id": 999},
        ],
        "tbl_analysis_entities": [
            {"analysis_entity_id": 31, "physical_sample_id": 21, "dataset_id": 101},
            {"analysis_entity_id": 32, "physical_sample_id": 22, "dataset_id": 102},
            {"analysis_entity_id": 33, "physical_sample_id": 23, "dataset_id": 103},
            {"analysis_entity_id": 35, "physical_sample_id": 25, "dataset_id": 105},
            {"analysis_entity_id": 999, "physical_sample_id": 999, "dataset_id": 999},
        ],
        "tbl_analysis_entity_ages": [
            {
                "analysis_entity_age_id": 41,
                "analysis_entity_id": 31,
                "age": 100,
                "age_older": 110,
                "age_younger": 90,
                "chronology_id": 1,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
            {
                "analysis_entity_age_id": 42,
                "analysis_entity_id": 32,
                "age": 200,
                "age_older": 210,
                "age_younger": 190,
                "chronology_id": 2,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
            {
                "analysis_entity_age_id": 43,
                "analysis_entity_id": 33,
                "age": 300,
                "age_older": 310,
                "age_younger": 290,
                "chronology_id": 3,
                "dating_specifier": "fixture",
                "age_range": 20,
            },
        ],
        "tbl_geochronology": [
            {
                "geochron_id": 51,
                "analysis_entity_id": 31,
                "dating_lab_id": 1,
                "lab_number": "lab-1",
                "age": 100,
                "error_older": 10,
                "error_younger": 10,
                "notes": None,
                "dating_uncertainty_id": 201,
            }
        ],
        "tbl_dendro_dates": [
            {
                "dendro_date_id": 61,
                "analysis_entity_id": 32,
                "age_older": 210,
                "age_younger": 190,
                "age_type_id": 301,
                "dating_uncertainty_id": 201,
                "dendro_lookup_id": 1,
                "season_id": 1,
                "age_range": 20,
            }
        ],
        "tbl_analysis_values": [
            {"analysis_value_id": 71, "analysis_entity_id": 31},
            {"analysis_value_id": 72, "analysis_entity_id": 32},
            {"analysis_value_id": 73, "analysis_entity_id": 33},
        ],
        "tbl_analysis_dating_ranges": [
            {
                "analysis_dating_range_id": 81,
                "analysis_value_id": 71,
                "low_value": 90,
                "high_value": 110,
                "age_type_id": 301,
                "dating_uncertainty_id": 201,
                "low_qualifier": None,
                "high_qualifier": None,
                "low_is_uncertain": False,
                "high_is_uncertain": False,
            },
            {
                "analysis_dating_range_id": 82,
                "analysis_value_id": 72,
                "low_value": 190,
                "high_value": 210,
                "age_type_id": 301,
                "dating_uncertainty_id": None,
                "low_qualifier": None,
                "high_qualifier": None,
                "low_is_uncertain": False,
                "high_is_uncertain": False,
            },
        ],
        "tbl_age_types": [
            {"age_type_id": 301, "age_type": "Calendar BP", "description": "fixture"}
        ],
        "tbl_relative_dates": [
            {
                "relative_date_id": 91,
                "analysis_entity_id": 33,
                "relative_age_id": 401,
                "dating_uncertainty_id": 201,
                "method_id": 501,
                "notes": "fixture",
            }
        ],
        "tbl_relative_ages": [
            {
                "relative_age_id": 401,
                "relative_age_name": "Period A",
                "description": "fixture",
                "abbreviation": "PA",
                "cal_age_older": None,
                "cal_age_younger": None,
                "c14_age_older": None,
                "c14_age_younger": None,
            }
        ],
        "tbl_relative_age_refs": [
            {"relative_age_ref_id": 601, "relative_age_id": 401, "biblio_id": 701}
        ],
        "tbl_dating_uncertainty": [
            {
                "dating_uncertainty_id": 201,
                "uncertainty": "reported",
                "description": "fixture",
            }
        ],
        "tbl_methods": [
            {
                "method_id": 501,
                "method_name": "stratigraphy",
                "method_abbrev_or_alt_name": "strat",
                "description": "fixture",
            }
        ],
        "tbl_datasets": [
            {"dataset_id": 101, "dataset_name": "d1", "biblio_id": 701},
            {"dataset_id": 102, "dataset_name": "d2", "biblio_id": 701},
            {"dataset_id": 103, "dataset_name": "d3", "biblio_id": None},
        ],
        "tbl_site_references": [
            {"site_reference_id": 801, "site_id": 1, "biblio_id": 701}
        ],
        "tbl_sample_group_references": [
            {"sample_group_reference_id": 901, "sample_group_id": 11, "biblio_id": 701}
        ],
        "tbl_biblio": [
            {
                "biblio_id": 701,
                "title": "Fixture",
                "full_reference": "Fixture reference",
                "year": 2026,
                "doi": "10.0000/fixture",
                "url": "https://example.invalid/fixture",
            }
        ],
    }
