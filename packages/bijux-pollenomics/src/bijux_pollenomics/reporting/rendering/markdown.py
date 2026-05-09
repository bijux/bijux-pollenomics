from __future__ import annotations

from ...publication_policy import (
    build_country_report_policy,
    build_sample_inventory_policy,
)
from ..models import CountryReport
from ..presentation.text import escape_pipes

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
    map_publication_contract_json_name: str,
    map_publication_contract_markdown_name: str,
    point_traceability_json_name: str,
    point_traceability_markdown_name: str,
    extra_artifacts: list[tuple[str, str]],
    map_publication_contract: dict[str, object],
    animal_atlas_summary: dict[str, object] | None = None,
) -> str:
    """Render a README for a shared multi-country map bundle."""
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
    layer_rows = (
        "\n".join(
            f"| {escape_pipes(str(row['label']))} | `{row['publication_role']}` | {escape_pipes(str(row['coverage_label']))} | `{row['count']}` |"
            for row in map_publication_contract.get("layer_rows", [])
        )
        or "| No visible layers | `-` | - | `0` |"
    )
    filter_lines = (
        "\n".join(
            f"- {escape_pipes(str(label))}"
            for label in map_publication_contract.get("filter_surfaces", [])
        )
        or "- No governed filter surfaces"
    )
    caveat_lines = (
        "\n".join(
            f"- {escape_pipes(str(label))}"
            for label in map_publication_contract.get("visible_caveats", [])
        )
        or "- No governed caveats"
    )
    animal_section = ""
    if (
        animal_atlas_summary
        and int(animal_atlas_summary.get("total_locality_points", 0)) > 0
    ):
        layer_group_lines = (
            "\n".join(
                f"- {label}" for label in animal_atlas_summary.get("layer_groups", [])
            )
            or "- No animal layer groups shipped"
        )
        animal_filter_lines = (
            "\n".join(
                f"- {label}"
                for label in animal_atlas_summary.get("filter_surfaces", [])
            )
            or "- No animal-specific filters shipped"
        )
        ui_lines = (
            "\n".join(
                f"- {label}" for label in animal_atlas_summary.get("ui_surfaces", [])
            )
            or "- No animal-specific inspection surfaces shipped"
        )
        caution_lines = (
            "\n".join(
                f"- {label}"
                for label in animal_atlas_summary.get("visible_caveats", [])
            )
            or "- No animal-specific caveats shipped"
        )
        confidence_rows = (
            "\n".join(
                f"| {escape_pipes(str(label))} | {count} |"
                for label, count in sorted(
                    animal_atlas_summary.get("coordinate_confidence_counts", {}).items()
                )
            )
            or "| No visible coordinate-confidence counts | 0 |"
        )
        species_lines = (
            "\n".join(
                f"| {escape_pipes(str(row.get('common_name', '')))} | {escape_pipes(str(row.get('latin_name', '')))} | {escape_pipes(str(row.get('animal_scope', '')))} | {row.get('locality_count', 0)} |"
                for row in animal_atlas_summary.get("species_layers", [])
            )
            or "| No animal species layers shipped | - | - | 0 |"
        )
        animal_section = f"""

## Animal aDNA Layers

- Total animal locality points: `{animal_atlas_summary["total_locality_points"]}`
- Shipped animal species: `{animal_atlas_summary["total_species"]}`
- Domesticated-core species layers: `{animal_atlas_summary["domesticated_species_count"]}`
- Comparator species layers: `{animal_atlas_summary["comparator_species_count"]}`

### Layer Groups

{layer_group_lines}

### Public Animal Filters

{animal_filter_lines}

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
    return f"""# {title}

This shared interactive map bundle was generated on `{generated_on}` from Homo
sapiens AADR `{version}` plus any governed contextual and animal surfaces that
the active scope contract allows.

{map_publication_contract["scope_summary"]}

## Included Countries

| Country | Unique samples |
| --- | ---: |
{rows}

## Bundle Notes

- This bundle is a generated publication artifact, not a source dataset.
- Local leaflet assets are copied into `./_map_assets` so the HTML does not depend on CDN-hosted library files.
- Basemap tiles are still requested from the active cartographic provider at runtime, so an offline browser session will not display background tiles.
- The interactive map presents the records and overlays that were generated into this bundle. Ranking artifacts are published alongside it and carry stricter evidence boundaries than the map view itself.
- Default basemap: `{map_publication_contract["default_basemap"]}`
- {map_publication_contract["bounds_summary"]}

## Output Files

- Interactive map: [`{map_html_name}`](./{map_html_name})
- Combined GeoJSON: [`{geojson_name}`](./{geojson_name})
- Machine-readable summary: [`{summary_json_name}`](./{summary_json_name})
- Map publication contract JSON: [`{map_publication_contract_json_name}`](./{map_publication_contract_json_name})
- Map publication contract markdown: [`{map_publication_contract_markdown_name}`](./{map_publication_contract_markdown_name})
- Point traceability JSON: [`{point_traceability_json_name}`](./{point_traceability_json_name})
- Point traceability markdown: [`{point_traceability_markdown_name}`](./{point_traceability_markdown_name})
{artifact_block}

## Visible Layer Contract

| Layer | Publication role | Coverage posture | Visible records |
| --- | --- | --- | ---: |
{layer_rows}

## Governed Filters

{filter_lines}

## Scope Caveats

{caveat_lines}
{animal_section}
"""
