from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile

from bijux_pollenomics.analysis import (
    LakeEvidenceBandScore,
    LakeEvidenceCandidate,
    LakeEvidenceRichnessAssessment,
    LakeEvidenceRichnessReport,
    LakeEvidenceSourceAnchor,
    build_lake_fieldwork_preparation_payload,
    render_lake_fieldwork_preparation_markdown,
    render_lake_fieldwork_preparation_section,
    write_lake_fieldwork_preparation_csv,
    write_lake_fieldwork_preparation_json,
)


def _source_point(
    *,
    source_record: str,
    source_name: str,
    source_layer_key: str,
    latitude: float,
    longitude: float,
    source_url: str = "https://example.test/source",
) -> LakeEvidenceSourceAnchor:
    return LakeEvidenceSourceAnchor(
        source_record=source_record,
        source_name=source_name,
        source_layer_key=source_layer_key,
        latitude=latitude,
        longitude=longitude,
        source_url=source_url,
    )


def _candidate(
    *,
    lake_name: str,
    lake_label: str,
    latitude: float,
    longitude: float,
    ambiguity_flags: tuple[str, ...],
    direct_pollen_source_count: int,
) -> LakeEvidenceCandidate:
    return LakeEvidenceCandidate(
        lake_name=lake_name,
        lake_label=lake_label,
        lake_token=lake_name.casefold().replace(" ", "-"),
        name_key=lake_name.casefold().replace(" ", ""),
        latitude=latitude,
        longitude=longitude,
        basin_posture="lake_basin",
        direct_pollen_source_count=direct_pollen_source_count,
        direct_pollen_record_count=direct_pollen_source_count,
        time_aware_direct_pollen_records=direct_pollen_source_count,
        pollen_sources=("landclim-sites", "neotoma-pollen")[
            :direct_pollen_source_count
        ],
        supporting_pollen_names=(lake_name,),
        supporting_source_records=("landclim-sites:l1", "neotoma-pollen:n1")[
            :direct_pollen_source_count
        ],
        supporting_source_points=(
            _source_point(
                source_record="landclim-sites:l1",
                source_name=lake_name,
                source_layer_key="landclim-sites",
                latitude=latitude,
                longitude=longitude,
            ),
        ),
        representative_source_record="landclim-sites:l1",
        representative_source_layer_key="landclim-sites",
        representative_source_name=lake_name,
        representative_source_url="https://example.test/source",
        coordinate_resolution_method="shared_source_coordinate",
        duplicate_name_count=2 if "duplicate_sweden_name" in ambiguity_flags else 1,
        coordinate_spread_km=0.9
        if "source_coordinate_spread" in ambiguity_flags
        else 0.0,
        ambiguity_flags=ambiguity_flags,
        ambiguity_note="identity review required" if ambiguity_flags else "",
        direct_pollen_signal=0.8,
    )


def _band(
    radius_km: int,
    *,
    band_rank: int,
    total_score: float,
    sead_site_count: int,
    evidence_family_count: int,
    human_adna_locality_count: int,
    domesticated_animal_locality_count: int = 0,
) -> LakeEvidenceBandScore:
    return LakeEvidenceBandScore(
        radius_km=radius_km,
        band_rank=band_rank,
        total_score=total_score,
        nearby_pollen_lake_count=2,
        human_adna_locality_count=human_adna_locality_count,
        human_adna_sample_count=human_adna_locality_count * 4,
        domesticated_animal_locality_count=domesticated_animal_locality_count,
        domesticated_animal_sample_count=domesticated_animal_locality_count,
        sead_site_count=sead_site_count,
        raa_density_site_count=100,
        evidence_family_count=evidence_family_count,
        nearby_pollen_signal=0.7,
        human_signal=0.5,
        animal_signal=0.0,
        archaeology_signal=0.7,
        diversity_signal=0.8,
    )


def _report() -> LakeEvidenceRichnessReport:
    strong = LakeEvidenceRichnessAssessment(
        candidate=_candidate(
            lake_name="Lake Clear",
            lake_label="Lake Clear",
            latitude=57.1,
            longitude=14.2,
            ambiguity_flags=(),
            direct_pollen_source_count=2,
        ),
        aggregate_rank=1,
        aggregate_score=0.62,
        band_scores=(
            _band(
                10,
                band_rank=1,
                total_score=0.55,
                sead_site_count=9,
                evidence_family_count=3,
                human_adna_locality_count=1,
            ),
            _band(
                20,
                band_rank=1,
                total_score=0.63,
                sead_site_count=24,
                evidence_family_count=4,
                human_adna_locality_count=2,
            ),
            _band(
                30,
                band_rank=1,
                total_score=0.60,
                sead_site_count=30,
                evidence_family_count=4,
                human_adna_locality_count=2,
            ),
            _band(
                40,
                band_rank=1,
                total_score=0.58,
                sead_site_count=36,
                evidence_family_count=4,
                human_adna_locality_count=2,
            ),
            _band(
                50,
                band_rank=1,
                total_score=0.57,
                sead_site_count=40,
                evidence_family_count=4,
                human_adna_locality_count=2,
            ),
        ),
    )
    ambiguous = LakeEvidenceRichnessAssessment(
        candidate=_candidate(
            lake_name="Lake Shared",
            lake_label="Lake Shared (57.500000, 15.500000)",
            latitude=57.5,
            longitude=15.5,
            ambiguity_flags=("duplicate_sweden_name", "source_coordinate_spread"),
            direct_pollen_source_count=2,
        ),
        aggregate_rank=2,
        aggregate_score=0.51,
        band_scores=(
            _band(
                10,
                band_rank=2,
                total_score=0.48,
                sead_site_count=3,
                evidence_family_count=3,
                human_adna_locality_count=0,
            ),
            _band(
                20,
                band_rank=2,
                total_score=0.52,
                sead_site_count=7,
                evidence_family_count=4,
                human_adna_locality_count=1,
            ),
            _band(
                30,
                band_rank=2,
                total_score=0.50,
                sead_site_count=10,
                evidence_family_count=4,
                human_adna_locality_count=1,
            ),
            _band(
                40,
                band_rank=2,
                total_score=0.49,
                sead_site_count=12,
                evidence_family_count=4,
                human_adna_locality_count=1,
            ),
            _band(
                50,
                band_rank=2,
                total_score=0.47,
                sead_site_count=15,
                evidence_family_count=4,
                human_adna_locality_count=1,
            ),
        ),
    )
    return LakeEvidenceRichnessReport(
        schema_version="sweden-lake-evidence-richness.v2",
        country="Sweden",
        radii_km=(10, 20, 30, 40, 50),
        methodology={},
        candidate_count=2,
        assessments=(strong, ambiguous),
    )


def test_lake_fieldwork_preparation_payload_keeps_identity_and_interoperability_visible() -> (
    None
):
    payload = build_lake_fieldwork_preparation_payload(_report())
    markdown = render_lake_fieldwork_preparation_markdown(payload)
    section = render_lake_fieldwork_preparation_section(
        json_name="sweden_lake_fieldwork_preparation_v66.json",
        csv_name="sweden_lake_fieldwork_preparation_v66.csv",
        markdown_name="sweden_lake_fieldwork_preparation_v66.md",
    )

    assert payload["schema_version"] == "sweden-lake-fieldwork-preparation.v1"
    assert payload["row_count"] == 2
    assert payload["rows"][0]["preparation_posture"] == "fieldwork_preparation_ready"
    assert payload["rows"][0]["palaeopen_alignment_posture"] == "high"
    assert payload["rows"][0]["scenario_consistency_posture"] == "high"
    assert payload["rows"][0]["scenario_top20_presence_count"] == 6
    assert payload["rows"][0]["google_maps_url"].startswith(
        "https://www.google.com/maps/search/"
    )
    assert (
        payload["rows"][1]["identity_posture"] == "duplicate_name_resolution_required"
    )
    assert payload["rows"][1]["preparation_posture"] == "identity_resolution_required"
    assert "Sweden lake fieldwork preparation" in markdown
    assert "Scenario consistency rule" in markdown
    assert "Lake Fieldwork Preparation" in section


def test_lake_fieldwork_preparation_writers_emit_reviewable_files() -> None:
    report = _report()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        json_path = root / "sweden_lake_fieldwork_preparation_v66.json"
        csv_path = root / "sweden_lake_fieldwork_preparation_v66.csv"

        write_lake_fieldwork_preparation_json(json_path, report)
        write_lake_fieldwork_preparation_csv(csv_path, report)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["row_count"] == 2

        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        assert rows[0]["preparation_posture"] == "fieldwork_preparation_ready"
        assert rows[0]["scenario_consistency_posture"] == "high"
        assert (
            "confirm the exact Swedish lake registry match before field planning"
            in rows[1]["required_actions"]
        )
