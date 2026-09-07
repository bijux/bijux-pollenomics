"""Independent publication of planned report fragments."""

from __future__ import annotations

from collections.abc import Callable
import json
import os
from pathlib import Path
from typing import cast

from ...models import MultiCountryMapReport
from ..paths import AtlasBundlePaths, serialize_publication_path
from .inventory import copy_scope_inputs, remove_scope_inputs
from .loading import load_scope_reports
from .models import PublishedReportPartitionPlan, ReportPartition


def publish_report_partition(
    staging_output_root: Path,
    *,
    partition: ReportPartition,
    plan: PublishedReportPartitionPlan,
    version_dir: Path,
    published_output_root: Path,
    context_root: Path | None,
    scope_input_root: Path | None,
    build_atlas_bundle_paths_fn: Callable[..., AtlasBundlePaths],
    build_public_animal_output_audit_fn: Callable[..., object],
    generate_country_report_fn: Callable[..., object],
    generate_multi_country_map_fn: Callable[..., MultiCountryMapReport],
    publish_animal_foundation_outputs_fn: Callable[..., dict[str, str]],
    publish_public_animal_reporting_outputs_fn: Callable[..., dict[str, str]],
    render_public_animal_output_audit_markdown_fn: Callable[..., str],
    write_summary_json_fn: Callable[[Path, dict[str, object]], None],
) -> None:
    """Write one planned fragment without reducer-owned cross-scope outputs."""
    staging_output_root = Path(staging_output_root)
    version_dir = Path(version_dir)
    published_output_root = Path(published_output_root)
    data_root = (
        Path(context_root)
        if context_root is not None
        else published_output_root.parents[1] / "data"
    )
    scopes = {scope.key: scope for scope in plan.geography.all_scopes()}
    if partition.kind in {"world", "regions"}:
        for scope_key in partition.scope_keys:
            scope = scopes[scope_key]
            generate_multi_country_map_fn(
                version_dir=version_dir,
                countries=scope.countries,
                output_dir=staging_output_root.joinpath(*scope.output_dir_parts),
                title=scope.map_title,
                slug=scope.slug,
                context_root=context_root,
                published_output_dir=published_output_root.joinpath(
                    *scope.output_dir_parts
                ),
                geography_scope=scope,
            )
        return
    if partition.kind == "countries":
        for scope_key in partition.scope_keys:
            scope = scopes[scope_key]
            parent_scope = scopes[str(scope.parent_key)]
            parent_paths = build_atlas_bundle_paths_fn(
                output_dir=Path(*parent_scope.output_dir_parts),
                slug=parent_scope.slug,
                version=version_dir.name,
            )
            country_dir = Path(*scope.output_dir_parts)
            parent_map_path = str(
                Path(
                    os.path.relpath(
                        Path(*parent_scope.output_dir_parts)
                        / parent_paths.map_html_path.name,
                        country_dir,
                    )
                )
            )
            generate_country_report_fn(
                version_dir=version_dir,
                country=scope.countries[0],
                output_dir=staging_output_root / country_dir,
                map_reference=(parent_scope.map_title, parent_map_path),
                published_output_dir=published_output_root / country_dir,
                context_root=context_root,
            )
        return
    if partition.kind != "foundation":
        raise ValueError(f"Unsupported report partition kind: {partition.kind}")
    if scope_input_root is None:
        raise ValueError("Foundation partition requires scope_input_root")

    copy_scope_inputs(
        staging_output_root,
        scope_input_root=scope_input_root,
        plan=plan,
    )
    _, country_reports, _ = load_scope_reports(
        staging_output_root,
        plan=plan,
        version=version_dir.name,
    )
    country_output_dirs = tuple(
        staging_output_root.joinpath(*scope.output_dir_parts)
        for scope in plan.geography.country_scopes
    )
    publish_public_animal_reporting_outputs_fn(
        staging_output_root,
        data_root=data_root,
        country_reports=country_reports,
        country_output_dirs=country_output_dirs,
        atlas_output_dir=staging_output_root.joinpath(
            *plan.geography.world_scope.output_dir_parts
        ),
    )
    publish_animal_foundation_outputs_fn(
        staging_output_root,
        data_root=data_root,
        docs_root=published_output_root.parent,
    )
    raw_animal_output_audit = build_public_animal_output_audit_fn(
        data_root, staging_output_root
    )
    if not isinstance(raw_animal_output_audit, dict):
        raise ValueError("Animal output audit must be an object")
    animal_output_audit = cast(dict[str, object], raw_animal_output_audit)
    animal_output_audit["report_root"] = serialize_publication_path(
        published_output_root
    )
    write_summary_json_fn(
        staging_output_root / "animal_output_audit.json",
        animal_output_audit,
    )
    (staging_output_root / "animal_output_audit.md").write_text(
        render_public_animal_output_audit_markdown_fn(animal_output_audit),
        encoding="utf-8",
    )
    remove_scope_inputs(staging_output_root, plan=plan)


def require_release_gate(output_root: Path, *, enforce_release_gates: bool) -> None:
    """Retain the monolithic animal release-gate refusal boundary."""
    payload = _json_object(Path(output_root) / "animal_publication_release_gate.json")
    if enforce_release_gates and not bool(payload.get("overall_ok")):
        raise ValueError("Animal publication release gate failed")


def require_repository_claim_gate(
    output_root: Path, *, enforce_release_gates: bool
) -> None:
    """Retain the monolithic repository claim-audit refusal boundary."""
    payload = _json_object(Path(output_root) / "repository_claim_audit.json")
    if enforce_release_gates and not bool(payload.get("overall_ok")):
        raise ValueError("Repository claim audit failed")


def _json_object(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Required report gate cannot be read: {path}") from error
    if not isinstance(payload, dict):
        raise ValueError(f"Required report gate must be an object: {path}")
    return payload
