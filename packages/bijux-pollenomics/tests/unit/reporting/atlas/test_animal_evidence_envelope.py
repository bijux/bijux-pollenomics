from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.adna.governance.atlas_candidates.models import (
    AnimalAtlasEvidenceRow,
)
from bijux_pollenomics.adna.governance.atlas_candidates.row_factory import (
    _build_evidence_row,
)
from bijux_pollenomics.reporting.adna.animal_localities.publication import (
    _write_animal_atlas_evidence_json,
)
from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.published_reports import (
    _load_animal_evidence_ids,
)


def evidence_row(site_id: str) -> AnimalAtlasEvidenceRow:
    sample_id = f"sample:{site_id}"
    chronology: dict[str, object] = {
        "original_text": "Synthetic 100-200 BP sample interval",
        "time_start_bp": 100,
        "time_end_bp": 200,
        "time_mean_bp": 150,
        "date_stddev_bp": "",
        "dating_basis": "bp_window",
        "evidence_class": "direct_radiocarbon_date",
        "precision_posture": "sample_precise_interval",
    }
    return _build_evidence_row(
        species_slug="ovis_aries",
        locality={
            "sample_ids": [sample_id],
            "sample_count": 1,
            "chronology": chronology,
        },
        site_identity={},
        coordinates={},
        provenance={},
        site_evidence={},
        citation={},
        review={},
        animal_scope="domesticated_core",
        project_accessions=("synthetic-project",),
        primary_project_accession="synthetic-project",
        site_record_id=site_id,
        latitude=59,
        longitude=18,
        sample_rows=({"master_id": sample_id, "chronology": chronology},),
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

    def test_loader_reads_actual_v2_writer_without_altering_owned_chronology(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            evidence_path = build_atlas_bundle_paths(
                output_dir, "nordic", "unused"
            ).animal_atlas_evidence_json_path
            rows = (evidence_row("site:one"), evidence_row("site:two"))
            _write_animal_atlas_evidence_json(evidence_path, rows)
            original = evidence_path.read_bytes()
            payload = json.loads(original)
            self.assertEqual(payload["schema_version"], "animal-atlas-evidence-rows.v2")
            self.assertEqual(
                payload["rows"][0]["chronology_role"], "locality_sample_coverage_hull"
            )
            self.assertEqual(
                payload["rows"][0]["sample_chronologies"][0]["sample_id"],
                "sample:site:one",
            )
            expected = {row.evidence_row_id for row in rows}
            self.assertEqual(
                _load_animal_evidence_ids(
                    output_dir,
                    slug="nordic",
                    build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
                ),
                expected,
            )
            self.assertEqual(evidence_path.read_bytes(), original)
            evidence_path.write_text(
                json.dumps(
                    {
                        "schema_version": "animal-atlas-evidence-rows.v1",
                        "rows": [
                            {"evidence_row_id": row.evidence_row_id} for row in rows
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
                expected,
            )
            for version in ("v1", "v2"):
                with self.subTest(version=version):
                    evidence_path.write_text(
                        json.dumps(
                            {
                                "schema_version": f"animal-atlas-evidence-rows.{version}",
                                "rows": [],
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
                        set(),
                    )

    def test_loader_refuses_malformed_and_duplicate_identity_rows(self) -> None:
        invalid_ids: tuple[object, ...] = (
            None,
            True,
            17,
            [],
            {},
            "",
            " ",
            " animal:one",
            "animal:one ",
            "animal:one\n",
        )
        invalid_rows: list[list[object]] = [
            [None],
            [False],
            [17],
            ["animal:one"],
            [[]],
            [{}],
            [{"evidence_row_id": "animal:one"}, {"evidence_row_id": "animal:one"}],
        ]
        for value in invalid_ids:
            invalid_rows.append([{"evidence_row_id": value}])
        with tempfile.TemporaryDirectory() as tmp:
            output_dir = Path(tmp)
            evidence_path = build_atlas_bundle_paths(
                output_dir, "nordic", "unused"
            ).animal_atlas_evidence_json_path
            for version in ("v1", "v2"):
                for rows in invalid_rows:
                    with self.subTest(version=version, rows=rows):
                        evidence_path.write_text(
                            json.dumps(
                                {
                                    "schema_version": f"animal-atlas-evidence-rows.{version}",
                                    "rows": rows,
                                }
                            ),
                            encoding="utf-8",
                        )
                        with self.assertRaisesRegex(
                            ValueError, "Animal atlas evidence"
                        ):
                            _load_animal_evidence_ids(
                                output_dir,
                                slug="nordic",
                                build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
                            )
