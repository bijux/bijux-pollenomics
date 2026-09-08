from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest

from bijux_pollenomics.collection.sources.boundaries.store import (
    load_repository_country_boundaries,
)
from bijux_pollenomics.collection.sources.neotoma.collection import (
    materialize_neotoma_repository_surfaces,
)
from bijux_pollenomics.collection.sources.neotoma.context_points import (
    normalize_neotoma_rows,
)
from bijux_pollenomics.collection.sources.neotoma.review import (
    build_neotoma_temporal_review,
)

ROOT = Path(__file__).resolve().parents[8]


class NeotomaRepositorySurfaceTests(unittest.TestCase):
    def test_materialize_neotoma_repository_surfaces_writes_temporal_review(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            data_root = Path(tmp) / "data"
            raw_root = data_root / "neotoma" / "raw"
            raw_root.mkdir(parents=True, exist_ok=True)
            (data_root / "boundaries" / "raw").mkdir(parents=True, exist_ok=True)
            (raw_root / "neotoma_pollen_sites.json").write_text(
                json.dumps(
                    {
                        "generated_on": "2026-06-22",
                        "source": "Neotoma",
                        "datasettype": "pollen",
                        "rows": [
                            {
                                "siteid": 20,
                                "sitename": "Ageröds Mosse",
                                "sitedescription": "Forested bog.",
                                "geography": '{"type":"Point","coordinates":[13.6,55.9]}',
                                "dataset_count": 1,
                                "sample_count": 3,
                                "chronology_count": 1,
                                "age_ranges": [
                                    {
                                        "units": "Calibrated radiocarbon years BP",
                                        "ageold": 3600,
                                        "ageyoung": 20,
                                    }
                                ],
                                "collectionunits": [{"datasets": []}],
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            sweden_boundary = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [10.0, 55.0],
                                    [25.0, 55.0],
                                    [25.0, 70.0],
                                    [10.0, 70.0],
                                    [10.0, 55.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "SWE"},
                    }
                ],
            }
            placeholder_boundary = {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {
                            "type": "Polygon",
                            "coordinates": [
                                [
                                    [0.0, 0.0],
                                    [1.0, 0.0],
                                    [1.0, 1.0],
                                    [0.0, 1.0],
                                    [0.0, 0.0],
                                ]
                            ],
                        },
                        "properties": {"ADM0_A3": "DNK"},
                    }
                ],
            }
            (data_root / "boundaries" / "raw" / "sweden.geojson").write_text(
                json.dumps(sweden_boundary),
                encoding="utf-8",
            )
            for country, code in (
                ("denmark", "DNK"),
                ("norway", "NOR"),
                ("finland", "FIN"),
            ):
                payload = json.loads(json.dumps(placeholder_boundary))
                payload["features"][0]["properties"]["ADM0_A3"] = code
                (data_root / "boundaries" / "raw" / f"{country}.geojson").write_text(
                    json.dumps(payload),
                    encoding="utf-8",
                )

            report = materialize_neotoma_repository_surfaces(data_root)

            normalized_payload = json.loads(
                report.normalized_geojson_path.read_text(encoding="utf-8")
            )
            temporal_review = json.loads(
                (data_root / "neotoma" / "review" / "temporal_review.json").read_text(
                    encoding="utf-8"
                )
            )

        self.assertEqual(report.point_count, 1)
        feature = normalized_payload["features"][0]
        self.assertEqual(feature["properties"]["country"], "Sweden")
        self.assertEqual(
            feature["properties"]["temporal_semantics"]["comparability_posture"],
            "contextual_label_only",
        )
        self.assertIsNone(feature["properties"]["time_start_bp"])
        self.assertIsNone(feature["properties"]["time_end_bp"])
        self.assertIsNone(feature["properties"]["time_mean_bp"])
        self.assertEqual(
            temporal_review["comparability_posture_counts"]["contextual_label_only"],
            1,
        )
        self.assertEqual(
            temporal_review["schema_version"], "neotoma-temporal-review.v4"
        )
        self.assertEqual(temporal_review["source_site_denominator"], 1)
        self.assertEqual(temporal_review["governed_country_projected_site_count"], 1)
        self.assertEqual(temporal_review["excluded_site_count"], 0)
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_with_source_bp_labelled_context"
            ],
            1,
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_with_source_bp_labelled_context_but_no_compact_chronology_rows"
            ],
            0,
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_with_source_bp_labelled_context_and_compact_chronology_rows"
            ],
            1,
        )
        self.assertEqual(
            temporal_review["coverage_summary"]["chronology_capture_posture"],
            "compact_context_with_separate_sample_chronology",
        )
        self.assertEqual(
            temporal_review["coverage_summary"]["compact_numeric_site_interval_count"],
            0,
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_without_compact_numeric_interval"
            ],
            1,
        )
        self.assertEqual(
            temporal_review["coverage_summary"][
                "site_count_without_source_bp_labelled_context"
            ],
            0,
        )
        self.assertEqual(
            temporal_review["rows"][0]["bp_context_posture"],
            "calendar_comparable_system_with_compact_chronology_rows",
        )
        self.assertEqual(
            temporal_review["rows"][0]["calendar_comparable_bp_system_age_range_count"],
            1,
        )


def test_current_snapshot_projects_only_governed_countries_with_null_site_time() -> (
    None
):
    data_root = ROOT / "data"
    payload = json.loads(
        (data_root / "neotoma/raw/neotoma_pollen_sites.json").read_text(
            encoding="utf-8"
        )
    )
    raw_rows = payload["rows"]
    assert isinstance(raw_rows, list)
    rows = [row for row in raw_rows if isinstance(row, dict)]

    records = normalize_neotoma_rows(
        rows,
        bbox=(4.0, 54.0, 35.0, 72.0),
        country_boundaries=load_repository_country_boundaries(data_root),
    )

    assert len(rows) == 200
    assert len(records) == 193
    assert Counter(record.country for record in records) == {
        "Denmark": 5,
        "Finland": 32,
        "Norway": 58,
        "Sweden": 98,
    }
    assert all(record.time_start_bp is None for record in records)
    assert all(record.time_end_bp is None for record in records)
    assert all(record.time_mean_bp is None for record in records)

    review = build_neotoma_temporal_review(rows, records)
    assert review["source_site_denominator"] == 200
    assert review["governed_country_projected_site_count"] == 193
    assert review["excluded_site_count"] == 7
    assert review["excluded_site_ids"] == [
        "13395",
        "26118",
        "3025",
        "3138",
        "3221",
        "3311",
        "700",
    ]
    posture_counts = review["comparability_posture_counts"]
    assert isinstance(posture_counts, dict)
    assert sum(posture_counts.values()) == 193
    review_rows = review["rows"]
    assert isinstance(review_rows, list)
    excluded_rows = [
        row
        for row in review_rows
        if isinstance(row, dict)
        and row["projection_status"] == "excluded_from_governed_country_projection"
    ]
    assert len(excluded_rows) == 7
    assert {row["country"] for row in excluded_rows} == {"UNASSIGNED"}
    coverage = review["coverage_summary"]
    assert coverage["site_count_with_source_bp_labelled_context"] == 169
    assert coverage["site_count_with_calendar_comparable_bp_system_context"] == 158
    assert coverage["site_count_with_noncomparable_bp_system_context_only"] == 11
    assert coverage["compact_numeric_site_interval_count"] == 0
    review_by_site = {
        str(row["site_id"]): row for row in review_rows if isinstance(row, dict)
    }
    assert review_by_site["12"]["bp_context_posture"] == (
        "calendar_comparable_system_context_only"
    )
    assert review_by_site["12"]["calendar_comparable_bp_system_age_range_units"] == [
        "Calibrated radiocarbon years BP"
    ]
    assert review_by_site["3141"]["bp_context_posture"] == (
        "noncomparable_bp_system_context_only"
    )
    assert review_by_site["3141"]["calendar_comparable_bp_system_age_range_count"] == 0
    assert review_by_site["28077"]["bp_context_posture"] == (
        "noncomparable_bp_system_context_only"
    )
