"""Project and cross-project sample-master orchestration."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.adna.sources.library import build_project_registry
from bijux_pollenomics.adna.species.definitions import resolve_species_definition

from .archive import (
    _archive_native_sample_rows,
    _empty_sample_master_row,
    _project_by_accession,
)
from .identity import _deduplicate_sample_rows
from .models import AdnaProjectSampleMaster, AdnaProjectSampleMasterRow
from .rendering import _render_sample_identity_ambiguity_markdown
from .supplements import _project_specific_sample_rows


def build_project_sample_master_rows(
    output_root: Path,
    project_accession: str,
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    output_root = Path(output_root)
    project = _project_by_accession(project_accession)
    species = resolve_species_definition(project.species_latin_name)
    raw_rows: list[AdnaProjectSampleMasterRow] = []
    raw_rows.extend(_archive_native_sample_rows(species, project))
    raw_rows.extend(_project_specific_sample_rows(output_root, species, project))
    return _deduplicate_sample_rows(raw_rows)


def build_project_sample_master(
    output_root: Path,
    project_accession: str,
) -> AdnaProjectSampleMaster:
    output_root = Path(output_root)
    project_row = {
        row.project_accession: row for row in build_project_registry(output_root)
    }[project_accession]
    bundle_path = (
        output_root
        / "adna"
        / "governance"
        / "source_library"
        / "projects"
        / project_accession
        / "intake_dossier.json"
    )
    extraction_plan = ""
    if bundle_path.is_file():
        import json

        extraction_plan = str(
            json.loads(bundle_path.read_text(encoding="utf-8")).get(
                "extraction_plan", ""
            )
        )
    rows = build_project_sample_master_rows(output_root, project_accession)
    recovered_sample_count = sum(
        1
        for row in rows
        if row.source_native_identity_kind != "sequencing_experiment_accession"
    )
    final_sample_count = sum(
        1 for row in rows if row.sample_identity_resolution == "final"
    )
    expected_sample_count = project_row.expected_sample_count
    unresolved_sample_count = (
        None
        if expected_sample_count is None
        else max(expected_sample_count - final_sample_count, 0)
    )
    return AdnaProjectSampleMaster(
        project_accession=project_accession,
        species_latin_name=project_row.species_latin_name,
        species_common_name=resolve_species_definition(
            project_row.species_latin_name
        ).common_name,
        expected_sample_count=project_row.expected_sample_count,
        expected_sample_count_status=project_row.expected_sample_count_status,
        expected_sample_count_provenance=project_row.expected_sample_count_provenance,
        expected_sample_count_artifact_path=project_row.expected_sample_count_artifact_path,
        recovered_sample_count=recovered_sample_count,
        unresolved_sample_count=unresolved_sample_count,
        final_sample_count=final_sample_count,
        ambiguity_row_count=sum(
            1 for row in rows if row.sample_identity_resolution == "ambiguous"
        ),
        sample_identifier_status=project_row.sample_identifier_status,
        extraction_plan=extraction_plan,
        rows=rows,
    )


def build_cross_project_sample_master_completeness(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        master = build_project_sample_master(output_root, project.project_accession)
        rows.append(
            {
                "project_accession": master.project_accession,
                "species_latin_name": master.species_latin_name,
                "species_common_name": master.species_common_name,
                "expected_sample_count": master.expected_sample_count,
                "expected_sample_count_status": master.expected_sample_count_status,
                "expected_sample_count_provenance": master.expected_sample_count_provenance,
                "expected_sample_count_artifact_path": master.expected_sample_count_artifact_path,
                "recovered_sample_count": master.recovered_sample_count,
                "unresolved_sample_count": master.unresolved_sample_count,
                "final_sample_count": master.final_sample_count,
                "ambiguity_row_count": master.ambiguity_row_count,
                "sample_identifier_status": master.sample_identifier_status,
            }
        )
    return tuple(rows)


def build_sample_identity_ambiguity_ledger(
    output_root: Path,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for project in build_archive_project_catalog():
        for row in build_project_sample_master_rows(
            output_root, project.project_accession
        ):
            if row.sample_identity_resolution != "ambiguous":
                continue
            rows.append(
                {
                    "project_accession": row.project_accession,
                    "species_latin_name": row.species_latin_name,
                    "repo_stable_sample_id": row.repo_stable_sample_id,
                    "preferred_sample_label": row.preferred_sample_label,
                    "sample_ambiguity_note": row.sample_ambiguity_note,
                    "sample_lineage_path": row.sample_lineage_path,
                    "sample_lineage_locator": row.sample_lineage_locator,
                }
            )
    return tuple(rows)


def materialize_sample_master_library(output_root: Path) -> None:
    from ....core.files import write_json, write_text
    from ....core.tabular import render_csv_rows

    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    completeness_rows = list(
        build_cross_project_sample_master_completeness(output_root)
    )
    ambiguity_rows = list(build_sample_identity_ambiguity_ledger(output_root))

    for project in build_archive_project_catalog():
        master = build_project_sample_master(output_root, project.project_accession)
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        write_json(
            project_root / "sample_master.json",
            {
                "schema_version": "animal-project-sample-master.v1",
                **master.as_dict(),
            },
        )
        write_text(
            project_root / "sample_master.csv",
            render_csv_rows(
                tuple(
                    [row.as_dict() for row in master.rows]
                    if master.rows
                    else [_empty_sample_master_row(master)]
                )
            ),
        )

    write_json(
        source_root / "project_sample_master_completeness.json",
        {
            "schema_version": "animal-project-sample-master-completeness.v1",
            "rows": completeness_rows,
        },
    )
    write_text(
        source_root / "project_sample_master_completeness.csv",
        render_csv_rows(tuple(completeness_rows)),
    )
    write_json(
        source_root / "sample_identity_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-identity-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_identity_ambiguity_ledger.md",
        _render_sample_identity_ambiguity_markdown(ambiguity_rows),
    )
