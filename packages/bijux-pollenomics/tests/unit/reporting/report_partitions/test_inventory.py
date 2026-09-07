from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.reporting.bundles.report_partitions.artifacts import (
    scientific_artifact_inventory,
)
from bijux_pollenomics.reporting.bundles.report_partitions.inventory import (
    assemble_fragment_files,
    copy_scope_inputs,
    relative_file_inventory,
)
from bijux_pollenomics.reporting.bundles.report_partitions.planning import (
    build_report_partition_plan,
)


def _fragment_roots(tmp_path: Path) -> dict[str, Path]:
    plan = build_report_partition_plan(("Sweden",), country_group_size=1)
    roots = {identity: tmp_path / identity for identity in plan.partition_ids}
    for root in roots.values():
        root.mkdir()
    (roots["world"] / "world").mkdir()
    (roots["world"] / "world" / "world.json").write_text("world")
    for scope in plan.geography.regional_scopes:
        path = roots["regions"].joinpath(*scope.output_dir_parts)
        path.mkdir(parents=True)
        (path / f"{scope.slug}.json").write_text(scope.key)
    country = roots["countries-000"] / "countries" / "sweden"
    country.mkdir(parents=True)
    (country / "sweden.json").write_text("country")
    for filename in {
        *scientific_artifact_inventory().values(),
        "animal_output_audit.json",
        "animal_output_audit.md",
    }:
        (roots["foundation"] / filename).write_text(filename)
    return roots


def test_assembly_rejects_missing_extra_and_overlapping_partitions(
    tmp_path: Path,
) -> None:
    plan = build_report_partition_plan(("Sweden",), country_group_size=1)
    roots = _fragment_roots(tmp_path)

    missing = dict(roots)
    missing.pop("foundation")
    with pytest.raises(ValueError, match="missing=.*foundation"):
        assemble_fragment_files(
            tmp_path / "missing", plan=plan, partition_roots=missing
        )

    extra = {**roots, "unplanned": tmp_path / "unplanned"}
    with pytest.raises(ValueError, match="extra=.*unplanned"):
        assemble_fragment_files(tmp_path / "extra", plan=plan, partition_roots=extra)

    overlap = roots["regions"] / "world" / "duplicate.json"
    overlap.parent.mkdir()
    overlap.write_text("duplicate")
    with pytest.raises(ValueError, match="paths differ from plan"):
        assemble_fragment_files(tmp_path / "overlap", plan=plan, partition_roots=roots)


def test_assembly_rejects_incomplete_foundation_inventory(tmp_path: Path) -> None:
    plan = build_report_partition_plan(("Sweden",), country_group_size=1)
    roots = _fragment_roots(tmp_path)
    (roots["foundation"] / "animal_output_audit.md").unlink()

    with pytest.raises(ValueError, match="Foundation partition inventory"):
        assemble_fragment_files(
            tmp_path / "assembled", plan=plan, partition_roots=roots
        )


def test_assembly_copies_each_owned_file_once(tmp_path: Path) -> None:
    plan = build_report_partition_plan(("Sweden",), country_group_size=1)
    roots = _fragment_roots(tmp_path)
    output = tmp_path / "assembled"

    assemble_fragment_files(output, plan=plan, partition_roots=roots)

    expected = {
        path.relative_to(root).as_posix()
        for root in roots.values()
        for path in root.rglob("*")
        if path.is_file()
    }
    actual = {
        path.relative_to(output).as_posix()
        for path in output.rglob("*")
        if path.is_file()
    }
    assert actual == expected


def test_inventory_rejects_symbolic_link(tmp_path: Path) -> None:
    root = tmp_path / "fragment"
    root.mkdir()
    external = tmp_path / "external.json"
    external.write_text("external")
    (root / "linked.json").symlink_to(external)

    with pytest.raises(ValueError, match="symbolic link: linked.json"):
        relative_file_inventory(root)


def test_foundation_scope_inputs_reject_symbolic_link(tmp_path: Path) -> None:
    plan = build_report_partition_plan(("Sweden",), country_group_size=1)
    scope_input_root = tmp_path / "scope-input"
    for scope in plan.geography.all_scopes():
        source = scope_input_root.joinpath(*scope.output_dir_parts)
        source.mkdir(parents=True)
        (source / "owned.json").write_text("owned")
    external = tmp_path / "external.json"
    external.write_text("external")
    world_root = scope_input_root.joinpath(*plan.geography.world_scope.output_dir_parts)
    (world_root / "linked.json").symlink_to(external)

    with pytest.raises(ValueError, match="symbolic link: linked.json"):
        copy_scope_inputs(
            tmp_path / "foundation",
            scope_input_root=scope_input_root,
            plan=plan,
        )
