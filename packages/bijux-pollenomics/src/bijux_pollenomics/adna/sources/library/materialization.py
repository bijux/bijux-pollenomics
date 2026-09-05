"""Governed aDNA source-library materialization."""

from __future__ import annotations

from pathlib import Path
from bijux_pollenomics.core.files import write_json, write_text
from bijux_pollenomics.adna.governance.contracts import (
    materialize_adna_governance_contracts,
)
from bijux_pollenomics.adna.workflow.paths import (
    adna_source_library_root,
)
from bijux_pollenomics.adna.sources.ena import build_archive_project_catalog
from .audits import (
    build_cross_project_source_audit,
    build_missing_source_blockers,
    build_source_intake_audit,
    build_source_intake_release_guard,
)
from .cache_control import _clear_source_library_caches
from .models import SOURCE_LIBRARY_SCHEMA_VERSION
from .registries import (
    _paper_manifest_rows,
    build_paper_registry,
    build_project_registry,
    build_project_source_bundles,
    build_supplement_registry,
    build_supplement_zip_member_registry,
)
from .rendering import (
    _project_intake_dossier,
    _render_csv,
    _render_curation_note,
    _render_project_intake_dossier,
    _render_source_storage_audit,
    _render_tracked_project_and_paper_inventory,
)
from .specifications import _doi_slug, _paper_source_spec
from .storage import (
    _artifact_kind_from_filename,
    _content_type_from_filename,
    _resolve_reference_stash_root,
    build_source_artifact_index,
    build_source_storage_audit,
)


def materialize_source_library(output_root: Path) -> None:
    """Write registries, per-project manifests, and curation notes for the local source library."""
    _clear_source_library_caches()
    output_root = Path(output_root)
    source_root = adna_source_library_root(output_root)
    source_root.mkdir(parents=True, exist_ok=True)
    _materialize_curated_local_supplements(output_root)

    project_registry = build_project_registry(output_root)
    paper_registry = build_paper_registry(output_root)
    supplement_registry = build_supplement_registry(output_root)
    supplement_zip_member_registry = build_supplement_zip_member_registry(output_root)
    source_audit = build_cross_project_source_audit(output_root)
    blockers = build_missing_source_blockers(output_root)
    intake_audit = build_source_intake_audit(output_root)
    intake_release_guard = build_source_intake_release_guard(output_root)
    source_artifact_index = build_source_artifact_index(output_root)
    source_storage_audit = build_source_storage_audit(output_root)

    write_json(
        source_root / "project_registry.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "rows": [row.as_dict() for row in project_registry],
        },
    )
    write_text(
        source_root / "project_registry.csv",
        _render_csv([row.as_dict() for row in project_registry]),
    )
    write_json(
        source_root / "paper_registry.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "rows": [row.as_dict() for row in paper_registry],
        },
    )
    write_text(
        source_root / "paper_registry.csv",
        _render_csv([row.as_dict() for row in paper_registry]),
    )
    write_json(
        source_root / "supplement_registry.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "rows": [row.as_dict() for row in supplement_registry],
        },
    )
    write_text(
        source_root / "supplement_registry.csv",
        _render_csv([row.as_dict() for row in supplement_registry]),
    )
    write_json(
        source_root / "supplement_zip_member_registry.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "rows": list(supplement_zip_member_registry),
        },
    )
    write_text(
        source_root / "supplement_zip_member_registry.csv",
        _render_csv(list(supplement_zip_member_registry)),
    )
    write_json(
        source_root / "source_artifact_index.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "rows": [row.as_dict() for row in source_artifact_index],
        },
    )
    write_text(
        source_root / "source_artifact_index.csv",
        _render_csv([row.as_dict() for row in source_artifact_index]),
    )
    write_json(source_root / "source_audit.json", source_audit)
    write_json(source_root / "source_blockers.json", blockers)
    write_json(source_root / "source_intake_audit.json", intake_audit)
    write_json(source_root / "source_intake_release_guard.json", intake_release_guard)
    write_json(source_root / "source_storage_audit.json", source_storage_audit)
    write_text(
        source_root / "source_storage_audit.md",
        _render_source_storage_audit(source_storage_audit),
    )
    write_json(
        source_root / "tracked_project_and_paper_inventory.json",
        {
            "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
            "projects": [row.as_dict() for row in project_registry],
            "papers": [row.as_dict() for row in paper_registry],
        },
    )
    write_text(
        source_root / "tracked_project_and_paper_inventory.md",
        _render_tracked_project_and_paper_inventory(project_registry, paper_registry),
    )

    bundles = build_project_source_bundles(output_root)
    for bundle in bundles:
        project_dir = source_root / "projects" / bundle.project_accession
        project_dir.mkdir(parents=True, exist_ok=True)
        write_json(project_dir / "bundle_manifest.json", bundle.as_dict())
        write_text(project_dir / "curation_note.md", _render_curation_note(bundle))
        write_json(
            project_dir / "intake_dossier.json",
            _project_intake_dossier(output_root, bundle),
        )
        write_text(
            project_dir / "intake_dossier.md",
            _render_project_intake_dossier(output_root, bundle),
        )

    for paper_row in paper_registry:
        paper_dir = source_root / "papers" / _doi_slug(paper_row.paper_doi)
        paper_dir.mkdir(parents=True, exist_ok=True)
        manifest_rows = list(_paper_manifest_rows(output_root, paper_row.paper_doi))
        write_json(
            paper_dir / "supplementary_manifest.json",
            {"schema_version": SOURCE_LIBRARY_SCHEMA_VERSION, "rows": manifest_rows},
        )
        write_text(paper_dir / "supplementary_manifest.csv", _render_csv(manifest_rows))

    from ...projects.evidence.chronology import (
        materialize_project_sample_chronology_library,
    )
    from ...projects.evidence.localities import (
        materialize_project_sample_locality_evidence_library,
    )
    from ...projects.sample_master import materialize_sample_master_library
    from ...projects.registry.sites import materialize_project_sample_site_library
    from ..inventory import materialize_source_inventory

    materialize_sample_master_library(output_root)
    materialize_project_sample_site_library(output_root)
    materialize_project_sample_locality_evidence_library(output_root)
    materialize_project_sample_chronology_library(output_root)
    materialize_source_inventory(output_root)
    materialize_adna_governance_contracts(output_root)
    _clear_source_library_caches()


def _materialize_curated_local_supplements(output_root: Path) -> None:
    source_root = adna_source_library_root(Path(output_root))
    stash_root = _resolve_reference_stash_root(output_root)
    if stash_root is None:
        return
    catalog = build_archive_project_catalog()
    for doi in _curated_local_supplement_ingestion_dois():
        stash_dir = stash_root / _doi_slug(doi)
        if not stash_dir.is_dir():
            continue
        project_accessions = tuple(
            sorted(
                project.project_accession
                for project in catalog
                if project.paper_linkage is not None
                and project.paper_linkage.doi == doi
            )
        )
        paper_dir = source_root / "papers" / _doi_slug(doi) / "supplementary"
        paper_dir.mkdir(parents=True, exist_ok=True)
        for source_path in sorted(
            path for path in stash_dir.iterdir() if path.is_file()
        ):
            if source_path.name.startswith(".") or source_path.name == ".DS_Store":
                continue
            if source_path.suffix.lower() == ".md":
                continue
            target_path = paper_dir / source_path.name
            target_path.write_bytes(source_path.read_bytes())
            write_json(
                target_path.with_suffix(target_path.suffix + ".metadata.json"),
                {
                    "schema_version": SOURCE_LIBRARY_SCHEMA_VERSION,
                    "source_url": _paper_source_spec(doi).article_source_url,
                    "artifact_kind": _artifact_kind_from_filename(source_path.name),
                    "content_type": _content_type_from_filename(source_path.name),
                    "byte_size": source_path.stat().st_size,
                    "paper_doi": doi,
                    "project_accessions": list(project_accessions),
                    "artifact_label": f"curated supplementary asset {source_path.name}",
                    "source_note": (
                        "Recovered from the local DOI-keyed supplement stash and copied into the governed source library."
                    ),
                },
            )


def _curated_local_supplement_ingestion_dois() -> tuple[str, ...]:
    return (
        "10.1016/j.cell.2019.03.049",
        "10.1016/j.isci.2025.113771",
        "10.1016/j.xgen.2025.101099",
        "10.1038/ncomms16082",
        "10.1038/s41562-021-01083-y",
        "10.1038/s41586-021-04018-9",
        "10.1038/s41586-024-08112-6",
        "10.1038/s41598-024-54296-2",
        "10.1073/pnas.1901169116",
        "10.1093/gbe/evae114",
        "10.1093/gbe/evaf181",
        "10.1111/1755-0998.12551",
        "10.1126/science.aam5298",
        "10.1126/science.aao3297",
        "10.1126/science.aav1002",
        "10.1126/science.adt2642",
        "10.24272/j.issn.2095-8137.2025.080",
    )
