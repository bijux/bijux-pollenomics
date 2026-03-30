from __future__ import annotations

import unittest

from bijux_pollenomics.data_downloader.aadr import dataset_directory_name, resolve_anno_files


class AadrDataTests(unittest.TestCase):
    def test_dataset_directory_name_maps_known_public_datasets(self) -> None:
        self.assertEqual(dataset_directory_name("v62.0_1240k_public.anno"), "1240k")
        self.assertEqual(dataset_directory_name("v62.0_HO_public.anno"), "ho")

    def test_resolve_anno_files_filters_to_requested_version(self) -> None:
        metadata = {
            "data": {
                "latestVersion": {
                    "files": [
                        {"dataFile": {"filename": "v62.0_1240k_public.anno", "id": 101}},
                        {"dataFile": {"filename": "v62.0_HO_public.anno", "id": 102}},
                        {"dataFile": {"filename": "v61.0_HO_public.anno", "id": 103}},
                        {"dataFile": {"filename": "v62.0_HO_public.geno", "id": 104}},
                    ]
                }
            }
        }

        files = resolve_anno_files(version="v62.0", metadata=metadata)

        self.assertEqual(
            [(item.dataset_name, item.filename, item.file_id) for item in files],
            [
                ("1240k", "v62.0_1240k_public.anno", 101),
                ("ho", "v62.0_HO_public.anno", 102),
            ],
        )


if __name__ == "__main__":
    unittest.main()
