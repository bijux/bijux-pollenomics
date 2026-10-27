"""Tracked sample and coordinate evidence invariant tests."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics.adna.governance.atlas_candidates.sample_support import (
    _atlas_admitted_sample_rows,
)
from bijux_pollenomics.adna.species.tracked_data import markdown
from bijux_pollenomics.adna.workflow.normalization import AdnaSpeciesNormalizationBundle

pytestmark = pytest.mark.generated_artifacts


def test_supplied_species_projection_avoids_global_recovery_and_bundle_builders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unexpected_global_builder(*_args: object, **_kwargs: object) -> object:
        raise AssertionError("supplied species view called a global builder")

    monkeypatch.setattr(
        markdown, "build_species_normalization_bundle", unexpected_global_builder
    )
    monkeypatch.setattr(
        markdown,
        "_species_project_recovery_deficits_payload",
        unexpected_global_builder,
    )
    bundle = cast(
        AdnaSpeciesNormalizationBundle,
        SimpleNamespace(
            species=SimpleNamespace(latin_name="Capra hircus"),
            sample_records=(SimpleNamespace(inclusion_status="site_curated"),) * 2,
            site_evidence_records=(object(),),
            coordinate_provenance_records=(
                SimpleNamespace(
                    mapping_posture="mappable_point",
                    coordinate_basis="supplementary_table_coordinates",
                ),
            ),
            locality_records=(
                SimpleNamespace(nordic_inclusion=False, coordinate_confidence="exact"),
            ),
        ),
    )
    deficits: dict[str, Any] = {
        "species_latin_name": "Capra hircus",
        "counts": {
            "project_count": 1,
            "projects_with_sample_gap": 1,
            "projects_with_site_gap": 0,
            "projects_with_chronology_gap": 0,
            "projects_blocked_before_publication": 1,
        },
        "rows": [
            {
                "project_accession": "source-project",
                "minimum_gap_count": 1,
                "lacking_defensible_site_assignment_count": 0,
                "missing_chronology_count": 0,
                "publication_readiness_status": "blocked",
            }
        ],
    }
    readme = markdown._render_species_root_readme(
        tmp_path,
        "Capra hircus",
        normalization_bundle=bundle,
        recovery_deficits_payload=deficits,
    )
    assert "- Curated sample rows: `2`" in readme
    assert "- Curated site rows: `1`" in readme
    assert "- Direct-coordinate rows: `1`" in readme
    assert "- Projects with sample recovery gaps: `1`" in readme
    assert "- Projects blocked before publication review: `1`" in readme
    support = markdown._render_support_summary_markdown(
        tmp_path, "Capra hircus", recovery_deficits_payload=deficits
    )
    assert "- Projects with sample recovery gaps: `1`" in support
    assert "- Projects blocked before publication review: `1`" in support
    deficit_report = markdown._render_species_project_recovery_deficits_markdown(
        tmp_path, "Capra hircus", recovery_deficits_payload=deficits
    )
    assert "| `source-project` | `1` | `0` | `0` | `blocked` |" in deficit_report


def test_supplied_species_renderers_reject_another_owner(tmp_path: Path) -> None:
    wrong_bundle = cast(
        AdnaSpeciesNormalizationBundle,
        SimpleNamespace(species=SimpleNamespace(latin_name="Ovis aries")),
    )
    with pytest.raises(ValueError, match="different species owner"):
        markdown._render_species_root_readme(
            tmp_path, "Capra hircus", normalization_bundle=wrong_bundle
        )
    for render in (
        markdown._render_species_root_readme,
        markdown._render_support_summary_markdown,
        markdown._render_species_project_recovery_deficits_markdown,
    ):
        with pytest.raises(ValueError, match="different species owner"):
            render(
                tmp_path,
                "Capra hircus",
                recovery_deficits_payload={"species_latin_name": "Ovis aries"},
            )


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
        atlas_admitted_sample_ids = set()
        for row in _atlas_admitted_sample_rows(tuple(sample_payload["samples"])):
            identity = row["identity"]
            assert isinstance(identity, dict)
            token = identity["stable_token"]
            assert isinstance(token, str)
            atlas_admitted_sample_ids.add(token)
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
                assert (
                    sample["identity"]["stable_token"] not in atlas_admitted_sample_ids
                )
                assert sample["inclusion_note"]
                continue
            if has_coordinates:
                assert provenance is not None, species_root.name
                assert provenance["mapping_posture"] == "mappable_point"
                assert provenance["coordinate_basis"]
                assert coordinates["confidence"]
            if provenance and provenance["mapping_posture"] == "refused_region_only":
                assert not has_coordinates
    assert admitted_sample_count == 1468
    assert refused_sample_count == 25
