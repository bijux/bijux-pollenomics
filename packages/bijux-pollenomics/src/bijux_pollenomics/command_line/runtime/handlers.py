from __future__ import annotations

import argparse
import json

from ...data_downloader import collect_data
from ...data_downloader import build_source_support_matrix
from ...data_downloader import validate_collection_summary_file
from ...foundation import build_ownership_map, build_product_scope, build_surface_map
from ...reporting import (
    generate_country_report,
    generate_multi_country_map,
    generate_published_reports,
    slugify,
)

__all__ = [
    "run_collect_data",
    "run_publish_reports",
    "run_ownership_map",
    "run_product_scope",
    "run_report_country",
    "run_report_multi_country_map",
    "run_source_support",
    "run_surface_map",
    "run_validate_collection_summary",
]


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
        f"Wrote {report.country} AADR {report.version} report with "
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
