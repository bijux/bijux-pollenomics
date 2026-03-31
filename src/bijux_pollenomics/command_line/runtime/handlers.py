from __future__ import annotations

import argparse

from ...data_downloader import collect_data
from ...reporting import generate_country_report, generate_multi_country_map, generate_published_reports, slugify

__all__ = [
    "run_collect_data",
    "run_publish_reports",
    "run_report_country",
    "run_report_multi_country_map",
]


def run_report_country(args: argparse.Namespace, *, parser: argparse.ArgumentParser) -> int:
    """Run the country-report command."""
    if bool(args.shared_map_label) != bool(args.shared_map_path):
        parser.error("--shared-map-label and --shared-map-path must be provided together")
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
    report = collect_data(output_root=args.output_root, sources=args.sources, version=args.version)
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
