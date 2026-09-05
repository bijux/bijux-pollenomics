from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.governance.admission import build_species_dataset_review
from bijux_pollenomics.adna.governance.curation import build_species_curation_manifest
from bijux_pollenomics.adna.governance.integrity import build_archive_integrity_report
from bijux_pollenomics.adna.governance.reviews import (
    build_species_project_manifest,
    build_species_review_dossier,
)
from bijux_pollenomics.adna.sources.ena import build_species_archive_projects
from bijux_pollenomics.adna.sources.library import materialize_source_library
from bijux_pollenomics.adna.workflow.layout import build_species_layout
from bijux_pollenomics.adna.workflow.manifests import build_species_manifest
from bijux_pollenomics.adna.workflow.normalization import (
    build_species_normalization_bundle,
)
from bijux_pollenomics.adna.workflow.runtime import build_species_runtime_manifest
from bijux_pollenomics.core.files import write_json, write_text

from ..tracked_species import TRACKED_ADNA_SPECIES
from .csv_exports import (
    _render_archive_inventory_csv,
    _render_citation_manifest_csv,
    _render_coordinate_provenance_csv,
    _render_locality_summaries_csv,
    _render_project_summaries_csv,
    _render_sample_records_csv,
    _render_site_evidence_csv,
    _render_source_snapshot_csv,
)
from .governance import _materialize_cross_species_adna_artifacts
from .markdown import (
    _render_review_dossier_markdown,
    _render_species_project_recovery_deficits_markdown,
    _render_species_root_readme,
    _render_support_summary_markdown,
)
from .payloads import (
    _archive_inventory_payload,
    _coordinate_provenance_payload,
    _locality_summaries_payload,
    _project_summaries_payload,
    _sample_records_payload,
    _site_evidence_payload,
    _source_snapshot_payload,
    _species_project_recovery_deficits_payload,
    _support_summary_payload,
)
from .validation import _validate_tracked_sample_admission


def materialize_tracked_species_adna(
    output_root: Path,
    *,
    species_names: tuple[str, ...] = TRACKED_ADNA_SPECIES,
) -> None:
    """Write the tracked species-owned animal aDNA files under one data root."""
    materialize_source_library(Path(output_root))
    for species_name in species_names:
        materialize_tracked_species_root(output_root, species_name)
    # Source-library audits consume species-owned generated data. Refresh them after
    # every species root so one invocation reaches the same state as a replay.
    materialize_source_library(Path(output_root))
    _materialize_cross_species_adna_artifacts(Path(output_root))


def materialize_tracked_species_root(output_root: Path, species_name: str) -> None:
    """Write all tracked data files for one non-human species root."""
    output_root = Path(output_root)
    layout = build_species_layout(species_name)
    species_root = output_root / layout.root_dir.removeprefix("data/")
    raw_root = species_root / "raw"
    normalized_root = species_root / "normalized"
    manifests_root = species_root / "manifests"
    reports_root = species_root / "reports"
    review_root = species_root / "review"
    for directory in (
        species_root,
        raw_root,
        normalized_root,
        manifests_root,
        reports_root,
        review_root,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    species_manifest = build_species_manifest(species_name)
    dataset_review = build_species_dataset_review(species_name)
    curation_manifest = build_species_curation_manifest(species_name)
    project_manifest = build_species_project_manifest(species_name)
    runtime_manifest = build_species_runtime_manifest(species_name)
    normalization_bundle = build_species_normalization_bundle(species_name)
    _validate_tracked_sample_admission(normalization_bundle)
    review_dossier = build_species_review_dossier(species_name)
    integrity_report = build_archive_integrity_report(species_name=species_name)
    archive_projects = build_species_archive_projects(species_name)

    write_text(
        species_root / "README.md",
        _render_species_root_readme(output_root, species_name),
    )
    write_json(
        raw_root / "archive_inventory.json",
        _archive_inventory_payload(archive_projects),
    )
    write_text(
        raw_root / "archive_inventory.csv",
        _render_archive_inventory_csv(archive_projects),
    )
    write_json(
        raw_root / "source_snapshot.json", _source_snapshot_payload(species_name)
    )
    write_text(
        raw_root / "source_snapshot.csv", _render_source_snapshot_csv(species_name)
    )
    write_text(
        normalized_root / "sample_records.csv",
        _render_sample_records_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "sample_records.json",
        _sample_records_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "coordinate_provenance.csv",
        _render_coordinate_provenance_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "coordinate_provenance.json",
        _coordinate_provenance_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "site_evidence.csv",
        _render_site_evidence_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "site_evidence.json",
        _site_evidence_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "project_summaries.csv",
        _render_project_summaries_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "project_summaries.json",
        _project_summaries_payload(normalization_bundle),
    )
    write_text(
        normalized_root / "locality_summaries.csv",
        _render_locality_summaries_csv(normalization_bundle),
    )
    write_json(
        normalized_root / "locality_summaries.json",
        _locality_summaries_payload(normalization_bundle),
    )
    write_json(manifests_root / "species_manifest.json", species_manifest.as_dict())
    write_json(manifests_root / "curation_manifest.json", curation_manifest.as_dict())
    write_json(manifests_root / "project_manifest.json", project_manifest.as_dict())
    write_json(manifests_root / "runtime_manifest.json", runtime_manifest.as_dict())
    write_json(
        manifests_root / "normalization_bundle.json",
        normalization_bundle.as_dict(),
    )
    write_text(
        manifests_root / "citation_manifest.csv",
        _render_citation_manifest_csv(archive_projects),
    )
    write_json(
        reports_root / "support_summary.json",
        _support_summary_payload(
            species_manifest=species_manifest.as_dict(),
            dataset_review=dataset_review.as_dict(),
            curation_manifest=curation_manifest.as_dict(),
            project_manifest=project_manifest.as_dict(),
            normalization_bundle=normalization_bundle.as_dict(),
        ),
    )
    write_text(
        reports_root / "support_summary.md",
        _render_support_summary_markdown(output_root, species_name),
    )
    write_json(
        reports_root / "project_recovery_deficits.json",
        _species_project_recovery_deficits_payload(output_root, species_name),
    )
    write_text(
        reports_root / "project_recovery_deficits.md",
        _render_species_project_recovery_deficits_markdown(output_root, species_name),
    )
    write_json(review_root / "species_review.json", review_dossier.as_dict())
    write_json(review_root / "archive_integrity.json", integrity_report.as_dict())
    write_text(
        review_root / "species_review.md", _render_review_dossier_markdown(species_name)
    )
