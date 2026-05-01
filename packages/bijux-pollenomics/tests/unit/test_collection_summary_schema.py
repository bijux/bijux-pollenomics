from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.data_downloader.collection_summary_schema import (
    validate_collection_summary_file,
    validate_collection_summary_payload,
)


class CollectionSummarySchemaUnitTests(unittest.TestCase):
    def test_validate_collection_summary_payload_accepts_complete_payload(self) -> None:
        payload: dict[str, object] = {
            "generated_on": "2026-05-01",
            "output_root": "data",
            "version": "v62.0",
            "collected_sources": ["aadr"],
            "source_output_roots": {"aadr": "data/aadr", "aadr_version_dir": "data/aadr/v62.0"},
            "source_metadata": {"aadr": {"version": "v62.0"}},
            "source_hashes": {"aadr": {"snapshot_sha256": "a" * 64}},
            "source_provenance": {"aadr": {"version": "v62.0"}},
            "source_replacement_rules": {"aadr": {"refresh_mode": "staging_swap"}},
            "summary_path": "data/collection_summary.json",
        }

        validate_collection_summary_payload(payload)

    def test_validate_collection_summary_payload_rejects_missing_source_hashes(self) -> None:
        payload: dict[str, object] = {
            "generated_on": "2026-05-01",
            "output_root": "data",
            "version": "v62.0",
            "collected_sources": ["aadr"],
            "source_output_roots": {"aadr": "data/aadr"},
            "source_metadata": {"aadr": {"version": "v62.0"}},
            "source_hashes": {},
            "source_provenance": {"aadr": {"version": "v62.0"}},
            "source_replacement_rules": {"aadr": {"refresh_mode": "staging_swap"}},
            "summary_path": "data/collection_summary.json",
        }

        with self.assertRaisesRegex(
            ValueError, "collection summary missing hashes for source: aadr"
        ):
            validate_collection_summary_payload(payload)

    def test_validate_collection_summary_file_reads_json_payload(self) -> None:
        payload: dict[str, object] = {
            "generated_on": "2026-05-01",
            "output_root": "data",
            "version": "v62.0",
            "collected_sources": ["aadr"],
            "source_output_roots": {"aadr": "data/aadr"},
            "source_metadata": {"aadr": {"version": "v62.0"}},
            "source_hashes": {"aadr": {"snapshot_sha256": "a" * 64}},
            "source_provenance": {"aadr": {"version": "v62.0"}},
            "source_replacement_rules": {"aadr": {"refresh_mode": "staging_swap"}},
            "summary_path": "data/collection_summary.json",
        }

        with tempfile.TemporaryDirectory() as tmp:
            summary_path = Path(tmp) / "collection_summary.json"
            summary_path.write_text(json.dumps(payload), encoding="utf-8")
            loaded = validate_collection_summary_file(summary_path)

        self.assertEqual(loaded["version"], "v62.0")


if __name__ == "__main__":
    unittest.main()
