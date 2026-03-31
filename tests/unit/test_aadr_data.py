from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from bijux_pollenomics.data_downloader.sources.aadr import (
    dataset_directory_name,
    download_aadr_anno_files,
    resolve_anno_files,
)


class AadrDataTests(unittest.TestCase):
    def test_dataset_directory_name_maps_known_public_datasets(self) -> None:
        self.assertEqual(dataset_directory_name("v62.0_1240k_public.anno"), "1240k")
        self.assertEqual(dataset_directory_name("v62.0_HO_public.anno"), "ho")

    def test_resolve_anno_files_filters_to_requested_version(self) -> None:
        metadata = {
            "data": [
                {
                    "files": [
                        {"dataFile": {"filename": "v62.0_1240k_public.anno", "id": 101}},
                        {"dataFile": {"filename": "v62.0_HO_public.anno", "id": 102}},
                        {"dataFile": {"filename": "v62.0_HO_public.geno", "id": 104}},
                    ]
                },
                {
                    "files": [
                        {"dataFile": {"filename": "v61.0_HO_public.anno", "id": 103}},
                    ]
                },
            ]
        }

        files = resolve_anno_files(version="v62.0", metadata=metadata)

        self.assertEqual(
            [(item.dataset_name, item.filename, item.file_id) for item in files],
            [
                ("1240k", "v62.0_1240k_public.anno", 101),
                ("ho", "v62.0_HO_public.anno", 102),
            ],
        )

    def test_resolve_anno_files_finds_historical_release_outside_latest_version(self) -> None:
        metadata = {
            "data": [
                {
                    "files": [
                        {"dataFile": {"filename": "v62.0_1240k_public.anno", "id": 201}},
                    ]
                },
                {
                    "files": [
                        {"dataFile": {"filename": "v54.1_HO_public.anno", "id": 301}},
                        {"dataFile": {"filename": "v54.1_1240k_public.anno", "id": 302}},
                    ]
                },
            ]
        }

        files = resolve_anno_files(version="v54.1", metadata=metadata)

        self.assertEqual(
            [(item.dataset_name, item.filename, item.file_id) for item in files],
            [
                ("1240k", "v54.1_1240k_public.anno", 302),
                ("ho", "v54.1_HO_public.anno", 301),
            ],
        )

    def test_download_aadr_anno_files_writes_release_manifest(self) -> None:
        first_payload = b"first"
        second_payload = b"second"
        metadata = {
            "data": [
                {
                    "versionNumber": 9,
                    "versionMinorNumber": 1,
                    "releaseTime": "2024-09-17T04:23:58Z",
                    "lastUpdateTime": "2024-09-17T04:23:58Z",
                    "files": [
                        {
                            "dataFile": {
                                "filename": "v62.0_1240k_public.anno",
                                "id": 101,
                                "md5": "8b04d5e3775d298e78455efc5ca404d5",
                                "filesize": len(first_payload),
                            }
                        },
                        {
                            "dataFile": {
                                "filename": "v62.0_HO_public.anno",
                                "id": 102,
                                "md5": "a9f0e61a137d86aa9db53465e0801612",
                                "filesize": len(second_payload),
                            }
                        },
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            with patch(
                "bijux_pollenomics.data_downloader.sources.aadr.fetch_release_history_metadata",
                return_value=metadata,
            ), patch(
                "bijux_pollenomics.data_downloader.sources.aadr.fetch_binary",
                side_effect=[first_payload, second_payload],
            ):
                report = download_aadr_anno_files(output_root, "v62.0")

            manifest = json.loads(report.manifest_path.read_text(encoding="utf-8"))

        self.assertEqual(report.downloaded_files[0].name, "v62.0_1240k_public.anno")
        self.assertEqual(report.downloaded_files[1].name, "v62.0_HO_public.anno")
        self.assertEqual(manifest["requested_version"], "v62.0")
        self.assertEqual(manifest["dataverse_version_number"], 9)
        self.assertEqual(
            [item["dataset_name"] for item in manifest["anno_files"]],
            ["1240k", "ho"],
        )
        self.assertEqual(
            manifest["downloaded_files"],
            ["1240k/v62.0_1240k_public.anno", "ho/v62.0_HO_public.anno"],
        )

    def test_download_aadr_anno_files_rejects_checksum_mismatch(self) -> None:
        metadata = {
            "data": [
                {
                    "files": [
                        {
                            "dataFile": {
                                "filename": "v62.0_HO_public.anno",
                                "id": 102,
                                "md5": "ffffffffffffffffffffffffffffffff",
                                "filesize": 6,
                            }
                        }
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp)
            with patch(
                "bijux_pollenomics.data_downloader.sources.aadr.fetch_release_history_metadata",
                return_value=metadata,
            ), patch(
                "bijux_pollenomics.data_downloader.sources.aadr.fetch_binary",
                return_value=b"second",
            ):
                with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                    download_aadr_anno_files(output_root, "v62.0")


if __name__ == "__main__":
    unittest.main()
