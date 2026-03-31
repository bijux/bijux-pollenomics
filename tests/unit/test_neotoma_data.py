from __future__ import annotations

import json
import tempfile
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from bijux_pollenomics.data_downloader.neotoma import (
    build_neotoma_download_archive_parts,
    build_neotoma_site_snapshot_rows,
    collect_neotoma_data,
    fetch_neotoma_api_rows,
    fetch_neotoma_dataset_inventory_rows,
    fetch_neotoma_dataset_download_rows,
    fetch_neotoma_pollen_rows,
    normalize_neotoma_rows,
)


class NeotomaDataTests(unittest.TestCase):
    def test_build_neotoma_download_archive_parts_splits_rows_into_stable_part_files(self) -> None:
        rows = [
            {"site": {"siteid": 20, "collectionunit": {"dataset": {"datasetid": 201}}}},
            {"site": {"siteid": 21, "collectionunit": {"dataset": {"datasetid": 202}}}},
            {"site": {"siteid": 22, "collectionunit": {"dataset": {"datasetid": 203}}}},
        ]

        parts = build_neotoma_download_archive_parts(rows, rows_per_part=2)

        self.assertEqual([part["filename"] for part in parts], ["part-001.json", "part-002.json"])
        self.assertEqual([part["row_count"] for part in parts], [2, 1])
        self.assertEqual(parts[0]["downloaded_dataset_ids"], [201, 202])
        self.assertEqual(parts[1]["downloaded_dataset_ids"], [203])

    def test_fetch_neotoma_api_rows_retries_retryable_http_errors(self) -> None:
        retry_error = HTTPError(
            url="https://api.neotomadb.org/v2.0/data/datasets",
            code=503,
            msg="Service Unavailable",
            hdrs=None,
            fp=BytesIO(b"retry later"),
        )

        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_json",
            side_effect=[
                retry_error,
                {"data": [{"site": {"siteid": 20, "datasets": [{"datasetid": 201}]}}]},
                {"data": []},
            ],
        ):
            rows = fetch_neotoma_api_rows("datasets")

        self.assertEqual(len(rows), 1)

    def test_fetch_neotoma_api_rows_retries_retryable_timeouts(self) -> None:
        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_json",
            side_effect=[
                TimeoutError("read timed out"),
                {"data": [{"site": {"siteid": 20, "datasets": [{"datasetid": 201}]}}]},
                {"data": []},
            ],
        ):
            rows = fetch_neotoma_api_rows("datasets")

        self.assertEqual(len(rows), 1)

    def test_fetch_neotoma_dataset_inventory_rows_flattens_site_collectionunits(self) -> None:
        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_json",
            return_value={
                "data": [
                    {
                        "siteid": 20,
                        "sitename": "Agerods Mosse",
                        "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                        "collectionunits": [
                            {
                                "collectionunitid": 1,
                                "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                            },
                            {
                                "collectionunitid": 2,
                                "datasets": [{"datasetid": 202, "datasettype": "pollen"}],
                            },
                        ],
                    }
                ]
            },
        ):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["site"]["siteid"], 20)
        self.assertEqual(
            [dataset["datasetid"] for dataset in rows[0]["site"]["datasets"]],
            [201, 202],
        )

    def test_fetch_neotoma_dataset_inventory_rows_uses_wide_bbox_inventory_limit(self) -> None:
        observed_params: list[dict[str, str]] = []

        def fake_fetch_json(url: str, params: dict[str, str] | None = None, **_: object) -> object:
            self.assertEqual(url, "https://api.neotomadb.org/v2.0/data/sites")
            self.assertIsNotNone(params)
            observed_params.append(dict(params or {}))
            return {
                "data": [
                    {
                        "siteid": 20,
                        "sitename": "Agerods Mosse",
                        "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                        "collectionunits": [
                            {
                                "collectionunitid": 1,
                                "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                            }
                        ],
                    }
                ]
            }

        with patch("bijux_pollenomics.data_downloader.neotoma.fetch_json", side_effect=fake_fetch_json):
            rows = fetch_neotoma_dataset_inventory_rows((4.0, 54.0, 35.0, 72.0))

        self.assertEqual(len(rows), 1)
        self.assertEqual(len(observed_params), 1)
        self.assertEqual(observed_params[0]["limit"], "400")
        self.assertEqual(observed_params[0]["offset"], "0")
        self.assertEqual(observed_params[0]["datasettype"], "pollen")

    def test_collect_neotoma_data_preserves_full_inventory_and_retained_subset(self) -> None:
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
        download_rows = []
        rows = []

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "neotoma"
            with patch(
                "bijux_pollenomics.data_downloader.neotoma.fetch_neotoma_dataset_inventory_rows",
                return_value=inventory_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.filter_neotoma_dataset_inventory_rows",
                return_value=matched_inventory_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.extract_neotoma_dataset_ids",
                return_value=[201],
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.fetch_neotoma_dataset_download_rows",
                return_value=download_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.build_neotoma_site_rows_from_downloads",
                return_value=rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.normalize_neotoma_rows",
                return_value=[],
            ):
                collect_neotoma_data(
                    output_root=output_root,
                    country_boundaries={"Sweden": {"features": []}},
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            inventory_payload = json.loads((output_root / "raw" / "neotoma_pollen_dataset_inventory.json").read_text(encoding="utf-8"))

        self.assertEqual(inventory_payload["queried_row_count"], 2)
        self.assertEqual(inventory_payload["retained_row_count"], 1)
        self.assertEqual(inventory_payload["retained_dataset_count"], 1)
        self.assertEqual(inventory_payload["endpoint"], "https://api.neotomadb.org/v2.0/data/sites")
        self.assertEqual([item["site"]["siteid"] for item in inventory_payload["rows"]], [20, 30])
        self.assertEqual([item["site"]["siteid"] for item in inventory_payload["retained_rows"]], [20])

    def test_fetch_neotoma_pollen_rows_hydrates_full_dataset_downloads(self) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[10.0, 55.0], [25.0, 55.0], [25.0, 70.0], [10.0, 70.0], [10.0, 55.0]]
                            ],
                        }
                    }
                ]
            }
        }

        def fake_fetch_json(url: str, params: dict[str, str] | None = None, **_: object) -> object:
            if url.endswith("/sites"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "siteid": 20,
                            "sitename": "Ageröds Mosse",
                            "sitedescription": "",
                            "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                            "altitude": 10,
                            "collectionunits": [
                                {
                                    "collectionunitid": 1,
                                    "collectionunit": "Core A",
                                    "handle": "CORE-A",
                                    "collectionunittype": "Core",
                                    "datasets": [{"datasetid": 201, "datasettype": "pollen"}],
                                },
                                {
                                    "collectionunitid": 2,
                                    "collectionunit": "Core B",
                                    "handle": "CORE-B",
                                    "collectionunittype": "Core",
                                    "datasets": [{"datasetid": 202, "datasettype": "pollen"}],
                                },
                            ],
                        },
                        {
                            "siteid": 30,
                            "sitename": "Outside Nordic",
                            "sitedescription": "",
                            "geography": '{"type":"Point","coordinates":[40.0,60.0]}',
                            "altitude": 25,
                            "collectionunits": [
                                {
                                    "collectionunitid": 3,
                                    "collectionunit": "Core C",
                                    "handle": "CORE-C",
                                    "collectionunittype": "Core",
                                    "datasets": [{"datasetid": 301, "datasettype": "pollen"}],
                                }
                            ],
                        },
                    ],
                }
            if url.endswith("/downloads/201"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "chronologies": [{"chronologyid": 7001}],
                                "defaultchronology": 7001,
                                "collectionunit": {
                                    "collectionunitid": 1,
                                    "collectionunit": "Core A",
                                    "handle": "CORE-A",
                                    "collunittype": "Core",
                                    "dataset": {
                                        "datasetid": 201,
                                        "datasettype": "pollen",
                                        "database": "European Pollen Database",
                                        "agerange": [{"units": "Calibrated radiocarbon years BP", "ageold": 2000, "ageyoung": 50}],
                                        "samples": [
                                            {
                                                "sampleid": 9001,
                                                "analysisunitid": 9101,
                                                "ages": [{"agetype": "Calibrated radiocarbon years BP", "ageolder": 2100, "ageyounger": 30}],
                                                "datum": [
                                                    {"taxonid": 1, "variablename": "Betula"},
                                                    {"taxonid": 2, "variablename": "Pinus"},
                                                ],
                                            }
                                        ],
                                    },
                                },
                            },
                        }
                    ],
                }
            if url.endswith("/downloads/202"):
                return {
                    "status": "success",
                    "message": "ok",
                    "data": [
                        {
                            "site": {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "altitude": 10,
                                "chronologies": [{"chronologyid": 7002}],
                                "defaultchronology": 7002,
                                "collectionunit": {
                                    "collectionunitid": 2,
                                    "collectionunit": "Core B",
                                    "handle": "CORE-B",
                                    "collunittype": "Core",
                                    "dataset": {
                                        "datasetid": 202,
                                        "datasettype": "pollen",
                                        "database": "European Pollen Database",
                                        "agerange": [{"units": "Calibrated radiocarbon years BP", "ageold": 3500, "ageyoung": 200}],
                                        "samples": [
                                            {
                                                "sampleid": 9002,
                                                "analysisunitid": 9102,
                                                "ages": [{"agetype": "Calibrated radiocarbon years BP", "ageolder": 3600, "ageyounger": 180}],
                                                "datum": [
                                                    {"taxonid": 3, "variablename": "Alnus"},
                                                ],
                                            }
                                        ],
                                    },
                                },
                            },
                        },
                    ],
                }

            raise AssertionError(f"Unexpected URL: {url}")

        with patch("bijux_pollenomics.data_downloader.neotoma.fetch_json", side_effect=fake_fetch_json):
            rows = fetch_neotoma_pollen_rows(
                bbox=(4.0, 54.0, 35.0, 72.0),
                country_boundaries=country_boundaries,
            )

        self.assertEqual([row["siteid"] for row in rows], [20])
        row_by_id = {row["siteid"]: row for row in rows}

        self.assertEqual(row_by_id[20]["sitename"], "Ageröds Mosse")
        self.assertEqual(row_by_id[20]["dataset_count"], 2)
        self.assertEqual(row_by_id[20]["sample_count"], 2)
        self.assertEqual(row_by_id[20]["chronology_count"], 2)
        self.assertEqual(row_by_id[20]["taxon_count"], 3)
        self.assertEqual(row_by_id[20]["databases"], ["European Pollen Database"])
        self.assertEqual(
            [unit["collectionunitid"] for unit in row_by_id[20]["collectionunits"]],
            [1, 2],
        )
        self.assertEqual(
            [
                dataset["datasetid"]
                for unit in row_by_id[20]["collectionunits"]
                for dataset in unit["datasets"]
            ],
            [201, 202],
        )

        records = normalize_neotoma_rows(rows, (4.0, 54.0, 35.0, 72.0), country_boundaries)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].time_start_bp, 30)
        self.assertEqual(records[0].time_end_bp, 3600)
        self.assertEqual(records[0].time_mean_bp, 1815)

    def test_fetch_neotoma_dataset_download_rows_rejects_missing_dataset_payloads(self) -> None:
        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_neotoma_dataset_download_row",
            side_effect=[
                [{"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}],
                [],
            ],
        ):
            with self.assertRaisesRegex(ValueError, "missing dataset IDs: 202"):
                fetch_neotoma_dataset_download_rows([201, 202])

    def test_fetch_neotoma_dataset_download_rows_retries_retryable_http_errors(self) -> None:
        retry_error = HTTPError(
            url="https://api.neotomadb.org/v2.0/data/downloads/201",
            code=429,
            msg="Too Many Requests",
            hdrs=None,
            fp=BytesIO(b"slow down"),
        )

        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_json",
            side_effect=[
                retry_error,
                {"data": [{"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}]},
            ],
        ):
            rows = fetch_neotoma_dataset_download_rows([201])

        self.assertEqual(len(rows), 1)

    def test_fetch_neotoma_dataset_download_rows_retries_retryable_timeouts(self) -> None:
        with patch(
            "bijux_pollenomics.data_downloader.neotoma.fetch_json",
            side_effect=[
                TimeoutError("read timed out"),
                {"data": [{"site": {"collectionunit": {"dataset": {"datasetid": 201}}}}]},
            ],
        ):
            rows = fetch_neotoma_dataset_download_rows([201])

        self.assertEqual(len(rows), 1)

    def test_normalize_neotoma_rows_recovers_coastal_nordic_sites_without_widening_scope(self) -> None:
        country_boundaries = {
            "Norway": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[10.0, 60.0], [13.0, 60.0], [13.0, 63.0], [10.0, 63.0], [10.0, 60.0]]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 1,
                "sitename": "Coastal site",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.05,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 10, "datasettype": "pollen"}],
                    }
                ],
            },
            {
                "siteid": 2,
                "sitename": "Too far away",
                "sitedescription": "",
                "geography": '{"type":"Point","coordinates":[13.5,61.5]}',
                "collectionunits": [
                    {
                        "datasets": [{"datasetid": 20, "datasettype": "pollen"}],
                    }
                ],
            },
        ]

        records = normalize_neotoma_rows(rows, (4.0, 54.0, 35.0, 72.0), country_boundaries)

        self.assertEqual([record.name for record in records], ["Coastal site"])
        self.assertEqual(records[0].country, "Norway")
        self.assertIsNone(records[0].time_start_bp)
        self.assertIsNone(records[0].time_end_bp)

    def test_build_neotoma_site_snapshot_rows_drops_nested_sample_payloads(self) -> None:
        rows = [
            {
                "siteid": 20,
                "sitename": "Snapshot test",
                "collectionunits": [
                    {
                        "collectionunitid": 1,
                        "datasets": [
                            {
                                "datasetid": 201,
                                "datasettype": "pollen",
                                "database": "European Pollen Database",
                                "chronologies": [{"chronologyid": 7001}],
                                "samples": [
                                    {
                                        "sampleid": 9001,
                                        "analysisunitid": 9101,
                                        "datum": [
                                            {"taxonid": 1, "variablename": "Betula"},
                                            {"taxonid": 2, "variablename": "Pinus"},
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        snapshot_rows = build_neotoma_site_snapshot_rows(rows)

        dataset = snapshot_rows[0]["collectionunits"][0]["datasets"][0]
        self.assertEqual(dataset["sample_count"], 1)
        self.assertEqual(dataset["analysis_unit_count"], 1)
        self.assertEqual(dataset["chronology_count"], 1)
        self.assertEqual(dataset["taxon_count"], 2)
        self.assertNotIn("samples", dataset)
        self.assertNotIn("chronologies", dataset)

    def test_normalize_neotoma_rows_derives_bp_interval_from_age_ranges(self) -> None:
        country_boundaries = {
            "Sweden": {
                "features": [
                    {
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [[10.0, 55.0], [25.0, 55.0], [25.0, 70.0], [10.0, 70.0], [10.0, 55.0]]
                            ],
                        }
                    }
                ]
            }
        }
        rows = [
            {
                "siteid": 20,
                "sitename": "Ageröds Mosse",
                "sitedescription": "Forested bog.",
                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                "collectionunits": [
                    {
                        "datasets": [
                            {
                                "datasetid": 201,
                                "datasettype": "pollen",
                                "database": "European Pollen Database",
                                "agerange": [
                                    {"units": "Radiocarbon years BP", "ageold": 3200, "ageyoung": 120},
                                    {"units": "Calibrated radiocarbon years BP", "ageold": 3600, "ageyoung": -20},
                                ],
                            }
                        ],
                    }
                ],
            }
        ]

        records = normalize_neotoma_rows(rows, (4.0, 54.0, 35.0, 72.0), country_boundaries)

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].time_start_bp, 0)
        self.assertEqual(records[0].time_end_bp, 3600)
        self.assertEqual(records[0].time_mean_bp, 1800)
        self.assertEqual(records[0].time_label, "0-3600 Calibrated radiocarbon years BP")

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
                    "collectionunit": {"dataset": {"datasetid": 201, "datasettype": "pollen"}},
                }
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "neotoma"
            with patch(
                "bijux_pollenomics.data_downloader.neotoma.fetch_neotoma_dataset_inventory_rows",
                return_value=inventory_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.filter_neotoma_dataset_inventory_rows",
                return_value=inventory_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.extract_neotoma_dataset_ids",
                return_value=[201],
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.fetch_neotoma_dataset_download_rows",
                return_value=download_rows,
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.build_neotoma_site_rows_from_downloads",
                return_value=[],
            ), patch(
                "bijux_pollenomics.data_downloader.neotoma.normalize_neotoma_rows",
                return_value=[],
            ):
                collect_neotoma_data(
                    output_root=output_root,
                    country_boundaries={"Sweden": {"features": []}},
                    bbox=(4.0, 54.0, 35.0, 72.0),
                )

            manifest_payload = json.loads(
                (output_root / "raw" / "neotoma_pollen_dataset_downloads" / "manifest.json").read_text(encoding="utf-8")
            )
            part_payload = json.loads(
                (output_root / "raw" / "neotoma_pollen_dataset_downloads" / "part-001.json").read_text(encoding="utf-8")
            )

        self.assertEqual(manifest_payload["requested_dataset_ids"], [201])
        self.assertEqual(manifest_payload["downloaded_dataset_ids"], [201])
        self.assertEqual(manifest_payload["part_count"], 1)
        self.assertEqual([part["filename"] for part in manifest_payload["parts"]], ["part-001.json"])
        self.assertEqual(part_payload["downloaded_dataset_ids"], [201])
        self.assertEqual(part_payload["row_count"], 1)


if __name__ == "__main__":
    unittest.main()
