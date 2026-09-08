from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.sources.archive import build_archive_project_catalog
from bijux_pollenomics.core.files import write_json, write_text
from bijux_pollenomics.core.tabular import render_csv_rows

from .audits import (
    build_cross_project_sample_chronology_audit,
    build_date_evidence_gap_queue,
    build_project_chronology_completeness_rows,
    build_project_sample_chronology_review_rows,
    build_sample_chronology_ambiguity_ledger,
    build_sample_chronology_conflict_ledger,
    build_sample_chronology_precision_audit,
    build_sample_chronology_provenance_rows,
    build_sample_chronology_review_rows,
    build_species_chronology_completeness_rows,
)
from .rendering import (
    _empty_sample_chronology_provenance_row,
    _empty_sample_chronology_row,
    _render_date_evidence_gap_queue_markdown,
    _render_sample_chronology_ambiguity_markdown,
    _render_sample_chronology_audit_markdown,
    _render_sample_chronology_conflict_markdown,
    _render_sample_chronology_precision_audit_markdown,
    _render_sample_chronology_provenance_markdown,
    _render_sample_chronology_review_markdown,
)
from .rows import build_project_sample_chronology_rows


def materialize_project_sample_chronology_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    project_review_rows = list(build_project_sample_chronology_review_rows(output_root))
    audit_payload = build_cross_project_sample_chronology_audit(output_root)
    ambiguity_rows = list(build_sample_chronology_ambiguity_ledger(output_root))
    conflict_rows = list(build_sample_chronology_conflict_ledger(output_root))
    precision_audit_payload = build_sample_chronology_precision_audit(output_root)
    gap_queue_rows = list(build_date_evidence_gap_queue(output_root))
    species_rows = list(build_species_chronology_completeness_rows(output_root))
    project_rows = list(build_project_chronology_completeness_rows(output_root))
    sample_review_rows = list(build_sample_chronology_review_rows(output_root))
    provenance_rows = list(build_sample_chronology_provenance_rows(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        chronology_rows = [
            row.as_dict()
            for row in build_project_sample_chronology_rows(
                output_root, project.project_accession
            )
        ]
        evidence_payload = {
            "schema_version": "animal-project-sample-chronology-evidence.v1",
            "project_accession": project.project_accession,
            "species_latin_name": project.species_latin_name,
            "row_count": len(chronology_rows),
            "rows": chronology_rows,
        }
        write_json(
            project_root / "sample_chronology.json",
            {
                "schema_version": "animal-project-sample-chronology.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(chronology_rows),
                "rows": chronology_rows,
            },
        )
        write_text(
            project_root / "sample_chronology.csv",
            render_csv_rows(
                tuple(chronology_rows)
                if chronology_rows
                else (_empty_sample_chronology_row(project),)
            ),
        )
        write_json(project_root / "sample_chronology_evidence.json", evidence_payload)
        write_text(
            project_root / "sample_chronology_evidence.csv",
            render_csv_rows(
                tuple(chronology_rows)
                if chronology_rows
                else (_empty_sample_chronology_row(project),)
            ),
        )
        project_provenance_rows = tuple(
            row
            for row in provenance_rows
            if row["project_accession"] == project.project_accession
        )
        write_json(
            project_root / "sample_chronology_provenance.json",
            {
                "schema_version": "animal-project-sample-chronology-provenance.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(project_provenance_rows),
                "rows": list(project_provenance_rows),
            },
        )
        write_text(
            project_root / "sample_chronology_provenance.csv",
            render_csv_rows(
                project_provenance_rows
                if project_provenance_rows
                else (_empty_sample_chronology_provenance_row(project),)
            ),
        )

    write_json(
        source_root / "project_sample_chronology_review.json",
        {
            "schema_version": "animal-project-sample-chronology-review.v1",
            "rows": project_review_rows,
        },
    )
    write_text(
        source_root / "project_sample_chronology_review.csv",
        render_csv_rows(tuple(project_review_rows)),
    )
    write_json(
        source_root / "sample_chronology_normalization_audit.json", audit_payload
    )
    write_text(
        source_root / "sample_chronology_normalization_audit.md",
        _render_sample_chronology_audit_markdown(audit_payload),
    )
    write_json(
        source_root / "sample_chronology_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-chronology-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_ambiguity_ledger.md",
        _render_sample_chronology_ambiguity_markdown(ambiguity_rows),
    )
    write_json(
        source_root / "sample_chronology_conflict_ledger.json",
        {
            "schema_version": "animal-sample-chronology-conflict-ledger.v1",
            "rows": conflict_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_conflict_ledger.md",
        _render_sample_chronology_conflict_markdown(conflict_rows),
    )
    write_json(
        source_root / "sample_chronology_precision_audit.json", precision_audit_payload
    )
    write_text(
        source_root / "sample_chronology_precision_audit.md",
        _render_sample_chronology_precision_audit_markdown(precision_audit_payload),
    )
    write_json(
        source_root / "species_chronology_completeness.json",
        {
            "schema_version": "animal-species-chronology-completeness.v1",
            "rows": species_rows,
        },
    )
    write_text(
        source_root / "species_chronology_completeness.csv",
        render_csv_rows(tuple(species_rows)),
    )
    write_json(
        source_root / "project_chronology_completeness.json",
        {
            "schema_version": "animal-project-chronology-completeness.v1",
            "rows": project_rows,
        },
    )
    write_text(
        source_root / "project_chronology_completeness.csv",
        render_csv_rows(tuple(project_rows)),
    )
    write_json(
        source_root / "sample_chronology_review.json",
        {
            "schema_version": "animal-sample-chronology-review.v1",
            "rows": sample_review_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_review.md",
        _render_sample_chronology_review_markdown(sample_review_rows),
    )
    write_json(
        source_root / "sample_chronology_provenance_review.json",
        {
            "schema_version": "animal-sample-chronology-provenance-review.v1",
            "rows": provenance_rows,
        },
    )
    write_text(
        source_root / "sample_chronology_provenance_review.md",
        _render_sample_chronology_provenance_markdown(provenance_rows),
    )
    write_json(
        source_root / "date_evidence_gap_queue.json",
        {
            "schema_version": "animal-date-evidence-gap-queue.v1",
            "rows": gap_queue_rows,
        },
    )
    write_text(
        source_root / "date_evidence_gap_queue.md",
        _render_date_evidence_gap_queue_markdown(gap_queue_rows),
    )
