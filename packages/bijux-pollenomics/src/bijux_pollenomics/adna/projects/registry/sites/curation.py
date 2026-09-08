"""Manual curation queue derived from unresolved sample-site evidence."""

from __future__ import annotations

from collections.abc import Iterable
import json
from pathlib import Path
from typing import cast

from ....sources.archive import build_archive_project_catalog
from .assembly import build_project_sample_site_rows
from .evidence import _counts_by_status


def build_sample_site_manual_curation_queue(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    source_root = (
        Path(output_root) / "adna" / "governance" / "source_library" / "projects"
    )
    for project in build_archive_project_catalog():
        dossier_path = source_root / project.project_accession / "intake_dossier.json"
        sample_site_rows = build_project_sample_site_rows(
            output_root, project.project_accession
        )
        counts = _counts_by_status(sample_site_rows)
        if not dossier_path.is_file():
            continue

        dossier = json.loads(dossier_path.read_text(encoding="utf-8"))
        queue_reasons = []
        if counts["project_level_site_only"]:
            queue_reasons.append(
                "project_level_site_only_rows_require_sample_owned_site_extraction"
            )
        if counts["region_only"]:
            queue_reasons.append("region_only_rows_require_finer_location_evidence")
        if counts["unresolved"]:
            queue_reasons.append("recovered_sample_rows_still_lack_any_location_claim")
        if not queue_reasons:
            continue
        rows.append(
            {
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "queued_sample_count": (
                    counts["project_level_site_only"]
                    + counts["region_only"]
                    + counts["unresolved"]
                ),
                "queue_reasons": queue_reasons,
                "sample_site_targets": list(dossier.get("sample_site_targets", [])),
                "expected_supplementary_artifacts": list(
                    dossier.get("expected_supplementary_artifacts", [])
                ),
                "local_artifact_paths": list(dossier.get("local_artifact_paths", [])),
                "recommended_next_surface": _recommended_next_surface(dossier),
            }
        )
    return tuple(rows)


def _recommended_next_surface(dossier: dict[str, object]) -> str:
    sample_site_targets = [
        str(item)
        for item in cast(Iterable[object], dossier.get("sample_site_targets", []))
        if str(item).strip()
    ]
    if sample_site_targets:
        return sample_site_targets[0]
    supplementary = [
        str(item)
        for item in cast(
            Iterable[object], dossier.get("expected_supplementary_artifacts", [])
        )
        if str(item).strip()
    ]
    if supplementary:
        return supplementary[0]
    local_artifacts = [
        str(item)
        for item in cast(Iterable[object], dossier.get("local_artifact_paths", []))
        if str(item).strip()
    ]
    if local_artifacts:
        return local_artifacts[0]
    return ""
