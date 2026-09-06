from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from bijux_pollenomics.collection.sources.boundaries.review import (
    BoundaryAuthority,
    PointEvidence,
    _build_boundary_review,
    _decision_summary,
    _validate_country_geometry,
    build_point_country_decision,
)
from bijux_pollenomics.collection.sources.boundaries.review.loaders.animal_adna import (
    _animal_source_lineage,
)


def _rectangle(
    west: float, south: float, east: float, north: float
) -> list[list[list[float]]]:
    return [
        [
            [west, south],
            [east, south],
            [east, north],
            [west, north],
            [west, south],
        ]
    ]


def _collection(
    country: str, code: str, rectangle: list[list[list[float]]]
) -> dict[str, object]:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Polygon", "coordinates": rectangle},
                "properties": {"ADM0_A3": code, "country": country},
            }
        ],
    }


def _authority(*, overlap: bool = False) -> BoundaryAuthority:
    rectangles = {
        "Sweden": _rectangle(0.0, 0.0, 2.0, 2.0),
        "Denmark": (
            _rectangle(0.0, 0.0, 2.0, 2.0)
            if overlap
            else _rectangle(4.0, 0.0, 6.0, 2.0)
        ),
        "Norway": _rectangle(8.0, 0.0, 10.0, 2.0),
        "Finland": _rectangle(12.0, 0.0, 14.0, 2.0),
    }
    admin_codes = {
        "Sweden": "SWE",
        "Denmark": "DNK",
        "Norway": "NOR",
        "Finland": "FIN",
    }
    boundaries = {
        country: _collection(country, admin_codes[country], rectangle)
        for country, rectangle in rectangles.items()
    }
    combined: dict[str, object] = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": boundaries[country]["features"][0]["geometry"],  # type: ignore[index]
                "properties": {"country": country},
            }
            for country in ("Sweden", "Denmark", "Norway", "Finland")
        ],
    }
    return BoundaryAuthority(
        boundaries=boundaries,
        normalized_collection=combined,
        source_manifest={
            "source": "Natural Earth",
            "dataset": "Admin 0 - Countries",
            "version": "5.1.1",
            "generated_on": "2026-09-04",
            "asset_url": "https://example.invalid/boundaries.geojson",
            "sha256": "1" * 64,
            "license": "public_domain",
            "license_url": "https://example.invalid/terms",
            "source_crs": "EPSG:4326",
            "coordinate_transformation": "none",
            "country_selection_field": "ADM0_A3",
            "geometry_inclusion_policy": (
                "retain_all_geometry_parts_from_each_selected_admin0_feature"
            ),
            "country_artifacts": {
                country: {"path": f"{country.casefold()}.geojson", "sha256": "2" * 64}
                for country in boundaries
            },
        },
        manifest_sha256="3" * 64,
        normalized_artifact_sha256="4" * 64,
        artifact_digest=f"sha256:{'4' * 64}",
    )


def _point(
    *,
    longitude: float,
    latitude: float,
    raw_country: str | None = None,
    published_country: str | None = None,
    scope: str = "four_country_expected",
) -> PointEvidence:
    return PointEvidence(
        source_family="fixture",
        source_scope=scope,  # type: ignore[arg-type]
        source_record_id="fixture:point:1",
        longitude=longitude,
        latitude=latitude,
        raw_country=raw_country,
        published_country=published_country,
        lineage=({"path": "fixture.json", "locator": "rows[0]", "role": "row"},),
    )


class BoundaryCountryReviewTests(unittest.TestCase):
    def test_raw_country_conflict_is_queued_without_human_approval(self) -> None:
        row = build_point_country_decision(
            _point(
                longitude=1.0,
                latitude=1.0,
                raw_country="DK",
                published_country="Sweden",
            ),
            authority=_authority(),
        )

        self.assertEqual(row["derived_country_code"], "SE")
        self.assertEqual(row["country_decision_status"], "review")
        self.assertEqual(row["raw_country_comparison"], "conflicts")
        self.assertIn(
            "raw_country_conflict", cast(list[str], row["review_reason_codes"])
        )
        self.assertEqual(row["qualified_review_status"], "pending")
        self.assertIsNone(row["qualified_reviewer"])
        self.assertIsNone(row["qualified_reviewed_at"])

    def test_multiple_boundary_membership_is_not_silently_assigned(self) -> None:
        row = build_point_country_decision(
            _point(longitude=1.0, latitude=1.0), authority=_authority(overlap=True)
        )

        self.assertEqual(row["country_decision_status"], "review")
        self.assertIsNone(row["derived_boundary_membership"])
        self.assertEqual(row["candidate_country_codes"], ["DK", "SE"])
        self.assertEqual(row["decision_method"], "multiple_boundary_containment")

    def test_global_point_outside_four_country_boundary_is_explicit_unassigned(
        self,
    ) -> None:
        row = build_point_country_decision(
            _point(
                longitude=30.0,
                latitude=30.0,
                raw_country="Turkey",
                published_country="Turkey",
                scope="global_with_four_country_filter",
            ),
            authority=_authority(),
        )

        self.assertEqual(row["country_decision_status"], "unassigned")
        self.assertEqual(row["refusal_reason"], "outside_governed_boundaries")
        self.assertEqual(row["review_requirement"], "no_point_review_required")
        self.assertEqual(row["qualified_review_status"], "not_required")

    def test_invalid_wgs84_coordinate_fails_closed(self) -> None:
        row = build_point_country_decision(
            _point(longitude=181.0, latitude=1.0), authority=_authority()
        )

        self.assertEqual(row["country_decision_status"], "refused")
        self.assertEqual(row["decision_method"], "coordinate_validation")
        self.assertEqual(row["review_requirement"], "qualified_review_required")

    def test_machine_geometry_review_keeps_all_four_human_reviews_pending(self) -> None:
        review = _build_boundary_review(_authority())

        countries = cast(list[dict[str, object]], review["countries"])
        self.assertEqual(
            [country["country_code"] for country in countries],
            ["SE", "DK", "NO", "FI"],
        )
        self.assertTrue(
            all(
                country["machine_structural_validation_status"] == "passed"
                and country["machine_polygon_part_inventory_status"] == "passed"
                and country["qualified_review_status"] == "pending"
                and country["qualified_reviewer"] is None
                for country in countries
            )
        )
        self.assertTrue(
            all(
                len(cast(list[dict[str, object]], country["polygon_part_inventory"]))
                == country["polygon_part_count"]
                for country in countries
            )
        )
        self.assertEqual(
            review["release_status"], "blocked_pending_qualified_boundary_review"
        )

    def test_geometry_validation_rejects_an_unclosed_ring(self) -> None:
        boundary = _collection("Sweden", "SWE", _rectangle(0.0, 0.0, 2.0, 2.0))
        features = cast(list[dict[str, object]], boundary["features"])
        geometry = cast(dict[str, object], features[0]["geometry"])
        coordinates = cast(list[list[list[float]]], geometry["coordinates"])
        coordinates[0][-1] = [1.0, 1.0]

        with self.assertRaisesRegex(ValueError, "not closed"):
            _validate_country_geometry(boundary, country="Sweden")

    def test_summary_keeps_equal_four_country_zero_denominators(self) -> None:
        row = build_point_country_decision(
            _point(longitude=1.0, latitude=1.0, raw_country="SE"),
            authority=_authority(),
        )

        summary = _decision_summary([row])
        self.assertEqual(
            summary["country_counts"],
            {"SE": 1, "DK": 0, "NO": 0, "FI": 0, "UNASSIGNED": 0},
        )


class GovernedBoundaryCountryReviewBundleTests(unittest.TestCase):
    def test_materializer_preserves_composite_animal_source_lineage(self) -> None:
        with tempfile.TemporaryDirectory(dir="artifacts") as temporary_directory:
            root = Path(temporary_directory)
            archive_path = root / "data/archive_metadata.html.gz"
            supplement_path = root / "data/supplement.xlsx"
            archive_path.parent.mkdir(parents=True)
            archive_path.write_bytes(b"archive")
            supplement_path.write_bytes(b"supplement")
            paths, lineage = _animal_source_lineage(
                root,
                source_path_text=("data/archive_metadata.html || data/supplement.xlsx"),
                source_locator="sample_accession:SAMPLE1 || Sheet1!row2",
                record_id="animal:sample1",
            )

        self.assertEqual(
            paths,
            (Path("data/archive_metadata.html.gz"), supplement_path.relative_to(root)),
        )
        self.assertEqual(
            [(row["path"], row["locator"]) for row in lineage],
            [
                ("data/archive_metadata.html.gz", "sample_accession:SAMPLE1"),
                ("data/supplement.xlsx", "Sheet1!row2"),
            ],
        )

    def test_materialized_bundle_reconciles_and_has_valid_digests(self) -> None:
        root = Path("data/boundaries/review")
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
        ledgers = [
            json.loads(path.read_text(encoding="utf-8"))
            for path in sorted((root / "country-decisions").glob("*.json"))
        ]

        self.assertEqual(
            {ledger["source_family"] for ledger in ledgers},
            {"animal_adna", "landclim", "neotoma", "sead"},
        )
        self.assertEqual(
            manifest["point_count"], sum(ledger["row_count"] for ledger in ledgers)
        )
        for output in manifest["outputs"]:
            path = Path(output["path"])
            self.assertEqual(
                hashlib.sha256(path.read_bytes()).hexdigest(), output["sha256"]
            )
        producer = manifest["producer"]
        producer_path = Path(producer["path"])
        self.assertEqual(
            hashlib.sha256(producer_path.read_bytes()).hexdigest(), producer["sha256"]
        )
        for ledger in ledgers:
            self.assertEqual(ledger["coordinate_reference_system"], "EPSG:4326")
            artifact_paths = {
                artifact["path"] for artifact in ledger["source_artifacts"]
            }
            for artifact in ledger["source_artifacts"]:
                artifact_path = Path(artifact["path"])
                self.assertEqual(artifact_path.stat().st_size, artifact["bytes"])
                self.assertEqual(
                    hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
                    artifact["sha256"],
                )
            self.assertEqual(
                set(ledger["summary"]["country_counts"]),
                {"SE", "DK", "NO", "FI", "UNASSIGNED"},
            )
            for row in ledger["decisions"]:
                self.assertEqual(
                    row["boundary_artifact_digest"],
                    manifest["boundary_authority"]["boundary_artifact_digest"],
                )
                self.assertTrue(row["source_native_lineage"])
                self.assertTrue(
                    all(
                        lineage["path"] in artifact_paths
                        for lineage in row["source_native_lineage"]
                    )
                )
                if row["qualified_review_status"] == "pending":
                    self.assertIsNone(row["qualified_reviewer"])
                    self.assertIsNone(row["qualified_reviewed_at"])


if __name__ == "__main__":
    unittest.main()
