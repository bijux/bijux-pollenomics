from __future__ import annotations

import csv
import io
from pathlib import Path

from .ena import build_archive_project_catalog
from .project_context import build_species_freshness_rows, resolve_project_context
from .tracked_species import TRACKED_ADNA_SPECIES

__all__ = [
    "build_cross_species_archive_inventory",
    "build_cross_species_bibliography",
    "build_cross_species_coverage_dashboard",
    "build_public_animal_output_audit",
    "build_shipped_adna_product_audit",
    "build_species_freshness_table",
    "render_csv_rows",
    "render_public_animal_output_audit_markdown",
]


def build_cross_species_bibliography() -> tuple[dict[str, object], ...]:
    """Deduplicate cited animal aDNA literature across all tracked species."""
    grouped: dict[str, dict[str, object]] = {}
    for project in build_archive_project_catalog():
        linkage = project.paper_linkage
        if linkage is None:
            continue
        key = linkage.doi or linkage.paper_title.casefold()
        current = grouped.setdefault(
            key,
            {
                "paper_title": linkage.paper_title,
                "paper_doi": linkage.doi,
                "journal_title": linkage.journal_title,
                "publication_year": linkage.publication_year,
                "reference_kind": linkage.reference_kind,
                "species_latin_names": set(),
                "project_accessions": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
        current["project_accessions"].add(project.project_accession)
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "paper_title": row["paper_title"],
                "paper_doi": row["paper_doi"],
                "journal_title": row["journal_title"],
                "publication_year": row["publication_year"],
                "reference_kind": row["reference_kind"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "project_accessions": sorted(row["project_accessions"]),
                "species_count": len(row["species_latin_names"]),
                "project_count": len(row["project_accessions"]),
            }
        )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item["publication_year"] or 0,
                item["paper_title"].casefold(),
            ),
            reverse=True,
        )
    )


def build_cross_species_archive_inventory() -> tuple[dict[str, object], ...]:
    """Deduplicate the tracked cross-species archive inventory."""
    grouped: dict[tuple[str, str], dict[str, object]] = {}
    for project in build_archive_project_catalog():
        key = (project.source_family, project.project_accession)
        current = grouped.setdefault(
            key,
            {
                "source_family": project.source_family,
                "project_accession": project.project_accession,
                "metadata_url": project.metadata_url,
                "result_kind": project.result_kind,
                "archive_status": project.archive_status,
                "evidence_strength": project.as_dict()["evidence_strength"],
                "access_policy": project.access_policy,
                "species_latin_names": set(),
            },
        )
        current["species_latin_names"].add(project.species_latin_name)
    rows = []
    for row in grouped.values():
        rows.append(
            {
                "source_family": row["source_family"],
                "project_accession": row["project_accession"],
                "metadata_url": row["metadata_url"],
                "result_kind": row["result_kind"],
                "archive_status": row["archive_status"],
                "evidence_strength": row["evidence_strength"],
                "access_policy": row["access_policy"],
                "species_latin_names": sorted(row["species_latin_names"]),
                "species_count": len(row["species_latin_names"]),
            }
        )
    return tuple(
        sorted(rows, key=lambda item: (item["source_family"], item["project_accession"]))
    )


def build_species_freshness_table() -> tuple[dict[str, object], ...]:
    """Return one freshness row per tracked animal species."""
    rows = build_species_freshness_rows(build_archive_project_catalog())
    tracked = set(TRACKED_ADNA_SPECIES)
    return tuple(
        row for row in rows if row["species_latin_name"] in tracked
    )


def build_cross_species_coverage_dashboard(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Report which animal evidence surfaces are actually shipped per species."""
    rows = [
        _build_species_coverage_row(
            data_root=Path(data_root),
            report_root=Path(report_root),
            species_name=species_name,
        )
        for species_name in TRACKED_ADNA_SPECIES
    ]
    return {
        "schema_version": "adna-cross-species-coverage-dashboard.v1",
        "rows": rows,
    }


def build_shipped_adna_product_audit(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Build a fuller product audit for what animal aDNA the repo really ships."""
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    rows = dashboard["rows"]
    return {
        "schema_version": "adna-shipped-product-audit.v1",
        "tracked_species_count": len(rows),
        "species_with_locality_artifacts": sum(
            1 for row in rows if row["normalized_locality_artifact_present"]
        ),
        "species_with_country_outputs": sum(
            1 for row in rows if row["country_output_count"] > 0
        ),
        "species_with_atlas_layers": sum(
            1 for row in rows if row["atlas_layer_count"] > 0
        ),
        "rows": rows,
        "missing_public_outputs": [
            row["species_latin_name"]
            for row in rows
            if row["country_output_count"] == 0 and row["atlas_layer_count"] == 0
        ],
    }


def build_public_animal_output_audit(
    data_root: Path,
    report_root: Path,
) -> dict[str, object]:
    """Summarize what the shipped public report tree currently exposes for animal aDNA."""
    report_root = Path(report_root)
    dashboard = build_cross_species_coverage_dashboard(data_root, report_root)
    countries = tuple(
        path.name
        for path in sorted(report_root.iterdir())
        if path.is_dir() and path.name not in {"nordic-atlas", "_map_assets"}
    ) if report_root.exists() else ()
    atlas_readme = report_root / "nordic-atlas" / "README.md"
    atlas_notes = (
        atlas_readme.read_text(encoding="utf-8")
        if atlas_readme.exists()
        else ""
    )
    return {
        "schema_version": "animal-output-audit.v1",
        "report_root": str(report_root),
        "countries": list(countries),
        "atlas_bundle_present": (report_root / "nordic-atlas").is_dir(),
        "country_bundle_count": len(countries),
        "atlas_notes": atlas_notes,
        "species_rows": dashboard["rows"],
    }


def render_public_animal_output_audit_markdown(payload: dict[str, object]) -> str:
    """Render the shipped public animal-output audit as reader-facing markdown."""
    rows = payload["species_rows"]
    lines = [
        "# Animal output audit",
        "",
        f"- Report root: `{payload['report_root']}`",
        f"- Atlas bundle present: `{str(payload['atlas_bundle_present']).lower()}`",
        f"- Country bundle count: `{payload['country_bundle_count']}`",
        "",
        "## Species output counts",
        "",
        "| Species | Atlas layers | Country outputs | Locality artifact shipped | Nordic lead count |",
        "| --- | ---: | ---: | --- | ---: |",
    ]
    for row in rows:
        lines.append(
            f"| {row['species_latin_name']} | {row['atlas_layer_count']} | "
            f"{row['country_output_count']} | "
            f"{str(row['normalized_locality_artifact_present']).lower()} | "
            f"{row['nordic_unmapped_lead_count']} |"
        )
    lines.extend(
        [
            "",
            "The current public report tree still ships no mapped non-human animal atlas "
            "layers or country bundles. The species rows above stay zero until those "
            "artifacts become real tracked report outputs.",
            "",
        ]
    )
    return "\n".join(lines)


def render_csv_rows(rows: tuple[dict[str, object], ...]) -> str:
    """Render homogeneous dict rows as CSV."""
    if not rows:
        return ""
    fieldnames = tuple(rows[0].keys())
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow(
            {
                key: _csv_value(value)
                for key, value in row.items()
            }
        )
    return buffer.getvalue()


def _build_species_coverage_row(
    *,
    data_root: Path,
    report_root: Path,
    species_name: str,
) -> dict[str, object]:
    from .species import resolve_species_definition

    species = resolve_species_definition(species_name)
    species_root = data_root / "adna" / species.slug
    context_rows = [
        resolve_project_context(project)
        for project in build_archive_project_catalog()
        if project.species_latin_name == species.latin_name
    ]
    country_output_count = _country_output_count(
        report_root,
        species.latin_name,
        species.common_name,
    )
    atlas_layer_count = _atlas_layer_count(
        report_root / "nordic-atlas",
        species.latin_name,
        species.common_name,
    )
    return {
        "species_latin_name": species.latin_name,
        "species_common_name": species.common_name,
        "raw_inventory_present": (species_root / "raw" / "archive_inventory.csv").is_file(),
        "citation_manifest_present": (
            species_root / "manifests" / "citation_manifest.csv"
        ).is_file(),
        "normalized_project_summary_present": (
            species_root / "normalized" / "project_summaries.csv"
        ).is_file(),
        "normalized_locality_artifact_present": (
            species_root / "normalized" / "locality_summaries.csv"
        ).is_file(),
        "review_markdown_present": (species_root / "review" / "species_review.md").is_file(),
        "review_json_present": (species_root / "review" / "species_review.json").is_file(),
        "country_output_count": country_output_count,
        "atlas_layer_count": atlas_layer_count,
        "nordic_unmapped_lead_count": sum(
            1 for row in context_rows if row.nordic_relevance == "nordic_relevant_unmapped"
        ),
    }


def _species_output_count(
    root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    if not root.exists():
        return 0
    del common_name
    latin_token = latin_name.casefold()
    explicit_markers = (
        "species_latin_name",
        "species_common_name",
        "support_class",
        "nordic_relevance",
    )
    matches = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.name in {
            "animal_output_audit.json",
            "animal_output_audit.md",
            "published_reports_summary.json",
        }:
            continue
        if path.suffix.lower() not in {".json", ".md", ".csv", ".geojson", ".html"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").casefold()
        if latin_token in text and any(marker in text for marker in explicit_markers):
            matches += 1
    return matches


def _country_output_count(
    report_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    if not report_root.exists():
        return 0
    return sum(
        1
        for path in report_root.iterdir()
        if path.is_dir()
        and path.name not in {"nordic-atlas", "_map_assets"}
        and _species_output_count(path, latin_name, common_name) > 0
    )


def _atlas_layer_count(
    atlas_root: Path,
    latin_name: str,
    common_name: str,
) -> int:
    return _species_output_count(atlas_root, latin_name, common_name)


def _csv_value(value: object) -> object:
    if isinstance(value, (list, tuple)):
        return ";".join(str(item) for item in value)
    if isinstance(value, bool):
        return str(value).lower()
    return value
