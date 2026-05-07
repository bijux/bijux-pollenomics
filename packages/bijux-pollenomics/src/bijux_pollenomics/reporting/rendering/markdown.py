from __future__ import annotations

from ...publication_policy import (
    build_country_report_policy,
    build_multi_country_map_policy,
    build_sample_inventory_policy,
)
from ..models import CountryReport
from ..shared.text import escape_pipes

__all__ = [
    "render_multi_country_map_markdown",
    "render_sample_markdown",
    "render_summary_markdown",
]


def render_summary_markdown(
    report: CountryReport,
    samples_csv_name: str,
    localities_csv_name: str,
    geojson_name: str,
    sample_markdown_name: str,
    summary_json_name: str,
    map_reference: tuple[str, str] | None,
    animal_section_markdown: str = "",
) -> str:
    """Render the country summary README."""
    policy = build_country_report_policy(report)
    latitude_values = [sample.latitude for sample in report.samples]
    longitude_values = [sample.longitude for sample in report.samples]
    latitude_range = (
        f"`{min(latitude_values):.6f}` to `{max(latitude_values):.6f}`"
        if latitude_values and longitude_values
        else "No latitude values available"
    )
    longitude_range = (
        f"`{min(longitude_values):.6f}` to `{max(longitude_values):.6f}`"
        if latitude_values and longitude_values
        else "No longitude values available"
    )

    dataset_lines = (
        "\n".join(
            f"| `{dataset}` | {count} |"
            for dataset, count in sorted(report.dataset_row_counts.items())
        )
        or "| No matching dataset rows | 0 |"
    )
    top_locality_lines = (
        "\n".join(
            f"| {escape_pipes(locality.locality)} | {locality.sample_count} | {locality.latitude_text} | {locality.longitude_text} | {escape_pipes(locality.time_label or '-')} | `{','.join(locality.datasets)}` |"
            for locality in report.localities[:15]
        )
        or "| No matching localities | 0 | - | - | - | - |"
    )

    map_line = ""
    if map_reference is not None:
        label, href = map_reference
        map_line = f'- Shared interactive map: <a href="{href}">{label}</a>\n'

    return f"""# {policy["title"]}

{policy["intro"]}
{policy["scope"]}

## Summary

- Country filter: `{report.country}`
- {policy["summary_label"]}: `{report.total_unique_samples}`
- Unique localities: `{report.total_unique_localities}`
- Latitude range: {latitude_range}
- Longitude range: {longitude_range}

{policy["empty_result_note"]}
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | {report.country} rows |
| --- | ---: |
{dataset_lines}

{policy["dedup_note"]}

## Output Files

{map_line}- Full sample inventory: [`{samples_csv_name}`](./{samples_csv_name})
- Locality summary: [`{localities_csv_name}`](./{localities_csv_name})
- Map-ready GeoJSON: [`{geojson_name}`](./{geojson_name})
- Machine-readable summary: [`{summary_json_name}`](./{summary_json_name})
- Full markdown sample table: [`{sample_markdown_name}`](./{sample_markdown_name})

## Top Localities

| Locality | Samples | Latitude | Longitude | BP coverage | Datasets |
| --- | ---: | ---: | ---: | --- | --- |
{top_locality_lines}
{animal_section_markdown}
"""


def render_sample_markdown(report: CountryReport) -> str:
    """Render the complete sample-level markdown table."""
    policy = build_sample_inventory_policy(report)
    lines = [
        f"# {policy['title']}",
        "",
        policy["summary"],
        "",
        "| Genetic ID | Master ID | Group ID | Locality | Latitude | Longitude | Publication | Full Date | Data Type | Sex | Datasets |",
        "| --- | --- | --- | --- | ---: | ---: | --- | --- | --- | --- | --- |",
    ]
    for sample in report.samples:
        lines.append(
            "| "
            + " | ".join(
                [
                    escape_pipes(sample.genetic_id),
                    escape_pipes(sample.master_id),
                    escape_pipes(sample.group_id),
                    escape_pipes(sample.locality),
                    sample.latitude_text,
                    sample.longitude_text,
                    escape_pipes(sample.publication),
                    escape_pipes(sample.full_date),
                    escape_pipes(sample.data_type),
                    escape_pipes(sample.molecular_sex),
                    ",".join(sample.datasets),
                ]
            )
            + " |"
        )
    return "\n".join(lines) + "\n"


def render_multi_country_map_markdown(
    title: str,
    version: str,
    generated_on: str,
    countries: tuple[str, ...],
    country_sample_counts: dict[str, int],
    map_html_name: str,
    geojson_name: str,
    summary_json_name: str,
    extra_artifacts: list[tuple[str, str]],
    animal_atlas_summary: dict[str, object] | None = None,
) -> str:
    """Render a README for a shared multi-country map bundle."""
    policy = build_multi_country_map_policy(
        title=title,
        version=version,
        generated_on=generated_on,
    )
    rows = (
        "\n".join(
            f"| {country} | {country_sample_counts[country]} |" for country in countries
        )
        or "| No countries requested | 0 |"
    )
    artifact_lines = "\n".join(
        f"- {label}: [`{filename}`](./{filename})"
        for label, filename in extra_artifacts
    )
    artifact_block = artifact_lines if artifact_lines else ""
    animal_section = ""
    if animal_atlas_summary and int(animal_atlas_summary.get("total_locality_points", 0)) > 0:
        layer_group_lines = "\n".join(
            f"- {label}"
            for label in animal_atlas_summary.get("layer_groups", [])
        ) or "- No animal layer groups shipped"
        filter_lines = "\n".join(
            f"- {label}"
            for label in animal_atlas_summary.get("filter_surfaces", [])
        ) or "- No animal-specific filters shipped"
        ui_lines = "\n".join(
            f"- {label}"
            for label in animal_atlas_summary.get("ui_surfaces", [])
        ) or "- No animal-specific inspection surfaces shipped"
        caution_lines = "\n".join(
            f"- {label}"
            for label in animal_atlas_summary.get("visible_caveats", [])
        ) or "- No animal-specific caveats shipped"
        confidence_rows = "\n".join(
            f"| {escape_pipes(str(label))} | {count} |"
            for label, count in sorted(
                animal_atlas_summary.get("coordinate_confidence_counts", {}).items()
            )
        ) or "| No visible coordinate-confidence counts | 0 |"
        species_lines = "\n".join(
            f"| {escape_pipes(str(row.get('common_name', '')))} | {escape_pipes(str(row.get('latin_name', '')))} | {escape_pipes(str(row.get('animal_scope', '')))} | {row.get('locality_count', 0)} |"
            for row in animal_atlas_summary.get("species_layers", [])
        ) or "| No animal species layers shipped | - | - | 0 |"
        animal_section = f"""

## Animal aDNA Layers

- Total animal locality points: `{animal_atlas_summary["total_locality_points"]}`
- Shipped animal species: `{animal_atlas_summary["total_species"]}`
- Domesticated-core species layers: `{animal_atlas_summary["domesticated_species_count"]}`
- Comparator species layers: `{animal_atlas_summary["comparator_species_count"]}`

### Layer Groups

{layer_group_lines}

### Public Animal Filters

{filter_lines}

### Animal Inspection Surfaces

{ui_lines}

### Visible Coordinate Confidence

| Coordinate confidence | Visible mapped points |
| --- | ---: |
{confidence_rows}

### Visible Animal Caveats

{caution_lines}

### Shipped Animal Species Layers

| Common name | Latin name | Animal scope | Mapped locality points |
| --- | --- | --- | ---: |
{species_lines}
"""
    return f"""# {policy["title"]}

{policy["intro"]}
{policy["scope"]}

## Included Countries

| Country | Unique samples |
| --- | ---: |
{rows}

## Bundle Notes

- This bundle is a generated publication artifact, not a source dataset.
- Local leaflet assets are copied into `./_map_assets` so the HTML does not depend on CDN-hosted library files.
- Basemap tiles are still requested from the active cartographic provider at runtime, so an offline browser session will not display background tiles.
- The interactive map presents the records and overlays that were generated into this bundle. Ranking artifacts are published alongside it and carry stricter evidence boundaries than the map view itself.
- {policy["count_note"]}

## Output Files

- Interactive map: [`{map_html_name}`](./{map_html_name})
- Combined GeoJSON: [`{geojson_name}`](./{geojson_name})
- Machine-readable summary: [`{summary_json_name}`](./{summary_json_name})
{artifact_block}
{animal_section}
"""
