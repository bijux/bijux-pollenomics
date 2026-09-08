"""Per-project source-library publication behavior."""

import json
from pathlib import Path

from .support import source_library_root


def test_project_bundle_carries_intake_and_publication_readiness(
    materialized_output_root: Path,
) -> None:
    project_root = source_library_root(materialized_output_root) / "projects/PRJEB36540"
    bundle = json.loads((project_root / "bundle_manifest.json").read_text("utf-8"))
    intake = json.loads((project_root / "intake_dossier.json").read_text("utf-8"))

    assert bundle["paper_download_status"] == "archived"
    assert "stage_statuses" in intake
    assert "publication_readiness_status" in intake
    assert "manual_curation_work_units" in intake


def test_project_bundle_publishes_sample_owned_evidence(
    materialized_output_root: Path,
) -> None:
    root = source_library_root(materialized_output_root)
    project_root = root / "projects/PRJEB36540"
    expected_project_outputs = {
        "locality_worksheet.json",
        "sample_chronology.json",
        "sample_chronology_evidence.json",
        "sample_locality_evidence.json",
        "sample_sites.json",
    }

    assert (
        sorted(
            name
            for name in expected_project_outputs
            if not (project_root / name).is_file()
        )
        == []
    )
    assert (
        root / "papers/10.1038-s42003-021-02794-8/supplementary_manifest.json"
    ).is_file()
