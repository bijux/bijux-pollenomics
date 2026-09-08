from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.published_reports import (
    _load_animal_evidence_ids,
)


class AnimalEvidenceEnvelopeTests(unittest.TestCase):
    def test_loader_requires_the_governed_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            evidence_path = build_atlas_bundle_paths(
                output_dir, "nordic", "unused"
            ).animal_atlas_evidence_json_path

            for invalid in (
                [{"evidence_row_id": "animal:one"}],
                {"schema_version": "wrong.v1", "rows": []},
                {
                    "schema_version": "animal-atlas-evidence-rows.v1",
                    "rows": {},
                },
            ):
                evidence_path.write_text(json.dumps(invalid), encoding="utf-8")
                with (
                    self.subTest(invalid=invalid),
                    self.assertRaisesRegex(ValueError, "Animal atlas evidence"),
                ):
                    _load_animal_evidence_ids(
                        output_dir,
                        slug="nordic",
                        build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
                    )

            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "animal-atlas-evidence-rows.v1",
                        "rows": [
                            {"evidence_row_id": "animal:one"},
                            {"evidence_row_id": "animal:two"},
                        ],
                    }
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                _load_animal_evidence_ids(
                    output_dir,
                    slug="nordic",
                    build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
                ),
                {"animal:one", "animal:two"},
            )
