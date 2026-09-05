from __future__ import annotations

from ....presentation.text import escape_pipes
from ..models import CountryAnimalOutputBundle


def render_country_animal_citations_markdown(bundle: CountryAnimalOutputBundle) -> str:
    """Render a public-facing citation appendix for one country's animal evidence."""
    lines = [
        f"# {bundle.country} animal aDNA citations",
        "",
        "This appendix lists the tracked animal-aDNA papers that currently back the",
        f"`{bundle.country}` country bundle.",
        "",
        "| Species | Project accession | Paper title | DOI | Year | Sample rows | Locality rows | Supplementary support | Source posture | Assignment posture |",
        "| --- | --- | --- | --- | ---: | ---: | ---: | --- | --- | --- |",
    ]
    if not bundle.citations:
        lines.append(
            "| No animal country citations yet | - | - | - | 0 | 0 | 0 | - | - | - |"
        )
    else:
        for row in bundle.citations:
            doi = str(row["paper_doi"])
            doi_cell = f"[{escape_pipes(doi)}](https://doi.org/{doi})" if doi else "-"
            lines.append(
                f"| {escape_pipes(str(row['species_latin_name']))} | "
                f"{escape_pipes(str(row['project_accession']))} | "
                f"{escape_pipes(str(row['paper_title']) or '-')} | "
                f"{doi_cell} | "
                f"{escape_pipes(str(row['publication_year']) or '0')} | "
                f"{row['sample_row_count']} | "
                f"{row['locality_row_count']} | "
                f"{escape_pipes(str(row['supplementary_support']) or '-')} | "
                f"{escape_pipes(str(row['source_posture']) or '-')} | "
                f"{escape_pipes(str(row['country_assignment_confidence']))} |"
            )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_samples_markdown(bundle: CountryAnimalOutputBundle) -> str:
    """Render one markdown table of country-resolved animal sample rows."""
    lines = [
        f"# {bundle.country} animal aDNA sample rows",
        "",
        "This table lists the exact curated animal sample rows that currently feed the",
        f"`{bundle.country}` country surface. Each row keeps the exact sample, site,",
        "chronology, and coordinate evidence locator that justifies publication.",
        "",
        "| Species | Sample record | Project accession | Locality | Assignment posture | Coordinate posture | Sample evidence | Site evidence | Chronology evidence | Coordinate evidence | Citation |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    if not bundle.sample_rows:
        lines.append(
            "| No country-resolved animal sample rows yet | - | - | - | - | - | - | - |"
        )
        lines.append("")
        return "\n".join(lines)
    for row in bundle.sample_rows:
        doi = str(row["paper_doi"])
        citation = f"[{escape_pipes(doi)}](https://doi.org/{doi})" if doi else "-"
        sample_locator = format_evidence_locator(
            str(row.get("sample_lineage_path", "")),
            str(row.get("sample_lineage_locator", "")),
        )
        site_locator = format_evidence_locator(
            str(row.get("site_evidence_path", "")),
            str(row.get("site_evidence_locator", "")),
        )
        chronology_locator = format_evidence_locator(
            str(row.get("chronology_provenance_path", "")),
            str(row.get("chronology_provenance_locator", "")),
        )
        coordinate_locator = format_evidence_locator(
            str(row.get("coordinate_provenance_path", "")),
            str(row.get("coordinate_provenance_locator", "")),
        )
        lines.append(
            f"| {escape_pipes(str(row['species_latin_name']))} | "
            f"{escape_pipes(str(row['sample_record_id']))} | "
            f"{escape_pipes(str(row['project_accession']))} | "
            f"{escape_pipes(str(row['locality']) or '-')} | "
            f"{escape_pipes(str(row['country_assignment_confidence']))} | "
            f"{escape_pipes(str(row['coordinate_basis']))} / "
            f"{escape_pipes(str(row['coordinate_confidence']))} | "
            f"{escape_pipes(sample_locator)} | "
            f"{escape_pipes(site_locator)} | "
            f"{escape_pipes(chronology_locator)} | "
            f"{escape_pipes(coordinate_locator)} | "
            f"{citation} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_country_animal_warnings_markdown(bundle: CountryAnimalOutputBundle) -> str:
    """Render one warning appendix for country-level animal evidence limits."""
    lines = [
        f"# {bundle.country} animal aDNA warnings",
        "",
        "These warnings make the country-level animal surface honest instead of",
        "letting regional, comparator, or approximate evidence look cleaner than it is.",
        "",
    ]
    if not bundle.warnings:
        lines.append(
            "- No additional warnings. The current country bundle has no tracked animal rows."
        )
        lines.append("")
        return "\n".join(lines)
    for row in bundle.warnings:
        lines.append(f"- `{row['severity']}` `{row['warning_code']}`: {row['message']}")
    lines.append("")
    return "\n".join(lines)


def render_country_animal_section(
    bundle: CountryAnimalOutputBundle,
    *,
    summary_json_name: str,
    samples_csv_name: str,
    samples_markdown_name: str,
    species_csv_name: str,
    localities_geojson_name: str,
    citations_markdown_name: str,
    warnings_markdown_name: str,
) -> str:
    """Render the README addendum for country-level animal outputs."""
    if not bundle.species_rows:
        return f"""

## Animal aDNA Country Outputs

No tracked non-human animal locality lead is currently assignable to `{bundle.country}`
with the current repository rules, so this country bundle ships only the human AADR
surface for now.
"""
    species_lines = "\n".join(
        f"| {escape_pipes(str(row['species_common_name']))} | "
        f"{escape_pipes(str(row['species_latin_name']))} | "
        f"{escape_pipes(str(row['animal_scope']))} | "
        f"{row['mapped_locality_count']} | "
        f"{escape_pipes(str(row['assignment_confidence']))} | "
        f"{escape_pipes(str(row['caution_note']))} |"
        for row in bundle.species_rows
    )
    return f"""

## Animal aDNA Country Outputs

- Tracked animal species represented: `{len(bundle.species_rows)}`
- Country-resolved animal sample rows: `{len(bundle.sample_rows)}`
- Country-resolved animal locality rows: `{len(bundle.localities)}`
- Supporting tracked projects: `{len(bundle.citations)}`
- Sample evidence-backed rows: `{bundle.evidence_quality_summary["sample_lineage_backed_sample_count"]}`
- Chronology-provenance-backed rows: `{bundle.evidence_quality_summary["chronology_provenance_backed_sample_count"]}`
- Coordinate-provenance-backed rows: `{bundle.evidence_quality_summary["coordinate_provenance_backed_sample_count"]}`

### Animal Output Files

- Machine-readable animal summary: [`{summary_json_name}`](./{summary_json_name})
- Animal sample rows CSV: [`{samples_csv_name}`](./{samples_csv_name})
- Animal sample rows markdown: [`{samples_markdown_name}`](./{samples_markdown_name})
- Animal species summary CSV: [`{species_csv_name}`](./{species_csv_name})
- Animal localities GeoJSON: [`{localities_geojson_name}`](./{localities_geojson_name})
- Animal citation appendix: [`{citations_markdown_name}`](./{citations_markdown_name})
- Animal warning appendix: [`{warnings_markdown_name}`](./{warnings_markdown_name})

### Country-Resolved Animal Species

| Common name | Latin name | Animal scope | Locality rows | Assignment posture | Caution |
| --- | --- | --- | ---: | --- | --- |
{species_lines}
"""

def format_evidence_locator(path: str, locator: str) -> str:
    path = path.strip()
    locator = locator.strip()
    if path and locator:
        return f"{path}#{locator}"
    if path:
        return path
    if locator:
        return locator
    return "-"
