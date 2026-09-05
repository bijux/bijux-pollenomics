"""Deterministic publication of the project sample-site library."""

from __future__ import annotations

from pathlib import Path

from .....core.files import write_json, write_text
from .....core.tabular import render_csv_rows
from ....sources.archive import build_archive_project_catalog
from .assembly import build_project_sample_site_rows
from .curation import build_sample_site_manual_curation_queue
from .rendering import (
    _empty_sample_site_row,
    _render_sample_site_ambiguity_markdown,
    _render_sample_site_manual_queue_markdown,
)
from .review import (
    build_project_sample_site_review_rows,
    build_sample_site_ambiguity_ledger,
)


def materialize_project_sample_site_library(output_root: Path) -> None:
    output_root = Path(output_root)
    source_root = output_root / "adna" / "governance" / "source_library"
    source_root.mkdir(parents=True, exist_ok=True)

    review_rows = list(build_project_sample_site_review_rows(output_root))
    ambiguity_rows = list(build_sample_site_ambiguity_ledger(output_root))
    queue_rows = list(build_sample_site_manual_curation_queue(output_root))

    for project in build_archive_project_catalog():
        project_root = source_root / "projects" / project.project_accession
        project_root.mkdir(parents=True, exist_ok=True)
        sample_site_rows = [
            row.as_dict()
            for row in build_project_sample_site_rows(
                output_root, project.project_accession
            )
        ]
        write_json(
            project_root / "sample_sites.json",
            {
                "schema_version": "animal-project-sample-sites.v1",
                "project_accession": project.project_accession,
                "species_latin_name": project.species_latin_name,
                "row_count": len(sample_site_rows),
                "rows": sample_site_rows,
            },
        )
        write_text(
            project_root / "sample_sites.csv",
            render_csv_rows(
                tuple(sample_site_rows)
                if sample_site_rows
                else (_empty_sample_site_row(project),)
            ),
        )

    write_json(
        source_root / "project_sample_site_review.json",
        {
            "schema_version": "animal-project-sample-site-review.v1",
            "rows": review_rows,
        },
    )
    write_text(
        source_root / "project_sample_site_review.csv",
        render_csv_rows(tuple(review_rows)),
    )
    write_json(
        source_root / "sample_site_ambiguity_ledger.json",
        {
            "schema_version": "animal-sample-site-ambiguity-ledger.v1",
            "rows": ambiguity_rows,
        },
    )
    write_text(
        source_root / "sample_site_ambiguity_ledger.md",
        _render_sample_site_ambiguity_markdown(ambiguity_rows),
    )
    write_json(
        source_root / "sample_site_manual_curation_queue.json",
        {
            "schema_version": "animal-sample-site-manual-curation-queue.v1",
            "rows": queue_rows,
        },
    )
    write_text(
        source_root / "sample_site_manual_curation_queue.md",
        _render_sample_site_manual_queue_markdown(queue_rows),
    )
