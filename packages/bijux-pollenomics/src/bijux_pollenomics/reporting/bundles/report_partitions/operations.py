"""High-level executable boundaries for partitioned report publication."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path

from ....config import DEFAULT_ATLAS_SLUG, DEFAULT_ATLAS_TITLE
from ...models import PublishedReportsReport
from ..country_selection import normalize_requested_countries
from ..staging import publish_into_staging_dir
from .inventory import _validate_partition_paths, relative_file_inventory
from .models import ReportPartitionResult
from .planning import build_report_partition_plan
from .publication import publish_report_partition
from .reducer import assemble_report_partition_tree


def generate_report_partition(
    partition_id: str,
    *,
    version_dir: Path,
    countries: Iterable[str],
    output_root: Path,
    published_output_root: Path,
    title: str = DEFAULT_ATLAS_TITLE,
    slug: str = DEFAULT_ATLAS_SLUG,
    context_root: Path | None = None,
    scope_input_root: Path | None = None,
    country_group_size: int = 2,
) -> ReportPartitionResult:
    """Generate one report fragment through fully resolved runtime publishers."""
    from ....adna.governance.audit_catalogs import (
        build_public_animal_output_audit,
        render_public_animal_output_audit_markdown,
    )
    from ... import service as reporting_service
    from ...adna.foundation_outputs import publish_animal_foundation_outputs
    from ...adna.public_outputs import publish_public_animal_reporting_outputs
    from ...rendering import write_summary_json
    from ..paths import build_atlas_bundle_paths

    normalized_countries = normalize_requested_countries(countries)
    plan = build_report_partition_plan(
        normalized_countries,
        title=title,
        slug=slug,
        country_group_size=country_group_size,
    )
    partition = next(
        (item for item in plan.partitions if item.identity == partition_id), None
    )
    if partition is None:
        raise ValueError(f"Unknown report partition: {partition_id}")
    output_root = Path(output_root)
    publish_into_staging_dir(
        output_root,
        lambda staging_output_root: publish_report_partition(
            staging_output_root,
            partition=partition,
            plan=plan,
            version_dir=Path(version_dir),
            published_output_root=Path(published_output_root),
            context_root=context_root,
            scope_input_root=scope_input_root,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_public_animal_output_audit_fn=build_public_animal_output_audit,
            generate_country_report_fn=reporting_service.generate_country_report,
            generate_multi_country_map_fn=reporting_service.generate_multi_country_map,
            publish_animal_foundation_outputs_fn=publish_animal_foundation_outputs,
            publish_public_animal_reporting_outputs_fn=(
                publish_public_animal_reporting_outputs
            ),
            render_public_animal_output_audit_markdown_fn=(
                render_public_animal_output_audit_markdown
            ),
            write_summary_json_fn=write_summary_json,
        ),
    )
    inventory = relative_file_inventory(output_root)
    _validate_partition_paths(partition.identity, inventory, plan=plan)
    return ReportPartitionResult(
        partition=partition,
        output_root=output_root,
        relative_paths=inventory,
    )


def assemble_report_partitions(
    *,
    version_dir: Path,
    countries: Iterable[str],
    output_root: Path,
    partition_roots: Mapping[str, Path],
    published_output_root: Path,
    title: str = DEFAULT_ATLAS_TITLE,
    slug: str = DEFAULT_ATLAS_SLUG,
    context_root: Path | None = None,
    country_group_size: int = 2,
) -> PublishedReportsReport:
    """Assemble exact report fragments and run cross-scope reducers atomically."""
    from ...presentation import publish_report_portal
    from ...rendering import write_summary_json
    from ...review.repository_truth_outputs import publish_repository_truth_outputs
    from ...review.sustainability_outputs import (
        publish_repository_output_sustainability_review,
    )
    from ..paths import build_atlas_bundle_paths
    from ..published_reports import (
        _looks_like_repository_publication_run,
        _write_geography_packets,
    )
    from ..summary_builders import build_published_reports_summary

    normalized_countries = normalize_requested_countries(countries)
    plan = build_report_partition_plan(
        normalized_countries,
        title=title,
        slug=slug,
        country_group_size=country_group_size,
    )
    return publish_into_staging_dir(
        Path(output_root),
        lambda staging_output_root: assemble_report_partition_tree(
            staging_output_root,
            plan=plan,
            partition_roots=partition_roots,
            version_dir=Path(version_dir),
            published_output_root=Path(published_output_root),
            context_root=context_root,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_published_reports_summary_fn=build_published_reports_summary,
            looks_like_repository_publication_run_fn=(
                _looks_like_repository_publication_run
            ),
            publish_report_portal_fn=publish_report_portal,
            publish_repository_output_sustainability_review_fn=(
                publish_repository_output_sustainability_review
            ),
            publish_repository_truth_outputs_fn=publish_repository_truth_outputs,
            write_geography_packets_fn=_write_geography_packets,
            write_summary_json_fn=write_summary_json,
        ),
    )
