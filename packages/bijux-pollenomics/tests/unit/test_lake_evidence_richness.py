from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile

from bijux_pollenomics.adna import (
    AdnaChronology,
    AdnaCoordinate,
    AdnaLocalityIdentity,
    AdnaLocalitySummary,
)
from bijux_pollenomics.analysis import (
    build_sweden_lake_evidence_richness_report,
    render_lake_evidence_richness_markdown,
    write_lake_evidence_richness_band_csv,
    write_lake_evidence_richness_json,
)


def _locality(
    name: str,
    latitude: float,
    longitude: float,
    *,
    sample_count: int,
) -> AdnaLocalitySummary:
    return AdnaLocalitySummary(
        identity=AdnaLocalityIdentity(
            namespace="shared_locality",
            stable_token=f"{name.casefold().replace(' ', '-')}-{latitude}-{longitude}",
            locality_text=name,
            political_entity="Sweden",
            source_anchor_tokens=("shared", str(latitude), str(longitude)),
        ),
        species_latin_name="Homo sapiens",
        species_common_name="human",
        source_family="AADR",
        source_releases=("v66",),
        record_modalities=("metadata_only",),
        review_strengths=("primary_paper_pinned",),
        provenance_qualities=("release_manifest_pinned",),
        locality=name,
        coordinates=AdnaCoordinate(
            latitude=latitude,
            longitude=longitude,
            latitude_text=str(latitude),
            longitude_text=str(longitude),
            confidence="unknown",
        ),
        sample_count=sample_count,
        sample_ids=tuple(f"S{index}" for index in range(sample_count)),
        datasets=("dataset",),
        chronology=AdnaChronology(
            original_text="3000 BP",
            time_start_bp=3500,
            time_end_bp=2500,
            time_mean_bp=3000,
            dating_basis="bp_window",
        ),
        sample_namespace="shared:sample",
    )


def _point_feature(
    *,
    source: str,
    layer_key: str,
    layer_label: str,
    category: str,
    country: str,
    record_id: str,
    name: str,
    latitude: float,
    longitude: float,
    description: str,
    time_start_bp: int | None = 3600,
    time_end_bp: int | None = 2400,
) -> dict[str, object]:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [longitude, latitude]},
        "properties": {
            "source": source,
            "layer_key": layer_key,
            "layer_label": layer_label,
            "category": category,
            "country": country,
            "record_id": record_id,
            "name": name,
            "geometry_type": "Point",
            "subtitle": category,
            "description": description,
            "source_url": "https://example.test",
            "record_count": 1,
            "time_start_bp": time_start_bp,
            "time_end_bp": time_end_bp,
            "time_mean_bp": 3000 if time_start_bp is not None else None,
            "time_label": "3000 BP" if time_start_bp is not None else "",
            "popup_rows": [],
        },
    }


def _raa_feature(
    *,
    min_longitude: float,
    min_latitude: float,
    max_longitude: float,
    max_latitude: float,
    count: int,
) -> dict[str, object]:
    return {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": [
                [
                    [min_longitude, min_latitude],
                    [max_longitude, min_latitude],
                    [max_longitude, max_latitude],
                    [min_longitude, max_latitude],
                    [min_longitude, min_latitude],
                ]
            ],
        },
        "properties": {
            "layer_key": "raa-archaeology",
            "layer_label": "RAÄ archaeology density",
            "country": "Sweden",
            "count": count,
            "count_label": str(count),
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_build_sweden_lake_evidence_richness_report_ranks_multi_signal_lakes() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        description="Lake basin with deep sequence.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n2",
                        name="Lake Gamma",
                        latitude=60.0,
                        longitude=16.0,
                        description="Small lake in upland valley.",
                    ),
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n3",
                        name="Bog Beta",
                        latitude=58.0,
                        longitude=15.0,
                        description="Raised bog with peat accumulation.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="LandClim",
                        layer_key="landclim-sites",
                        layer_label="LandClim pollen sites",
                        category="Pollen sequence",
                        country="Sweden",
                        record_id="l1",
                        name="Lake Alpha",
                        latitude=57.0005,
                        longitude=14.0005,
                        description="LandClim site metadata.",
                    ),
                    _point_feature(
                        source="LandClim",
                        layer_key="landclim-sites",
                        layer_label="LandClim pollen sites",
                        category="Pollen sequence",
                        country="Sweden",
                        record_id="l2",
                        name="Lake Gamma",
                        latitude=60.0,
                        longitude=16.0,
                        description="LandClim site metadata.",
                    ),
                ],
            },
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s1",
                        name="Alpha archaeology 1",
                        latitude=57.03,
                        longitude=14.01,
                        description="Nearby archaeology.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s2",
                        name="Alpha archaeology 2",
                        latitude=57.04,
                        longitude=14.02,
                        description="Nearby archaeology.",
                    ),
                    _point_feature(
                        source="SEAD",
                        layer_key="sead-sites",
                        layer_label="SEAD sites",
                        category="Environmental archaeology",
                        country="Sweden",
                        record_id="s3",
                        name="Gamma archaeology",
                        latitude=60.12,
                        longitude=16.08,
                        description="More distant archaeology.",
                    ),
                ],
            },
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _raa_feature(
                        min_longitude=13.5,
                        min_latitude=56.5,
                        max_longitude=14.5,
                        max_latitude=57.5,
                        count=1200,
                    ),
                    _raa_feature(
                        min_longitude=15.5,
                        min_latitude=59.5,
                        max_longitude=16.5,
                        max_latitude=60.5,
                        count=300,
                    ),
                ],
            },
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(
                _locality("Alpha human cluster", 57.02, 14.02, sample_count=8),
                _locality("Gamma human cluster", 60.12, 16.04, sample_count=2),
            ),
            animal_localities=(
                {
                    "locality": "Alpha horse",
                    "latitude": 57.05,
                    "longitude": 14.04,
                    "sample_count": 1,
                },
            ),
        )

        assert report.schema_version == "sweden-lake-evidence-richness.v1"
        assert report.candidate_count == 2
        assert [assessment.candidate.lake_name for assessment in report.assessments] == [
            "Lake Alpha",
            "Lake Gamma",
        ]
        top = report.assessments[0]
        assert top.candidate.direct_pollen_source_count == 2
        assert top.aggregate_score > report.assessments[1].aggregate_score
        assert top.band_scores[0].human_adna_locality_count == 1
        assert top.band_scores[0].domesticated_animal_locality_count == 1
        assert top.band_scores[0].sead_site_count == 2
        assert top.band_scores[0].raa_density_site_count == 1200


def test_lake_evidence_richness_packets_write_reviewable_outputs() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write_json(
            root / "neotoma" / "normalized" / "nordic_pollen_sites.geojson",
            {
                "type": "FeatureCollection",
                "features": [
                    _point_feature(
                        source="Neotoma",
                        layer_key="neotoma-pollen",
                        layer_label="Neotoma pollen sites",
                        category="Pollen",
                        country="Sweden",
                        record_id="n1",
                        name="Lake Alpha",
                        latitude=57.0,
                        longitude=14.0,
                        description="Lake basin with deep sequence.",
                    ),
                ],
            },
        )
        _write_json(
            root / "landclim" / "normalized" / "nordic_pollen_site_sequences.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "sead" / "normalized" / "nordic_environmental_sites.geojson",
            {"type": "FeatureCollection", "features": []},
        )
        _write_json(
            root / "raa" / "normalized" / "sweden_archaeology_density.geojson",
            {"type": "FeatureCollection", "features": []},
        )

        report = build_sweden_lake_evidence_richness_report(
            context_root=root,
            human_localities=(_locality("Alpha human cluster", 57.02, 14.02, sample_count=3),),
            animal_localities=(),
        )
        json_path = root / "lake_evidence.json"
        csv_path = root / "lake_evidence.csv"
        markdown = render_lake_evidence_richness_markdown(report)
        write_lake_evidence_richness_json(json_path, report)
        write_lake_evidence_richness_band_csv(csv_path, report)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        assert payload["candidate_count"] == 1
        assert len(rows) == len(report.radii_km)
        assert markdown.startswith("# Sweden lake evidence richness")
        assert "## 10 km Ranking" in markdown
