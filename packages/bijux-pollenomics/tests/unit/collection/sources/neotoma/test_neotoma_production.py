from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.sources.boundaries.collection import (
    BOUNDARY_CODES,
    NATURAL_EARTH_ADMIN0_URL,
    NATURAL_EARTH_RELEASE_PAGE_URL,
    NATURAL_EARTH_TERMS_URL,
    NATURAL_EARTH_VERSION,
)
from bijux_pollenomics.collection.sources.neotoma.production import (
    NeotomaProductionConfig,
    load_validated_neotoma_raw_archive,
    main,
    run_neotoma_relational_production,
)


def _write_json(path: Path, payload: object) -> bytes:
    content = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return content


def _feature(country_code: str, offset: float) -> dict[str, object]:
    return {
        "type": "Feature",
        "properties": {"ADM0_A3": country_code},
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [offset, 0.0],
                    [offset + 5.0, 0.0],
                    [offset + 5.0, 5.0],
                    [offset, 5.0],
                    [offset, 0.0],
                ]
            ],
        },
    }


def _boundary_authority(root: Path) -> None:
    features = {
        country: _feature(country_code, index * 10.0)
        for index, (country, country_code) in enumerate(BOUNDARY_CODES.items())
    }
    artifact_records: dict[str, object] = {}
    for country, feature in features.items():
        path = root / "raw" / f"{country.lower()}.geojson"
        content = _write_json(
            path, {"type": "FeatureCollection", "features": [feature]}
        )
        artifact_records[country] = {
            "path": path.name,
            "sha256": hashlib.sha256(content).hexdigest(),
            "feature_count": 1,
        }
    normalized_content = _write_json(
        root / "normalized" / "nordic_country_boundaries.geojson",
        {"type": "FeatureCollection", "features": list(features.values())},
    )
    _write_json(
        root / "raw" / "source_manifest.json",
        {
            "schema_version": "natural-earth-boundary-receipt.v1",
            "generated_on": "2026-09-04",
            "source": "Natural Earth",
            "dataset": "Admin 0 - Countries",
            "version": NATURAL_EARTH_VERSION,
            "release_page_url": NATURAL_EARTH_RELEASE_PAGE_URL,
            "asset_url": NATURAL_EARTH_ADMIN0_URL,
            "sha256": "1" * 64,
            "license": "public_domain",
            "license_url": NATURAL_EARTH_TERMS_URL,
            "source_crs": "EPSG:4326",
            "coordinate_transformation": "none",
            "country_selection_field": "ADM0_A3",
            "geometry_inclusion_policy": (
                "retain_all_geometry_parts_from_each_selected_admin0_feature"
            ),
            "feature_count": 258,
            "country_codes": BOUNDARY_CODES,
            "country_artifacts": artifact_records,
            "normalized_artifact": {
                "path": "normalized/nordic_country_boundaries.geojson",
                "sha256": hashlib.sha256(normalized_content).hexdigest(),
                "feature_count": 4,
            },
        },
    )


def _raw_row(dataset_id: int) -> dict[str, object]:
    return {
        "site": {
            "siteid": dataset_id,
            "sitename": f"Site {dataset_id}",
            "geography": json.dumps(
                {
                    "type": "Point",
                    "coordinates": [1.0 + dataset_id / 100.0, 1.0],
                }
            ),
            "geopolitical": ["Sweden"],
            "collectionunit": {
                "collectionunitid": dataset_id,
                "dataset": {"datasetid": dataset_id, "samples": []},
                "chronologies": [],
                "defaultchronology": None,
            },
            "dataset": {"datasetid": dataset_id},
        }
    }


def _raw_archive(root: Path) -> None:
    parts: list[dict[str, object]] = []
    dataset_ids = list(range(1, 10))
    for part_number, dataset_id in enumerate(dataset_ids, start=1):
        filename = f"part-{part_number:03d}.json"
        payload = {
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "endpoint_template": (
                "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
            ),
            "datasettype": "pollen",
            "part_number": part_number,
            "part_count": 9,
            "row_count": 1,
            "downloaded_dataset_count": 1,
            "downloaded_dataset_ids": [dataset_id],
            "rows": [_raw_row(dataset_id)],
        }
        content = _write_json(root / filename, payload)
        parts.append(
            {
                "filename": filename,
                "part_number": part_number,
                "row_count": 1,
                "downloaded_dataset_count": 1,
                "downloaded_dataset_ids": [dataset_id],
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    _write_json(
        root / "manifest.json",
        {
            "generated_on": "2026-04-01",
            "source": "Neotoma",
            "archive_dir": "raw/neotoma_pollen_dataset_downloads",
            "endpoint_template": (
                "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
            ),
            "datasettype": "pollen",
            "requested_dataset_count": 9,
            "requested_dataset_ids": dataset_ids,
            "downloaded_dataset_count": 9,
            "downloaded_dataset_ids": dataset_ids,
            "row_count": 9,
            "rows_per_part": 1,
            "part_count": 9,
            "parts": parts,
        },
    )


class NeotomaProductionTests(unittest.TestCase):
    def _fixture(self, workspace: Path) -> tuple[Path, Path, Path]:
        raw_root = workspace / "raw"
        boundary_root = workspace / "boundaries"
        approved_parent = workspace / "approved"
        approved_parent.mkdir()
        _raw_archive(raw_root)
        _boundary_authority(boundary_root)
        return raw_root, boundary_root, approved_parent

    def test_production_is_content_derived_and_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            raw_root, boundary_root, approved_parent = self._fixture(workspace)

            first = run_neotoma_relational_production(
                raw_archive_root=raw_root,
                boundary_root=boundary_root,
                output_root=approved_parent / "first",
                approved_output_parent=approved_parent,
                config=NeotomaProductionConfig(rows_per_part=2),
            )
            second = run_neotoma_relational_production(
                raw_archive_root=raw_root,
                boundary_root=boundary_root,
                output_root=approved_parent / "second",
                approved_output_parent=approved_parent,
                config=NeotomaProductionConfig(rows_per_part=2),
            )

            self.assertEqual(first.source_snapshot_id, second.source_snapshot_id)
            self.assertEqual(first.boundary_authority_id, second.boundary_authority_id)
            self.assertEqual(first.build_id, second.build_id)
            self.assertEqual(first.raw_part_count, 9)
            self.assertEqual(first.raw_row_count, 9)
            self.assertEqual(first.site_count, 9)
            self.assertEqual(
                first.country_counts,
                {"SE": 9, "DK": 0, "NO": 0, "FI": 0, "UNASSIGNED": 0},
            )
            self.assertEqual(first.country_decision_counts["assigned"], 9)
            first_manifest = json.loads(Path(first.manifest_path).read_text())
            second_manifest = json.loads(Path(second.manifest_path).read_text())
            self.assertEqual(
                first_manifest["materialization_sha256"],
                second_manifest["materialization_sha256"],
            )

    def test_rejects_raw_hash_count_and_boundary_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            raw_root, boundary_root, approved_parent = self._fixture(workspace)
            first_part = raw_root / "part-001.json"
            first_part.write_bytes(first_part.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
                run_neotoma_relational_production(
                    raw_archive_root=raw_root,
                    boundary_root=boundary_root,
                    output_root=approved_parent / "raw-tamper",
                    approved_output_parent=approved_parent,
                )
            self.assertFalse((approved_parent / "raw-tamper").exists())

            _raw_archive(raw_root)
            manifest_path = raw_root / "manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["row_count"] = 8
            _write_json(manifest_path, manifest)
            with self.assertRaisesRegex(ValueError, "aggregate row count"):
                load_validated_neotoma_raw_archive(raw_root)

            _raw_archive(raw_root)
            sweden_path = boundary_root / "raw" / "sweden.geojson"
            sweden_path.write_bytes(sweden_path.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "digest mismatch"):
                run_neotoma_relational_production(
                    raw_archive_root=raw_root,
                    boundary_root=boundary_root,
                    output_root=approved_parent / "boundary-tamper",
                    approved_output_parent=approved_parent,
                )

    def test_output_authority_and_config_are_part_of_gate_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            raw_root, boundary_root, approved_parent = self._fixture(workspace)
            with self.assertRaisesRegex(ValueError, "outside"):
                run_neotoma_relational_production(
                    raw_archive_root=raw_root,
                    boundary_root=boundary_root,
                    output_root=workspace / "outside",
                    approved_output_parent=approved_parent,
                )

            nested = approved_parent / "nested"
            nested.mkdir()
            with self.assertRaisesRegex(ValueError, "outside"):
                run_neotoma_relational_production(
                    raw_archive_root=raw_root,
                    boundary_root=boundary_root,
                    output_root=nested / "..",
                    approved_output_parent=approved_parent,
                )

            first = run_neotoma_relational_production(
                raw_archive_root=raw_root,
                boundary_root=boundary_root,
                output_root=approved_parent / "producer-one",
                approved_output_parent=approved_parent,
            )
            changed = run_neotoma_relational_production(
                raw_archive_root=raw_root,
                boundary_root=boundary_root,
                output_root=approved_parent / "producer-two",
                approved_output_parent=approved_parent,
                config=NeotomaProductionConfig(producer_version="2"),
            )
            self.assertEqual(first.source_snapshot_id, changed.source_snapshot_id)
            self.assertEqual(first.boundary_authority_id, changed.boundary_authority_id)
            self.assertNotEqual(first.build_id, changed.build_id)

    def test_cli_emits_machine_readable_success_and_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            raw_root, boundary_root, approved_parent = self._fixture(workspace)
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = main(
                    [
                        "--raw-archive",
                        str(raw_root),
                        "--boundary-root",
                        str(boundary_root),
                        "--output",
                        str(approved_parent / "cli"),
                        "--approved-output-parent",
                        str(approved_parent),
                        "--rows-per-part",
                        "3",
                    ]
                )
            self.assertEqual(result, 0)
            self.assertEqual(json.loads(stdout.getvalue())["status"], "ok")

            stderr = StringIO()
            with redirect_stderr(stderr):
                failure = main(
                    [
                        "--raw-archive",
                        str(raw_root / "missing"),
                        "--boundary-root",
                        str(boundary_root),
                        "--output",
                        str(approved_parent / "failure"),
                        "--approved-output-parent",
                        str(approved_parent),
                    ]
                )
            self.assertEqual(failure, 1)
            self.assertEqual(json.loads(stderr.getvalue())["status"], "failed")


if __name__ == "__main__":
    unittest.main()
