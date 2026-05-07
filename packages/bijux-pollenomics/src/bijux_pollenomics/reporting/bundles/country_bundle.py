from __future__ import annotations

from collections.abc import Callable, Iterable
from pathlib import Path

from ..adna.country_outputs import (
    build_country_animal_output_bundle,
    render_country_animal_citations_markdown,
    render_country_animal_samples_markdown,
    render_country_animal_section,
    render_country_animal_warnings_markdown,
    write_country_animal_localities_geojson,
    write_country_animal_samples_csv,
    write_country_animal_species_csv,
)
from ..models import CountryReport, LocalitySummary, SampleRecord
from .paths import CountryBundlePaths, build_country_bundle_paths
from .summary_builders.country import build_country_bundle_manifest

__all__ = ["publish_country_report_bundle"]


def publish_country_report_bundle(
    staging_output_dir: Path,
    *,
    report: CountryReport,
    country: str,
    version: str,
    map_reference: tuple[str, str] | None,
    build_country_report_summary_fn: Callable[
        [CountryReport, CountryBundlePaths], dict[str, object]
    ],
    render_sample_markdown_fn: Callable[[CountryReport], str],
    render_summary_markdown_fn: Callable[..., str],
    write_localities_csv_fn: Callable[[Path, Iterable[LocalitySummary]], None],
    write_samples_csv_fn: Callable[[Path, Iterable[SampleRecord]], None],
    write_samples_geojson_fn: Callable[[Path, Iterable[SampleRecord]], None],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
    context_root: Path | None = None,
) -> None:
    """Write the full country report artifact bundle into one staging directory."""
    bundle_paths = build_country_bundle_paths(
        output_dir=staging_output_dir,
        country=country,
        version=version,
    )
    write_samples_csv_fn(bundle_paths.samples_csv_path, report.samples)
    write_localities_csv_fn(bundle_paths.localities_csv_path, report.localities)
    write_samples_geojson_fn(bundle_paths.samples_geojson_path, report.samples)
    animal_section_markdown = ""
    if context_root is not None:
        animal_bundle = build_country_animal_output_bundle(
            data_root=context_root,
            country=country,
            version=version,
            generated_on=report.generated_on,
        )
        write_summary_json_fn(
            bundle_paths.animal_summary_json_path,
            animal_bundle.as_dict(),
        )
        write_country_animal_samples_csv(
            bundle_paths.animal_samples_csv_path,
            animal_bundle,
        )
        write_country_animal_species_csv(
            bundle_paths.animal_species_csv_path,
            animal_bundle,
        )
        write_country_animal_localities_geojson(
            bundle_paths.animal_localities_geojson_path,
            animal_bundle,
        )
        bundle_paths.animal_samples_markdown_path.write_text(
            render_country_animal_samples_markdown(animal_bundle),
            encoding="utf-8",
        )
        bundle_paths.animal_citations_markdown_path.write_text(
            render_country_animal_citations_markdown(animal_bundle),
            encoding="utf-8",
        )
        bundle_paths.animal_warnings_markdown_path.write_text(
            render_country_animal_warnings_markdown(animal_bundle),
            encoding="utf-8",
        )
        animal_section_markdown = render_country_animal_section(
            animal_bundle,
            summary_json_name=bundle_paths.animal_summary_json_path.name,
            samples_csv_name=bundle_paths.animal_samples_csv_path.name,
            samples_markdown_name=bundle_paths.animal_samples_markdown_path.name,
            species_csv_name=bundle_paths.animal_species_csv_path.name,
            localities_geojson_name=bundle_paths.animal_localities_geojson_path.name,
            citations_markdown_name=bundle_paths.animal_citations_markdown_path.name,
            warnings_markdown_name=bundle_paths.animal_warnings_markdown_path.name,
        )
    write_summary_json_fn(
        bundle_paths.bundle_manifest_path,
        build_country_bundle_manifest(report, bundle_paths),
    )
    write_summary_json_fn(
        bundle_paths.summary_json_path,
        build_country_report_summary_fn(report, bundle_paths),
    )
    bundle_paths.samples_markdown_path.write_text(
        render_sample_markdown_fn(report), encoding="utf-8"
    )
    bundle_paths.readme_path.write_text(
        render_summary_markdown_fn(
            report=report,
            samples_csv_name=bundle_paths.samples_csv_path.name,
            localities_csv_name=bundle_paths.localities_csv_path.name,
            geojson_name=bundle_paths.samples_geojson_path.name,
            sample_markdown_name=bundle_paths.samples_markdown_path.name,
            summary_json_name=bundle_paths.summary_json_path.name,
            map_reference=map_reference,
            animal_section_markdown=animal_section_markdown,
        ),
        encoding="utf-8",
    )
