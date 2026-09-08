from __future__ import annotations

from pathlib import Path

from .....core.files import write_json, write_text
from .....core.tabular import render_csv_rows
from ....sources.archive import build_archive_project_catalog
from .completeness import (
    build_project_locality_completeness_rows,
    build_species_locality_completeness_rows,
)
from .conflicts import build_sample_locality_conflict_ledger
from .curation import build_sample_locality_manual_curation_workflow_rows
from .evidence_rows import build_project_sample_locality_evidence_rows
from .normalization import build_site_name_normalization_dictionary_rows
from .rendering import (
    _render_project_locality_substitution_ledger_markdown,
    _render_sample_locality_conflict_ledger_markdown,
    _render_sample_locality_manual_curation_workflow_markdown,
)
from .substitutions import build_project_locality_substitution_ledger
from .worksheets import build_project_locality_worksheet_rows


def materialize_project_sample_locality_evidence_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    conflict_rows = list(build_sample_locality_conflict_ledger(output_root))
    curation_rows = list(
        build_sample_locality_manual_curation_workflow_rows(output_root)
    )
    substitution_rows = list(build_project_locality_substitution_ledger(output_root))
    dictionary_rows = list(build_site_name_normalization_dictionary_rows(output_root))
    species_rows = list(build_species_locality_completeness_rows(output_root))
    project_rows = list(build_project_locality_completeness_rows(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        worksheet_rows = list(
            build_project_locality_worksheet_rows(
                output_root, project.project_accession
            )
        )
        packet_rows = list(
            build_project_sample_locality_evidence_rows(
                output_root, project.project_accession
            )
        )
        write_json(
            project_root / "locality_worksheet.json",
            {
                "schema_version": "animal-project-locality-worksheet.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(worksheet_rows),
                "rows": worksheet_rows,
            },
        )
        write_text(
            project_root / "locality_worksheet.csv",
            render_csv_rows(tuple(worksheet_rows)),
        )
        write_json(
            project_root / "sample_locality_evidence.json",
            {
                "schema_version": "animal-project-sample-locality-evidence.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(packet_rows),
                "rows": packet_rows,
            },
        )
        write_text(
            project_root / "sample_locality_evidence.csv",
            render_csv_rows(tuple(packet_rows)),
        )

    write_json(
        source_root / "sample_locality_conflict_ledger.json",
        {
            "schema_version": "animal-sample-locality-conflict-ledger.v1",
            "rows": conflict_rows,
        },
    )
    write_text(
        source_root / "sample_locality_conflict_ledger.md",
        _render_sample_locality_conflict_ledger_markdown(conflict_rows),
    )
    write_json(
        source_root / "sample_locality_manual_curation_workflow.json",
        {
            "schema_version": "animal-sample-locality-manual-curation-workflow.v1",
            "rows": curation_rows,
        },
    )
    write_text(
        source_root / "sample_locality_manual_curation_workflow.md",
        _render_sample_locality_manual_curation_workflow_markdown(curation_rows),
    )
    write_json(
        source_root / "project_locality_substitution_ledger.json",
        {
            "schema_version": "animal-project-locality-substitution-ledger.v1",
            "rows": substitution_rows,
        },
    )
    write_text(
        source_root / "project_locality_substitution_ledger.md",
        _render_project_locality_substitution_ledger_markdown(substitution_rows),
    )
    write_json(
        source_root / "site_name_normalization_dictionary.json",
        {
            "schema_version": "animal-site-name-normalization-dictionary.v1",
            "rows": dictionary_rows,
        },
    )
    write_text(
        source_root / "site_name_normalization_dictionary.csv",
        render_csv_rows(tuple(dictionary_rows)),
    )
    write_json(
        source_root / "species_locality_completeness.json",
        {
            "schema_version": "animal-species-locality-completeness.v1",
            "rows": species_rows,
        },
    )
    write_text(
        source_root / "species_locality_completeness.csv",
        render_csv_rows(tuple(species_rows)),
    )
    write_json(
        source_root / "project_locality_completeness.json",
        {
            "schema_version": "animal-project-locality-completeness.v1",
            "rows": project_rows,
        },
    )
    write_text(
        source_root / "project_locality_completeness.csv",
        render_csv_rows(tuple(project_rows)),
    )
