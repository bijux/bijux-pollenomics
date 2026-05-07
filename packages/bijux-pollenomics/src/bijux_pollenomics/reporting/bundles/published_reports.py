from __future__ import annotations

from collections.abc import Callable
import json
from pathlib import Path

from ...adna.catalogs import (
    build_public_animal_output_audit,
    render_public_animal_output_audit_markdown,
)
from ..adna.foundation_outputs import publish_animal_foundation_outputs
from ..adna.public_outputs import publish_public_animal_reporting_outputs
from ..foundation import publish_repository_truth_outputs
from ..models import CountryReport, MultiCountryMapReport, PublishedReportsReport
from .paths import AtlasBundlePaths

__all__ = ["publish_published_reports_tree"]


def publish_published_reports_tree(
    staging_output_root: Path,
    *,
    version_dir: Path,
    output_root: Path,
    normalized_countries: tuple[str, ...],
    title: str,
    atlas_slug: str,
    context_root: Path | None,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_published_reports_summary_fn: Callable[..., dict[str, object]],
    generate_country_report_fn: Callable[..., object],
    generate_multi_country_map_fn: Callable[..., MultiCountryMapReport],
    slugify_fn: Callable[[str], str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> PublishedReportsReport:
    """Publish the full report tree: one shared atlas plus one country bundle per country."""
    shared_map_dir = staging_output_root / atlas_slug
    map_report = generate_multi_country_map_fn(
        version_dir=version_dir,
        countries=normalized_countries,
        output_dir=shared_map_dir,
        title=title,
        slug=atlas_slug,
        context_root=context_root,
        published_output_dir=output_root / shared_map_dir.name,
    )

    country_output_dirs: list[Path] = []
    country_reports: list[CountryReport] = []
    shared_bundle_paths = build_atlas_bundle_paths_fn(
        output_dir=shared_map_dir,
        slug=map_report.slug,
        version=map_report.version,
    )
    shared_map_path = (
        f"../{shared_map_dir.name}/{shared_bundle_paths.map_html_path.name}"
    )
    for country in normalized_countries:
        country_dir = staging_output_root / slugify_fn(country)
        country_report = generate_country_report_fn(
            version_dir=version_dir,
            country=country,
            output_dir=country_dir,
            map_reference=(title, shared_map_path),
            published_output_dir=output_root / country_dir.name,
            context_root=context_root,
        )
        country_output_dirs.append(country_dir)
        if isinstance(country_report, CountryReport):
            country_reports.append(country_report)

    summary_path = staging_output_root / "published_reports_summary.json"
    scientific_artifacts = publish_public_animal_reporting_outputs(
        staging_output_root,
        data_root=context_root if context_root is not None else output_root.parents[1] / "data",
        country_reports=tuple(country_reports),
        country_output_dirs=tuple(country_output_dirs),
        atlas_output_dir=shared_map_dir,
    )
    foundation_artifacts = publish_animal_foundation_outputs(
        staging_output_root,
        data_root=context_root if context_root is not None else output_root.parents[1] / "data",
        docs_root=output_root.parent,
    )
    repository_truth_artifacts = publish_repository_truth_outputs(
        staging_output_root,
        data_root=context_root if context_root is not None else output_root.parents[1] / "data",
        docs_root=output_root.parent,
    )
    scientific_artifacts = {**scientific_artifacts, **foundation_artifacts}
    release_gate_payload = json.loads(
        (staging_output_root / "animal_publication_release_gate.json").read_text(
            encoding="utf-8"
        )
    )
    if not bool(release_gate_payload.get("overall_ok")):
        raise ValueError("Animal publication release gate failed")
    generated_report = PublishedReportsReport(
        version=map_report.version,
        generated_on=map_report.generated_on,
        countries=normalized_countries,
        shared_map_dir=output_root / shared_map_dir.name,
        country_output_dirs=tuple(
            output_root / path.name for path in country_output_dirs
        ),
        summary_path=output_root / summary_path.name,
    )
    write_summary_json_fn(
        summary_path,
        build_published_reports_summary_fn(
            generated_report,
            map_report,
            scientific_artifacts=scientific_artifacts,
            repository_truth_artifacts=repository_truth_artifacts,
        ),
    )
    data_root = context_root if context_root is not None else output_root.parents[1] / "data"
    animal_output_audit = build_public_animal_output_audit(data_root, staging_output_root)
    animal_output_audit["report_root"] = str(output_root)
    write_summary_json_fn(
        staging_output_root / "animal_output_audit.json",
        animal_output_audit,
    )
    (staging_output_root / "animal_output_audit.md").write_text(
        render_public_animal_output_audit_markdown(animal_output_audit),
        encoding="utf-8",
    )
    return generated_report
