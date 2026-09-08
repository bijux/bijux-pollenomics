from __future__ import annotations

from pathlib import Path
import shutil

from bijux_pollenomics.reporting.bundles.paths import build_atlas_bundle_paths
from bijux_pollenomics.reporting.bundles.published_reports import (
    _write_geography_packets,
    publish_published_reports_tree,
)
from bijux_pollenomics.reporting.bundles.report_partitions.planning import (
    build_report_partition_plan,
)
from bijux_pollenomics.reporting.bundles.report_partitions.publication import (
    publish_report_partition,
)
from bijux_pollenomics.reporting.bundles.report_partitions.reducer import (
    assemble_report_partition_tree,
)
from bijux_pollenomics.reporting.bundles.summary_builders import (
    build_published_reports_summary,
)

from .support import (
    build_audit,
    generate_country,
    generate_map,
    publish_foundation,
    publish_portal,
    publish_public,
    publish_sustainability,
    publish_truth,
    render_audit,
    write_json,
)


def test_partitioned_publication_is_byte_identical_to_monolithic_tree(
    tmp_path: Path, monkeypatch
) -> None:
    version_dir = tmp_path / "source" / "v66"
    version_dir.mkdir(parents=True)
    data_root = tmp_path / "data"
    data_root.mkdir()
    published_root = Path("docs/report")
    countries = ("Sweden", "Norway", "Finland", "Denmark")
    title = "Comparative World Evidence"
    slug = "comparative-world"

    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.publish_public_animal_reporting_outputs",
        publish_public,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.publish_animal_foundation_outputs",
        publish_foundation,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.publish_repository_truth_outputs",
        publish_truth,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.publish_repository_output_sustainability_review",
        publish_sustainability,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.publish_report_portal",
        publish_portal,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.build_public_animal_output_audit",
        build_audit,
    )
    monkeypatch.setattr(
        "bijux_pollenomics.reporting.bundles.published_reports.render_public_animal_output_audit_markdown",
        render_audit,
    )

    monolithic_root = tmp_path / "monolithic"
    monolithic_root.mkdir()
    monolithic_report = publish_published_reports_tree(
        monolithic_root,
        version_dir=version_dir,
        output_root=tmp_path / "unused-report-root",
        published_output_root=published_root,
        normalized_countries=countries,
        title=title,
        atlas_slug=slug,
        context_root=data_root,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
        build_published_reports_summary_fn=build_published_reports_summary,
        generate_country_report_fn=generate_country,
        generate_multi_country_map_fn=generate_map,
        slugify_fn=lambda value: value,
        write_summary_json_fn=write_json,
    )

    plan = build_report_partition_plan(
        countries,
        title=title,
        slug=slug,
        country_group_size=2,
    )
    fragment_parent = tmp_path / "fragments"
    partition_roots: dict[str, Path] = {}
    scope_input_root = tmp_path / "scope-input"
    scope_input_root.mkdir()
    for partition in plan.partitions:
        if partition.kind == "foundation":
            continue
        root = fragment_parent / partition.identity
        root.mkdir(parents=True)
        publish_report_partition(
            root,
            partition=partition,
            plan=plan,
            version_dir=version_dir,
            published_output_root=published_root,
            context_root=data_root,
            scope_input_root=None,
            build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
            build_public_animal_output_audit_fn=build_audit,
            generate_country_report_fn=generate_country,
            generate_multi_country_map_fn=generate_map,
            publish_animal_foundation_outputs_fn=publish_foundation,
            publish_public_animal_reporting_outputs_fn=publish_public,
            render_public_animal_output_audit_markdown_fn=render_audit,
            write_summary_json_fn=write_json,
        )
        partition_roots[partition.identity] = root
        shutil.copytree(root, scope_input_root, dirs_exist_ok=True)

    foundation = plan.partitions[-1]
    foundation_root = fragment_parent / foundation.identity
    foundation_root.mkdir(parents=True)
    publish_report_partition(
        foundation_root,
        partition=foundation,
        plan=plan,
        version_dir=version_dir,
        published_output_root=published_root,
        context_root=data_root,
        scope_input_root=scope_input_root,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
        build_public_animal_output_audit_fn=build_audit,
        generate_country_report_fn=generate_country,
        generate_multi_country_map_fn=generate_map,
        publish_animal_foundation_outputs_fn=publish_foundation,
        publish_public_animal_reporting_outputs_fn=publish_public,
        render_public_animal_output_audit_markdown_fn=render_audit,
        write_summary_json_fn=write_json,
    )
    partition_roots[foundation.identity] = foundation_root

    assembled_root = tmp_path / "assembled"
    assembled_root.mkdir()
    assembled_report = assemble_report_partition_tree(
        assembled_root,
        plan=plan,
        partition_roots=partition_roots,
        version_dir=version_dir,
        published_output_root=published_root,
        context_root=data_root,
        build_atlas_bundle_paths_fn=build_atlas_bundle_paths,
        build_published_reports_summary_fn=build_published_reports_summary,
        looks_like_repository_publication_run_fn=lambda **_: False,
        publish_report_portal_fn=publish_portal,
        publish_repository_output_sustainability_review_fn=publish_sustainability,
        publish_repository_truth_outputs_fn=publish_truth,
        write_geography_packets_fn=_write_geography_packets,
        write_summary_json_fn=write_json,
    )

    assert assembled_report == monolithic_report
    assert _tree_bytes(assembled_root) == _tree_bytes(monolithic_root)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }
