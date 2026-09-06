"""Per-project source-bundle registry construction."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.sources.archive import (
    build_archive_project_catalog,
    classify_archive_project_evidence,
)

from ..models import AdnaSourceArtifact, AdnaSourceBundleManifest
from ..specifications import _paper_required, _supplement_required
from ..storage import _iter_materialized_artifacts


def build_project_source_bundles(
    output_root: Path,
) -> tuple[AdnaSourceBundleManifest, ...]:
    """Return one per-project manifest describing local paper and supplement support."""
    output_root = Path(output_root)
    artifacts_by_project: dict[str, list[AdnaSourceArtifact]] = {}
    for artifact in _iter_materialized_artifacts(output_root):
        for accession in artifact.project_accessions:
            artifacts_by_project.setdefault(accession, []).append(artifact)

    bundles: list[AdnaSourceBundleManifest] = []
    for project in build_archive_project_catalog():
        project_artifacts = tuple(
            sorted(
                artifacts_by_project.get(project.project_accession, ()),
                key=lambda item: item.artifact_id,
            )
        )
        local_project_artifacts = tuple(
            item for item in project_artifacts if item.fetch_status == "archived"
        )
        paper_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind
            in {
                "article_html",
                "article_pdf",
                "article_full_text_xml",
                "paper_metadata_json",
            }
        )
        supplement_artifacts = tuple(
            item
            for item in local_project_artifacts
            if item.artifact_kind.startswith("supplementary_")
        )
        paper_required = _paper_required(project.archive_status)
        supplement_required = _supplement_required(project)
        blockers = []
        if paper_required and not paper_artifacts:
            blockers.append("missing_local_paper_evidence")
        if supplement_required and not supplement_artifacts:
            blockers.append("missing_local_supplementary_material")
        if project.paper_linkage is None:
            blockers.append("paper_linkage_not_curated")
        bundles.append(
            AdnaSourceBundleManifest(
                project_accession=project.project_accession,
                species_latin_name=project.species_latin_name,
                archive_status=project.archive_status,
                evidence_strength=classify_archive_project_evidence(project),
                project_url=project.metadata_url,
                paper_doi=None
                if project.paper_linkage is None
                else project.paper_linkage.doi,
                paper_title=(
                    None
                    if project.paper_linkage is None
                    else project.paper_linkage.paper_title
                ),
                archive_metadata_sufficient=not paper_required,
                paper_required=paper_required,
                supplement_required=supplement_required,
                paper_download_status=_fold_fetch_status(paper_artifacts),
                supplement_download_status=_fold_fetch_status(supplement_artifacts),
                local_artifact_ids=tuple(
                    item.artifact_id for item in local_project_artifacts
                ),
                local_artifact_paths=tuple(
                    item.local_path for item in local_project_artifacts
                ),
                blockers=tuple(blockers),
            )
        )
    return tuple(sorted(bundles, key=lambda item: item.project_accession))


def _fold_fetch_status(artifacts: tuple[AdnaSourceArtifact, ...]) -> str:
    if not artifacts:
        return "missing"
    statuses = {item.fetch_status for item in artifacts}
    if statuses == {"archived"}:
        return "archived"
    if "archived" in statuses:
        return "partial"
    return "missing"
