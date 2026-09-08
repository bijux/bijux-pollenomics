"""Assembly and cross-scope reduction for report partitions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from ...models import PublishedReportsReport
from ..paths import AtlasBundlePaths
from .artifacts import scientific_artifact_inventory
from .inventory import assemble_fragment_files
from .loading import load_scope_reports
from .models import PublishedReportPartitionPlan
from .publication import require_release_gate, require_repository_claim_gate


def assemble_report_partition_tree(
    staging_output_root: Path,
    *,
    plan: PublishedReportPartitionPlan,
    partition_roots: Mapping[str, Path],
    version_dir: Path,
    published_output_root: Path,
    context_root: Path | None,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_published_reports_summary_fn: Callable[..., dict[str, object]],
    looks_like_repository_publication_run_fn: Callable[..., bool],
    publish_report_portal_fn: Callable[[Path], dict[str, str]],
    publish_repository_output_sustainability_review_fn: Callable[..., object],
    publish_repository_truth_outputs_fn: Callable[..., dict[str, str]],
    write_geography_packets_fn: Callable[..., None],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> PublishedReportsReport:
    """Assemble exact fragments, then publish all cross-scope derived outputs."""
    staging_output_root = Path(staging_output_root)
    version_dir = Path(version_dir)
    published_output_root = Path(published_output_root)
    data_root = (
        Path(context_root)
        if context_root is not None
        else published_output_root.parents[1] / "data"
    )
    docs_root = published_output_root.parent
    enforce_release_gates = looks_like_repository_publication_run_fn(
        data_root=data_root,
        docs_root=docs_root,
    )
    assemble_fragment_files(
        staging_output_root,
        plan=plan,
        partition_roots=partition_roots,
    )
    scope_reports, _, country_reports_by_scope = load_scope_reports(
        staging_output_root,
        plan=plan,
        version=version_dir.name,
    )
    world_scope = plan.geography.world_scope
    map_report = scope_reports[world_scope.key]

    repository_truth_artifacts = publish_repository_truth_outputs_fn(
        staging_output_root,
        data_root=data_root,
        docs_root=docs_root,
    )
    require_release_gate(
        staging_output_root,
        enforce_release_gates=enforce_release_gates,
    )
    write_geography_packets_fn(
        staging_output_root,
        plan=plan.geography,
        scope_reports=scope_reports,
        country_reports=country_reports_by_scope,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths_fn,
        write_summary_json_fn=write_summary_json_fn,
    )

    generated_report = PublishedReportsReport(
        version=map_report.version,
        generated_on=map_report.generated_on,
        countries=tuple(world_scope.countries),
        shared_map_dir=published_output_root.joinpath(*world_scope.output_dir_parts),
        country_output_dirs=tuple(
            published_output_root.joinpath(*scope.output_dir_parts)
            for scope in plan.geography.country_scopes
        ),
        summary_path=published_output_root / "published_reports_summary.json",
        regional_output_dirs=tuple(
            published_output_root.joinpath(*scope.output_dir_parts)
            for scope in plan.geography.regional_scopes
        ),
        country_output_root=published_output_root / "countries",
    )
    write_summary_json_fn(
        staging_output_root / "published_reports_summary.json",
        build_published_reports_summary_fn(
            generated_report,
            map_report,
            plan=plan.geography,
            scientific_artifacts=scientific_artifact_inventory(),
            repository_truth_artifacts=repository_truth_artifacts,
        ),
    )
    publish_report_portal_fn(staging_output_root)
    publish_repository_output_sustainability_review_fn(
        staging_output_root,
        data_root=data_root,
        docs_root=docs_root,
    )
    require_repository_claim_gate(
        staging_output_root,
        enforce_release_gates=enforce_release_gates,
    )
    return generated_report
