from __future__ import annotations

import argparse
import json

from ...adna import (
    build_archive_integrity_report,
    build_archive_project_catalog,
    build_domestication_coverage_report,
    build_species_archive_projects,
    build_species_artifact_plan,
    build_species_curation_manifest,
    build_species_layout,
    build_species_normalization_bundle,
    build_species_review_dossier,
    build_species_runtime_manifest,
    build_species_support_matrix,
)
from ...adna.tracked_species import TRACKED_ADNA_SPECIES
from ...data_downloader import (
    build_source_support_matrix,
    collect_data,
    validate_collection_summary_file,
)
from ...data_downloader.repository_snapshot import (
    materialize_repository_collection_snapshot,
)
from ...foundation import (
    build_ownership_map,
    build_product_scope,
    build_release_bar,
    build_release_readiness_report,
    build_surface_map,
)
from ...reporting import (
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
    refresh_animal_adna_foundation,
    slugify,
)

__all__ = [
    "run_adna_archive_projects",
    "run_adna_artifact_plan",
    "run_adna_curation_manifest",
    "run_adna_domestication_coverage",
    "run_adna_layout",
    "run_adna_release_bar",
    "run_adna_normalization_bundle",
    "run_adna_runtime_manifest",
    "run_adna_release_readiness",
    "run_adna_species",
    "run_adna_species_review",
    "run_collect_data",
    "run_refresh_animal_adna_foundation",
    "run_publish_reports",
    "run_refresh_data_contract_surfaces",
    "run_ownership_map",
    "run_product_scope",
    "run_report_country",
    "run_report_multi_country_map",
    "run_source_support",
    "run_surface_map",
    "run_validate_collection_summary",
]


def run_adna_archive_projects(args: argparse.Namespace) -> int:
    """Print the curated archive project inventory for ancient-DNA support."""
    rows = (
        build_species_archive_projects(args.species)
        if args.species
        else build_archive_project_catalog()
    )
    if args.json:
        print(json.dumps([row.as_dict() for row in rows], indent=2, sort_keys=True))
        return 0
    for row in rows:
        print(
            f"{row.species_latin_name}: project={row.project_accession}; "
            f"result={row.result_kind}; status={row.archive_status}; "
            f"evidence={row.as_dict()['evidence_strength']}"
        )
    return 0


def run_adna_artifact_plan(args: argparse.Namespace) -> int:
    """Print the deterministic species rebuild artifact plan."""
    plan = build_species_artifact_plan(args.species)
    if args.json:
        print(json.dumps(plan.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"species={plan.species_latin_name}")
    for entry in plan.entries:
        print(f"artifact={entry.artifact_kind}; path={entry.target_path}")
    return 0


def run_adna_layout(args: argparse.Namespace) -> int:
    """Print the canonical on-disk species layout for ancient-DNA support."""
    layout = build_species_layout(args.species)
    if args.json:
        print(json.dumps(layout.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"root={layout.root_dir}")
    print(f"raw={layout.raw_dir}")
    print(f"normalized={layout.normalized_dir}")
    print(f"manifests={layout.manifests_dir}")
    print(f"reports={layout.reports_dir}")
    print(f"review={layout.review_dir}")
    return 0


def run_adna_curation_manifest(args: argparse.Namespace) -> int:
    """Print the species-owned curation manifest for one non-human aDNA program."""
    manifest = build_species_curation_manifest(args.species)
    if args.json:
        print(json.dumps(manifest.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"species={manifest.species.latin_name}")
    print(f"curation_class={manifest.curation_class}")
    print(f"curated_projects={len(manifest.curated_projects)}")
    print(f"pending_projects={len(manifest.pending_projects)}")
    print(f"rejected_projects={len(manifest.rejected_projects)}")
    return 0


def run_adna_normalization_bundle(args: argparse.Namespace) -> int:
    """Print the governed non-human normalization bundle."""
    bundle = build_species_normalization_bundle(args.species)
    if args.json:
        print(json.dumps(bundle.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"species={bundle.species.latin_name}")
    print(f"project_summaries={len(bundle.project_summaries)}")
    print(f"study_summaries={len(bundle.study_summaries)}")
    print(f"lineage_records={len(bundle.lineage_records)}")
    print(f"refusals={len(bundle.refusals)}")
    return 0


def run_adna_domestication_coverage(args: argparse.Namespace) -> int:
    """Print the cross-species domestication coverage report."""
    report = build_domestication_coverage_report()
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
        return 0
    for row in report.rows:
        print(
            f"{row.species_latin_name}: class={row.curation_class}; "
            f"posture={row.coverage_posture}; "
            f"curated={row.curated_project_count}; "
            f"pending={row.pending_project_count}; "
            f"rejected={row.rejected_project_count}"
        )
    return 0


def run_adna_species(args: argparse.Namespace) -> int:
    """Print the canonical species support matrix for ancient-DNA support."""
    rows = build_species_support_matrix()
    if args.json:
        print(json.dumps([row.as_dict() for row in rows], indent=2, sort_keys=True))
        return 0
    for row in rows:
        modalities = ", ".join(row.modalities)
        aliases = ", ".join(row.aliases)
        print(
            f"{row.latin_name}: status={row.support_status}; "
            f"modalities={modalities}; aliases={aliases}"
        )
    return 0


def run_adna_runtime_manifest(args: argparse.Namespace) -> int:
    """Print the species-owned runtime manifest."""
    manifest = build_species_runtime_manifest(args.species, version=args.version)
    if args.json:
        print(json.dumps(manifest.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"species={manifest.species.latin_name}")
    print(f"runtime_ready={str(manifest.runtime_ready).lower()}")
    print(f"analysis_boundary={manifest.analysis_boundary}")
    for bundle in manifest.source_bundles:
        print(
            "bundle="
            f"{bundle.source_family}:{bundle.source_release}; "
            f"kind={bundle.bundle_kind}; "
            f"tracked_root={bundle.tracked_root}; "
            f"modality={bundle.record_modality}; "
            f"review={bundle.review_strength}"
        )
    return 0


def run_adna_release_readiness(args: argparse.Namespace) -> int:
    """Print the medium-weight release readiness gate for one species."""
    report = build_release_readiness_report(args.species)
    if args.json:
        print(json.dumps(report.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"species={report.species_latin_name}")
    print(f"source_identity_ok={str(report.source_identity_ok).lower()}")
    print(f"curation_integrity_ok={str(report.curation_integrity_ok).lower()}")
    print(
        f"normalized_record_contract_ok={str(report.normalized_record_contract_ok).lower()}"
    )
    print(f"atlas_bundle_contract_ok={str(report.atlas_bundle_contract_ok).lower()}")
    print(f"ranking_provenance_ok={str(report.ranking_provenance_ok).lower()}")
    print(f"overall_ok={str(report.overall_ok).lower()}")
    if report.findings:
        print("findings=" + ", ".join(report.findings))
    return 0


def run_adna_release_bar(args: argparse.Namespace) -> int:
    """Print the platform release bar for bijux-pollenomics."""
    release_bar = build_release_bar()
    if args.json:
        print(json.dumps(release_bar.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"current_posture={release_bar.current_posture}")
    print(
        "species_aware_adna_support_defined="
        f"{str(release_bar.species_aware_adna_support_defined).lower()}"
    )
    print(
        f"bovine_split_rule_defined={str(release_bar.bovine_split_rule_defined).lower()}"
    )
    print(
        "homo_sapiens_genotype_boundary_defined="
        f"{str(release_bar.homo_sapiens_genotype_boundary_defined).lower()}"
    )
    print(
        "nonhuman_domestication_program_defined="
        f"{str(release_bar.nonhuman_domestication_program_defined).lower()}"
    )
    print(
        "scientific_review_surface_defined="
        f"{str(release_bar.scientific_review_surface_defined).lower()}"
    )
    print(
        f"ranking_boundary_defined={str(release_bar.ranking_boundary_defined).lower()}"
    )
    if release_bar.blockers:
        print("blockers=" + ", ".join(release_bar.blockers))
    return 0


def run_adna_species_review(args: argparse.Namespace) -> int:
    """Print the governed review for one species dataset."""
    dossier = build_species_review_dossier(args.species)
    review = dossier.dataset_review
    integrity = build_archive_integrity_report(species_name=args.species)
    payload = {
        "review": review.as_dict(),
        "project_manifest": dossier.project_manifest.as_dict(),
        "project_reviews": [item.as_dict() for item in dossier.project_reviews],
        "release_blockers": list(dossier.release_blockers),
        "integrity": integrity.as_dict(),
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0
    print(
        f"{review.species.latin_name}: role={review.product_role}; "
        f"assignment={review.assignment_rule}; bucket={review.dataset_bucket}"
    )
    if review.blocking_reasons:
        print("blocking_reasons=" + ", ".join(review.blocking_reasons))
    print(f"core_projects={review.core_project_count}")
    print(f"curated_projects={review.curated_support_project_count}")
    print(f"duplicate_accessions={len(integrity.duplicates)}")
    print(f"species_mismatches={len(integrity.species_mismatches)}")
    for item in dossier.project_reviews:
        print(
            f"project={item.project_accession}; "
            f"evidence={item.evidence_strength}; "
            f"admissible={str(item.admissible_for_curated_support).lower()}"
        )
    return 0


def run_report_country(
    args: argparse.Namespace, *, parser: argparse.ArgumentParser
) -> int:
    """Run the country-report command."""
    if bool(args.shared_map_label) != bool(args.shared_map_path):
        parser.error(
            "--shared-map-label and --shared-map-path must be provided together"
        )
    version_dir = args.aadr_root / args.version
    output_dir = args.output_root / slugify(args.country)
    map_reference = None
    if args.shared_map_label and args.shared_map_path:
        map_reference = (args.shared_map_label, args.shared_map_path)
    report = generate_country_report(
        version_dir=version_dir,
        country=args.country,
        output_dir=output_dir,
        map_reference=map_reference,
    )
    print(
        f"Wrote {report.country} Homo sapiens aDNA {report.version} report with "
        f"{report.total_unique_samples} unique samples to {output_dir}"
    )
    return 0


def run_report_multi_country_map(args: argparse.Namespace) -> int:
    """Run the shared multi-country atlas command."""
    version_dir = args.aadr_root / args.version
    output_dir = args.output_root / slugify(args.name)
    report = generate_multi_country_map(
        version_dir=version_dir,
        countries=args.countries,
        output_dir=output_dir,
        title=args.title,
        slug=slugify(args.name),
        context_root=args.context_root,
    )
    print(
        f"Wrote {report.title} with "
        f"{report.total_unique_samples} unique samples to {output_dir}"
    )
    return 0


def run_collect_data(args: argparse.Namespace) -> int:
    """Run the data-collection command."""
    report = collect_data(
        output_root=args.output_root, sources=args.sources, version=args.version
    )
    print(
        f"Wrote data sources {', '.join(report.collected_sources)} to {report.output_root} with "
        f"{report.aadr_file_count} AADR .anno files, "
        f"{report.landclim_site_count} LandClim pollen sequences, "
        f"{report.landclim_grid_cell_count} LandClim REVEALS grid cells, "
        f"{report.neotoma_point_count} Neotoma points, "
        f"{report.sead_point_count} SEAD points, and "
        f"{report.raa_total_site_count} Swedish archaeology records in the RAÄ layer"
    )
    return 0


def run_publish_reports(args: argparse.Namespace) -> int:
    """Run the checked-in publication workflow."""
    version_dir = args.aadr_root / args.version
    report = generate_published_reports(
        version_dir=version_dir,
        countries=args.countries,
        output_root=args.output_root,
        title=args.title,
        slug=args.name,
        context_root=args.context_root,
    )
    print(
        f"Wrote published report bundles for {', '.join(report.countries)} to {args.output_root} "
        f"with shared map under {report.shared_map_dir.name}"
    )
    return 0


def run_refresh_animal_adna_foundation(args: argparse.Namespace) -> int:
    """Refresh tracked animal source capture, normalized roots, and published outputs."""
    report = refresh_animal_adna_foundation(
        data_root=args.data_root,
        aadr_root=args.aadr_root,
        report_root=args.output_root,
        countries=args.countries,
        version=args.version,
        context_root=args.context_root,
        species_names=tuple(args.species) if args.species else TRACKED_ADNA_SPECIES,
    )
    print(
        f"Refreshed animal foundation for {', '.join(report.refreshed_species_latin_names)} "
        f"with {report.source_library_project_count} source-library projects and "
        f"{report.atlas_evidence_row_count} atlas evidence rows"
    )
    return 0


def run_surface_map(args: argparse.Namespace) -> int:
    """Print the runtime-versus-roadmap surface map."""
    surface_map = build_surface_map()
    if args.json:
        print(json.dumps(surface_map.as_dict(), indent=2, sort_keys=True))
        return 0
    print("runtime surfaces")
    for item in surface_map.runtime_surfaces:
        print(f"- {item}")
    print("planned engine surfaces")
    for item in surface_map.planned_engine_surfaces:
        print(f"- {item}")
    return 0


def run_product_scope(args: argparse.Namespace) -> int:
    """Print an explicit current-scope versus roadmap-scope statement."""
    scope = build_product_scope()
    if args.json:
        print(json.dumps(scope.as_dict(), indent=2, sort_keys=True))
        return 0
    print(f"current product mode: {scope.current_product_mode}")
    for capability in scope.current_capabilities:
        print(f"- capability: {capability}")
    print(f"roadmap mode: {scope.roadmap_mode}")
    for claim in scope.not_yet_supported_claims:
        print(f"- not-yet-supported: {claim}")
    return 0


def run_ownership_map(args: argparse.Namespace) -> int:
    """Print a short ownership map for core runtime concerns."""
    ownership_map = build_ownership_map()
    if args.json:
        print(json.dumps([entry.as_dict() for entry in ownership_map], indent=2))
        return 0
    for entry in ownership_map:
        print(f"{entry.concern}: {entry.owner_module}")
        print(f"  reason: {entry.reason}")
    return 0


def run_source_support(args: argparse.Namespace) -> int:
    """Print support-status and country-coverage rows for tracked sources."""
    support_rows = build_source_support_matrix()
    if args.json:
        print(json.dumps([row.as_dict() for row in support_rows], indent=2))
        return 0
    for row in support_rows:
        countries = ", ".join(row.country_coverage)
        print(f"{row.source}: status={row.support_status}; countries={countries}")
    return 0


def run_validate_collection_summary(args: argparse.Namespace) -> int:
    """Validate a collection summary payload independent of full data recollection."""
    payload = validate_collection_summary_file(args.summary_path)
    sources = payload.get("collected_sources", [])
    source_count = len(sources) if isinstance(sources, list) else 0
    print(
        f"Validated collection summary at {args.summary_path} with {source_count} collected sources"
    )
    return 0


def run_refresh_data_contract_surfaces(args: argparse.Namespace) -> int:
    """Refresh checked-in data contract surfaces from the current repository tree."""
    summary = materialize_repository_collection_snapshot(
        args.data_root,
        version=args.version,
    )
    print(
        "Refreshed data contract surfaces at "
        f"{summary.summary_path} for {len(summary.source_family_state_rows)} source families"
    )
    return 0
