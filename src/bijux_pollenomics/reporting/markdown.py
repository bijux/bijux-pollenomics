from __future__ import annotations

from .models import CountryReport
from .utils import escape_pipes


def render_summary_markdown(
    report: CountryReport,
    samples_csv_name: str,
    localities_csv_name: str,
    geojson_name: str,
    sample_markdown_name: str,
    summary_json_name: str,
    map_reference: tuple[str, str] | None,
) -> str:
    """Render the country summary README."""
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

    dataset_lines = "\n".join(
        f"| `{dataset}` | {count} |"
        for dataset, count in sorted(report.dataset_row_counts.items())
    ) or "| No matching dataset rows | 0 |"
    top_locality_lines = "\n".join(
        f"| {escape_pipes(locality.locality)} | {locality.sample_count} | {locality.latitude_text} | {locality.longitude_text} | {escape_pipes(locality.time_label or '-')} | `{','.join(locality.datasets)}` |"
        for locality in report.localities[:15]
    ) or "| No matching localities | 0 | - | - | - | - |"

    map_line = ""
    if map_reference is not None:
        label, href = map_reference
        map_line = f'- Shared interactive map: <a href="{href}">{label}</a>\n'

    return f"""# {report.country} AADR {report.version} Report

This bundle was generated from the AADR `{report.version}` `.anno` files on `{report.generated_on}`.
It inventories only AADR sample rows that match the `{report.country}` country filter. Environmental and archaeology context layers are published in the shared map bundle, not duplicated here.

## Summary

- Country filter: `{report.country}`
- Unique AADR samples: `{report.total_unique_samples}`
- Unique localities: `{report.total_unique_localities}`
- Latitude range: {latitude_range}
- Longitude range: {longitude_range}

This country bundle is valid even when the filter returns zero AADR samples. In that case the CSV, GeoJSON, and markdown exports remain present so downstream checks can distinguish an empty result from a missing artifact.
Locality rows now preserve the combined BP coverage of the samples they aggregate.

## Dataset Coverage

| Dataset | {report.country} rows |
| --- | ---: |
{dataset_lines}

The report deduplicates samples by `genetic_id` across datasets. Dataset row counts can differ by coverage, but the combined inventory for `{report.country}` contains `{report.total_unique_samples}` unique samples in AADR `{report.version}`.

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
"""


def render_sample_markdown(report: CountryReport) -> str:
    """Render the complete sample-level markdown table."""
    lines = [
        f"# {report.country} AADR {report.version} Sample Inventory",
        "",
        f"Generated on `{report.generated_on}`. Total samples: `{report.total_unique_samples}`.",
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
) -> str:
    """Render a README for a shared multi-country map bundle."""
    rows = "\n".join(
        f"| {country} | {country_sample_counts[country]} |"
        for country in countries
    ) or "| No countries requested | 0 |"
    artifact_lines = "\n".join(
        f"- {label}: [`{filename}`](./{filename})"
        for label, filename in extra_artifacts
    )
    artifact_block = artifact_lines if artifact_lines else ""
    return f"""# {title}

This shared interactive map bundle was generated on `{generated_on}`.
It combines AADR `{version}` with whichever contextual datasets are present in the repository at generation time and copies those derived artifacts into this directory.

## Included Countries

| Country | Unique samples |
| --- | ---: |
{rows}

## Bundle Notes

- This bundle is a generated publication artifact, not a source dataset.
- Local leaflet assets are copied into `./_map_assets` so the HTML does not depend on CDN-hosted library files.
- Basemap tiles are still requested from the active cartographic provider at runtime, so an offline browser session will not display background tiles.
- The map does not rank, score, or reconcile disagreement between sources; it only presents the records and overlays that were generated into this bundle.
- Country sample counts in this README refer to AADR records. Context layers can have different geographic scope and record counts inside the map.

## Output Files

- Interactive map: [`{map_html_name}`](./{map_html_name})
- Combined GeoJSON: [`{geojson_name}`](./{geojson_name})
- Machine-readable summary: [`{summary_json_name}`](./{summary_json_name})
{artifact_block}
"""
