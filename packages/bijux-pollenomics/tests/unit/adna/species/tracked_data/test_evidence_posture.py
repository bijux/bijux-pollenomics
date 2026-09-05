"""Tracked sample and coordinate evidence invariant tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.generated_artifacts


def test_sample_rows_require_matching_coordinate_provenance_for_mapping(
    tracked_data_root: Path,
) -> None:
    admitted_sample_count = 0
    refused_sample_count = 0

    for species_root in (tracked_data_root / "adna" / "species").iterdir():
        if not species_root.is_dir() or species_root.name == "homo_sapiens":
            continue
        sample_payload = json.loads(
            (species_root / "normalized" / "sample_records.json").read_text(
                encoding="utf-8"
            )
        )
        assert sample_payload["evidence_domain"] == "animal_ancient_dna"
        assert not sample_payload["pollen_eligible"]
        assert not sample_payload["pollen_propagation_eligible"]
        admitted_sample_count += sample_payload["admitted_sample_count"]
        refused_sample_count += sample_payload["refused_sample_count"]
        assert sample_payload["refused_sample_count"] == len(
            sample_payload["sample_refusals"]
        )
        provenance_payload = json.loads(
            (species_root / "normalized" / "coordinate_provenance.json").read_text(
                encoding="utf-8"
            )
        )
        provenance_by_accession = {
            row["project_accession"]: row
            for row in provenance_payload["coordinate_provenance"]
        }
        for sample in sample_payload["samples"]:
            assert sample["sample_identity_resolution"] == "final"
            assert sample["sample_evidence_status"] != "not_yet_recoverable"
            provenance = provenance_by_accession.get(sample["project_accession"])
            coordinates = sample["coordinates"]
            has_coordinates = bool(
                coordinates["latitude_text"] and coordinates["longitude_text"]
            )
            if sample["inclusion_status"] == "sample_context_blocked":
                assert not has_coordinates
                assert sample["locality"] is None
                assert sample["chronology"]["time_start_bp"] is None
                assert sample["chronology"]["time_end_bp"] is None
                continue
            if has_coordinates:
                assert provenance is not None, species_root.name
                assert provenance["mapping_posture"] == "mappable_point"
                assert provenance["coordinate_basis"]
                assert coordinates["confidence"]
            if provenance and provenance["mapping_posture"] == "refused_region_only":
                assert not has_coordinates
    assert admitted_sample_count == 1450
    assert refused_sample_count == 42
