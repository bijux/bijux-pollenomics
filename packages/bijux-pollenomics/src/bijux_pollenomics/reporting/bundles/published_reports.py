from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path

from ...adna.catalogs import (
    build_public_animal_output_audit,
    render_public_animal_output_audit_markdown,
)
from ..adna.foundation_outputs import publish_animal_foundation_outputs
from ..adna.public_outputs import publish_public_animal_reporting_outputs
from ..foundation import publish_repository_truth_outputs
from ..geography import (
    GeographicScope,
    PublishedGeographyPlan,
    build_published_geography_plan,
    render_geography_onboarding_contract_markdown,
    render_geography_scope_registry_markdown,
    render_geography_subset_validation_markdown,
)
from ..models import CountryReport, MultiCountryMapReport, PublishedReportsReport
from .paths import AtlasBundlePaths, build_country_bundle_paths

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
    """Publish the full report tree as one world surface plus derived regional and country views."""
    plan = build_published_geography_plan(normalized_countries)
    scope_reports: dict[str, MultiCountryMapReport] = {}
    world_scope = plan.world_scope
    shared_map_dir = staging_output_root.joinpath(*world_scope.output_dir_parts)
    map_report = generate_multi_country_map_fn(
        version_dir=version_dir,
        countries=world_scope.countries,
        output_dir=shared_map_dir,
        title=world_scope.map_title,
        slug=world_scope.slug,
        context_root=context_root,
        published_output_dir=output_root.joinpath(*world_scope.output_dir_parts),
        geography_scope=world_scope,
    )
    scope_reports[world_scope.key] = map_report

    regional_output_dirs: list[Path] = []
    for scope in plan.regional_scopes:
        scope_dir = staging_output_root.joinpath(*scope.output_dir_parts)
        scope_report = generate_multi_country_map_fn(
            version_dir=version_dir,
            countries=scope.countries,
            output_dir=scope_dir,
            title=scope.map_title,
            slug=scope.slug,
            context_root=context_root,
            published_output_dir=output_root.joinpath(*scope.output_dir_parts),
            geography_scope=scope,
        )
        scope_reports[scope.key] = scope_report
        regional_output_dirs.append(scope_dir)

    country_output_dirs: list[Path] = []
    country_reports: list[CountryReport] = []
    country_reports_by_scope_key: dict[str, CountryReport] = {}
    scope_lookup = {scope.key: scope for scope in plan.all_scopes()}
    for country_scope in plan.country_scopes:
        parent_scope = scope_lookup[str(country_scope.parent_key)]
        parent_report = scope_reports[str(country_scope.parent_key)]
        parent_dir = staging_output_root.joinpath(*parent_scope.output_dir_parts)
        parent_bundle_paths = build_atlas_bundle_paths_fn(
            output_dir=parent_dir,
            slug=parent_report.slug,
            version=parent_report.version,
        )
        country_dir = staging_output_root.joinpath(*country_scope.output_dir_parts)
        parent_map_path = str(
            Path(
                os.path.relpath(
                    parent_dir / parent_bundle_paths.map_html_path.name,
                    country_dir,
                )
            )
        )
        country_report = generate_country_report_fn(
            version_dir=version_dir,
            country=country_scope.countries[0],
            output_dir=country_dir,
            map_reference=(parent_report.title, parent_map_path),
            published_output_dir=output_root.joinpath(*country_scope.output_dir_parts),
            context_root=context_root,
        )
        country_output_dirs.append(country_dir)
        if isinstance(country_report, CountryReport):
            country_reports.append(country_report)
            country_reports_by_scope_key[country_scope.key] = country_report

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
    _write_geography_packets(
        staging_output_root,
        plan=plan,
        scope_reports=scope_reports,
        country_reports=country_reports_by_scope_key,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
        write_summary_json_fn=write_summary_json_fn,
    )
    generated_report = PublishedReportsReport(
        version=map_report.version,
        generated_on=map_report.generated_on,
        countries=normalized_countries,
        shared_map_dir=output_root.joinpath(*world_scope.output_dir_parts),
        country_output_dirs=tuple(
            output_root.joinpath(*scope.output_dir_parts)
            for scope in plan.country_scopes
        ),
        summary_path=output_root / summary_path.name,
        regional_output_dirs=tuple(
            output_root.joinpath(*scope.output_dir_parts)
            for scope in plan.regional_scopes
        ),
        country_output_root=output_root.joinpath("countries"),
    )
    write_summary_json_fn(
        summary_path,
        build_published_reports_summary_fn(
            generated_report,
            map_report,
            plan=plan,
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
    repository_claim_audit = json.loads(
        (staging_output_root / "repository_claim_audit.json").read_text(
            encoding="utf-8"
        )
    )
    if not bool(repository_claim_audit.get("overall_ok")):
        raise ValueError("Repository claim audit failed")
    return generated_report


def _write_geography_packets(
    output_root: Path,
    *,
    plan: PublishedGeographyPlan,
    scope_reports: dict[str, MultiCountryMapReport],
    country_reports: dict[str, CountryReport],
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    registry_payload = {
        "schema_version": "publication-geography-registry.v1",
        "scopes": [
            {
                "key": scope.key,
                "kind": scope.kind,
                "label": scope.label,
                "parent_key": scope.parent_key,
                "directory": str(Path(*scope.output_dir_parts)),
                "country_count": len(scope.countries),
                "countries": list(scope.countries),
            }
            for scope in plan.all_scopes()
        ],
    }
    write_summary_json_fn(output_root / "publication_geography_registry.json", registry_payload)
    (output_root / "publication_geography_registry.md").write_text(
        render_geography_scope_registry_markdown(registry_payload),
        encoding="utf-8",
    )

    subset_rows: list[dict[str, object]] = []
    for scope in (*plan.regional_scopes, *plan.country_scopes):
        parent_scope = next(
            parent for parent in plan.all_scopes() if parent.key == scope.parent_key
        )
        subset_rows.append(
            _build_subset_validation_row(
                output_root=output_root,
                scope=scope,
                parent_scope=parent_scope,
                parent_report=scope_reports[parent_scope.key],
                country_report=country_reports.get(scope.key),
                scope_report=scope_reports.get(scope.key),
                build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
            )
        )
    subset_payload = {
        "schema_version": "publication-geography-subset-validation.v1",
        "rows": subset_rows,
    }
    write_summary_json_fn(
        output_root / "publication_geography_subset_validation.json",
        subset_payload,
    )
    (output_root / "publication_geography_subset_validation.md").write_text(
        render_geography_subset_validation_markdown(subset_payload),
        encoding="utf-8",
    )

    onboarding_payload = {
        "schema_version": "publication-country-onboarding-contract.v1",
        "required_surfaces": [
            "published country roster entry",
            "world geography bundle",
            "Europe-plus geography bundle when applicable",
            "country bundle under docs/report/countries/<country-slug>/",
            "subset validation row proving world -> region -> country lineage",
        ],
    }
    write_summary_json_fn(
        output_root / "publication_country_onboarding_contract.json",
        onboarding_payload,
    )
    (output_root / "publication_country_onboarding_contract.md").write_text(
        render_geography_onboarding_contract_markdown(onboarding_payload),
        encoding="utf-8",
    )


def _build_subset_validation_row(
    *,
    output_root: Path,
    scope: GeographicScope,
    parent_scope: GeographicScope,
    parent_report: MultiCountryMapReport,
    country_report: CountryReport | None,
    scope_report: MultiCountryMapReport | None,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
) -> dict[str, object]:
    scope_dir = output_root.joinpath(*scope.output_dir_parts)
    if scope.kind == "country":
        if country_report is None:
            raise KeyError(f"Missing country report for scope {scope.key}")
        scope_human_ids = _load_country_human_sample_ids(
            scope_dir,
            country=scope.countries[0],
            version=country_report.version,
        )
        scope_animal_ids = _load_country_animal_evidence_ids(
            scope_dir,
            country=scope.countries[0],
            version=country_report.version,
        )
    else:
        if scope_report is None:
            raise KeyError(f"Missing map report for scope {scope.key}")
        scope_human_ids = _load_human_sample_ids(scope_dir, slug=scope_report.slug)
        scope_animal_ids = _load_animal_evidence_ids(
            scope_dir,
            slug=scope_report.slug,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
        )
    parent_human_ids = _load_human_sample_ids(
        output_root.joinpath(*parent_scope.output_dir_parts),
        slug=parent_report.slug,
    )
    parent_animal_ids = _load_animal_evidence_ids(
        output_root.joinpath(*parent_scope.output_dir_parts),
        slug=parent_report.slug,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
    )
    return {
        "scope": scope.label,
        "parent_scope": parent_scope.label,
        "country_subset_ok": set(scope.countries).issubset(parent_scope.countries),
        "animal_subset_ok": scope_animal_ids.issubset(parent_animal_ids),
        "human_subset_ok": scope_human_ids.issubset(parent_human_ids),
    }


def _load_human_sample_ids(scope_dir: Path, *, slug: str) -> set[str]:
    payload = json.loads((scope_dir / f"{slug}_samples.geojson").read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        return set()
    identifiers: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        genetic_id = str(properties.get("genetic_id", "")).strip()
        if genetic_id:
            identifiers.add(genetic_id)
    return identifiers


def _load_animal_evidence_ids(
    scope_dir: Path,
    *,
    slug: str,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
) -> set[str]:
    bundle_paths = build_atlas_bundle_paths_fn(output_dir=scope_dir, slug=slug, version="unused")
    payload = json.loads(bundle_paths.animal_atlas_evidence_json_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return set()
    identifiers: set[str] = set()
    for row in payload:
        if not isinstance(row, dict):
            continue
        evidence_row_id = str(row.get("evidence_row_id", "")).strip()
        if evidence_row_id:
            identifiers.add(evidence_row_id)
    return identifiers


def _load_country_human_sample_ids(
    scope_dir: Path,
    *,
    country: str,
    version: str,
) -> set[str]:
    bundle_paths = build_country_bundle_paths(scope_dir, country, version)
    payload = json.loads(bundle_paths.samples_geojson_path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    if not isinstance(features, list):
        return set()
    identifiers: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties", {})
        if not isinstance(properties, dict):
            continue
        genetic_id = str(properties.get("genetic_id", "")).strip()
        if genetic_id:
            identifiers.add(genetic_id)
    return identifiers


def _load_country_animal_evidence_ids(
    scope_dir: Path,
    *,
    country: str,
    version: str,
) -> set[str]:
    bundle_paths = build_country_bundle_paths(scope_dir, country, version)
    if not bundle_paths.animal_summary_json_path.is_file():
        return set()
    payload = json.loads(
        bundle_paths.animal_summary_json_path.read_text(encoding="utf-8")
    )
    sample_rows = payload.get("sample_rows", [])
    if not isinstance(sample_rows, list):
        return set()
    identifiers: set[str] = set()
    for row in sample_rows:
        if not isinstance(row, dict):
            continue
        evidence_row_id = str(row.get("evidence_row_id", "")).strip()
        if evidence_row_id:
            identifiers.add(evidence_row_id)
    return identifiers
