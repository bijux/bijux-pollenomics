from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import (
    inventory_reports,
    load_policy,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    parse_binding,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import (
    discover_manifests,
    inventory_json,
    merge_fragment_trees,
)
from bijux_pollenomics_dev.ci.report_rebuild.execution import load_fragments
from bijux_pollenomics_dev.ci.report_rebuild.workflow import (
    assemble_partition_lane,
    build_partition,
    build_partition_plan,
    verify_partitioned_rebuild,
)


def _policy(root: Path) -> Path:
    path = root / "policy.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": "reproducible-report-build-policy.v2",
                "generator": {
                    "module": "bijux_pollenomics",
                    "arguments": [
                        "publish-reports",
                        "--aadr-root",
                        "{repo_root}/data/aadr",
                        "--version",
                        "v66",
                        "--output-root",
                        "{output_root}",
                        "--published-output-root",
                        "docs/report",
                        "--context-root",
                        "{repo_root}/data",
                    ],
                },
                "input_paths": ["policy.json", "source.txt"],
                "allowed_input_symlinks": {},
                "excluded_input_globs": ["**/__pycache__", "**/*.pyc"],
                "require_clean_repository": False,
                "partitioning": {
                    "schema_version": "published-report-partition-policy.v1",
                    "country_group_size": 2,
                },
                "tracked_report_root": "docs/report",
                "volatile_text_rules": [],
            }
        ),
        encoding="utf-8",
    )
    return path


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    (tmp_path / "docs/report").mkdir(parents=True)
    (tmp_path / "source.txt").write_text("source\n", encoding="utf-8")
    policy_path = _policy(tmp_path)
    plan_path = tmp_path / "plan.json"
    build_partition_plan(
        repo_root=tmp_path,
        policy_path=policy_path,
        output_path=plan_path,
    )
    return tmp_path, policy_path, plan_path


def _fragment_path(partition_id: str) -> str:
    return f"fragments/{partition_id}.txt"


def _write_complete_tree(
    root: Path, *, plan_path: Path, report_payload: str = "report\n"
) -> None:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    root.mkdir(parents=True, exist_ok=True)
    for partition_id in plan["partition_ids"]:
        path = root / _fragment_path(partition_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = report_payload if partition_id == "world" else f"{partition_id}\n"
        path.write_text(payload, encoding="utf-8")
    (root / "reducer.txt").write_text("reduced\n", encoding="utf-8")


def _assembly(
    root: Path,
    *,
    lane: str,
    binding: dict[str, object],
    report_payload: str = "report\n",
    overlap: bool = False,
) -> Path:
    assembly = root / lane
    output = assembly / "output"
    _write_complete_tree(
        output, plan_path=root.parent / "plan.json", report_payload=report_payload
    )
    policy = load_policy(root.parent / "policy.json")
    inventory = inventory_reports(output, policy)
    plan = json.loads((root.parent / "plan.json").read_text(encoding="utf-8"))
    partition_ids = plan["partition_ids"]
    fragment_paths = {
        partition_id: [_fragment_path(partition_id)] for partition_id in partition_ids
    }
    if overlap:
        fragment_paths["foundation"] = [_fragment_path("world")]
    assembly_paths = ["reducer.txt"]
    manifest = {
        "schema_version": "partitioned-report-assembly.v1",
        "assembly_id": "assemble",
        "assembly_paths": assembly_paths,
        "binding": binding,
        "fragment_manifest_sha256": {
            partition_id: str(index) * 64
            for index, partition_id in enumerate(partition_ids, start=1)
        },
        "fragment_paths": fragment_paths,
        "inventory": inventory_json(inventory),
        "lane": lane,
        "partition_ids": partition_ids,
    }
    (assembly / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return assembly / "manifest.json"


def _fragment(
    root: Path,
    *,
    partition_id: str,
    relative_path: str,
    binding: dict[str, object],
) -> None:
    fragment = root / partition_id
    output = fragment / "output"
    path = output / relative_path
    path.parent.mkdir(parents=True)
    path.write_text(f"{partition_id}\n", encoding="utf-8")
    policy = load_policy(root.parent / "policy.json")
    inventory = inventory_reports(output, policy)
    (fragment / "manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "partitioned-report-fragment.v1",
                "binding": binding,
                "lane": "reference",
                "partition_id": partition_id,
                "relative_paths": [relative_path],
                "inventory": inventory_json(inventory),
            }
        ),
        encoding="utf-8",
    )


def test_runtime_plan_has_exact_default_partition_dag(tmp_path: Path) -> None:
    root, policy_path, _ = _fixture(tmp_path)

    report = build_partition_plan(
        repo_root=root,
        policy_path=policy_path,
        output_path=root / "artifacts/plan.json",
    )

    assert report["scope_partition_ids"] == [
        "world",
        "regions",
        "countries-000",
        "countries-001",
    ]
    assert report["dependent_partition_ids"] == ["foundation"]
    assert report["partition_ids"] == [
        "world",
        "regions",
        "countries-000",
        "countries-001",
        "foundation",
    ]


def test_runtime_plan_rejects_noncanonical_generator_contract(tmp_path: Path) -> None:
    root, policy_path, _ = _fixture(tmp_path)
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    policy["generator"]["arguments"][4] = "v65"
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="canonical report generator"):
        build_partition_plan(
            repo_root=root,
            policy_path=policy_path,
            output_path=root / "artifacts/plan.json",
        )


def test_partition_consumer_rejects_same_id_plan_with_changed_grouping(
    tmp_path: Path,
) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert plan["partition_ids"] == [
        "world",
        "regions",
        "countries-000",
        "countries-001",
        "foundation",
    ]
    plan["parameters"]["country_group_size"] = 3
    plan_path.write_text(json.dumps(plan), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="canonical bound plan"):
        build_partition(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            lane="reference",
            partition_id="world",
            evidence_root=root / "artifacts/fragment",
        )


def test_partition_build_rejects_governed_input_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import bijux_pollenomics.reporting.bundles.report_partitions as runtime

    root, policy_path, plan_path = _fixture(tmp_path)

    def mutate_input(partition_id: str, **kwargs: object) -> SimpleNamespace:
        output_root = Path(str(kwargs["output_root"]))
        (output_root / "world").mkdir(parents=True)
        (output_root / "world/report.txt").write_text("report\n", encoding="utf-8")
        (root / "source.txt").write_text("mutated\n", encoding="utf-8")
        return SimpleNamespace(
            partition=partition_id,
            output_root=output_root,
            relative_paths=("world/report.txt",),
        )

    monkeypatch.setattr(runtime, "generate_report_partition", mutate_input)

    with pytest.raises(ReportRebuildError, match="post-build"):
        build_partition(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            lane="reference",
            partition_id="world",
            evidence_root=root / "artifacts/fragment",
        )


def test_partition_build_accepts_runtime_inventory_order_difference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import bijux_pollenomics.reporting.bundles.report_partitions as runtime

    root, policy_path, plan_path = _fixture(tmp_path)

    def generate(partition_id: str, **kwargs: object) -> SimpleNamespace:
        output_root = Path(str(kwargs["output_root"]))
        (output_root / "world").mkdir(parents=True)
        (output_root / "world/a.txt").write_text("a\n", encoding="utf-8")
        (output_root / "world/z.txt").write_text("z\n", encoding="utf-8")
        return SimpleNamespace(
            partition=partition_id,
            output_root=output_root,
            relative_paths=("world/z.txt", "world/a.txt"),
        )

    monkeypatch.setattr(runtime, "generate_report_partition", generate)

    manifest = build_partition(
        repo_root=root,
        policy_path=policy_path,
        plan_path=plan_path,
        lane="reference",
        partition_id="world",
        evidence_root=root / "artifacts/fragment",
    )

    relative_paths = manifest["relative_paths"]
    assert isinstance(relative_paths, list)
    assert set(relative_paths) == {"world/a.txt", "world/z.txt"}


def test_lane_assembly_rejects_governed_input_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import bijux_pollenomics.reporting.bundles.report_partitions as runtime

    root, policy_path, plan_path = _fixture(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    fragments = root / "fragment-artifacts"
    for partition_id in plan["partition_ids"]:
        _fragment(
            fragments,
            partition_id=partition_id,
            relative_path=_fragment_path(partition_id),
            binding=plan["binding"],
        )

    def mutate_input(**kwargs: object) -> SimpleNamespace:
        output_root = Path(str(kwargs["output_root"]))
        _write_complete_tree(output_root, plan_path=plan_path, report_payload="world\n")
        (root / "source.txt").write_text("mutated\n", encoding="utf-8")
        return SimpleNamespace(output_root=output_root)

    monkeypatch.setattr(runtime, "assemble_report_partitions", mutate_input)

    with pytest.raises(ReportRebuildError, match="post-assembly"):
        assemble_partition_lane(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            lane="reference",
            partition_artifacts_root=fragments,
            evidence_root=root / "artifacts/assembly",
        )


def test_partitioned_rebuild_requires_two_complete_trees_and_tracked_match(
    tmp_path: Path,
) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    reference = _assembly(
        root / "assemblies", lane="reference", binding=plan["binding"]
    )
    replay = _assembly(root / "assemblies", lane="replay", binding=plan["binding"])

    report = verify_partitioned_rebuild(
        repo_root=root,
        policy_path=policy_path,
        plan_path=plan_path,
        reference_manifest_path=reference,
        replay_manifest_path=replay,
        evidence_root=root / "artifacts/final",
    )

    assert report["status"] == "PASS"
    assert report["differences"] == []


def test_partitioned_rebuild_detects_cross_lane_content_drift(tmp_path: Path) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    reference = _assembly(
        root / "assemblies", lane="reference", binding=plan["binding"]
    )
    replay = _assembly(
        root / "assemblies",
        lane="replay",
        binding=plan["binding"],
        report_payload="drift\n",
    )

    report = verify_partitioned_rebuild(
        repo_root=root,
        policy_path=policy_path,
        plan_path=plan_path,
        reference_manifest_path=reference,
        replay_manifest_path=replay,
        evidence_root=root / "artifacts/final",
    )

    assert report["status"] == "FAIL"
    differences = report["differences"]
    assert isinstance(differences, list)
    assert all(isinstance(row, dict) for row in differences)
    assert any(row["comparison"] == "reference_vs_replay" for row in differences)


def test_assembly_manifest_rejects_overlapping_path_ownership(tmp_path: Path) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    reference = _assembly(
        root / "assemblies", lane="reference", binding=plan["binding"], overlap=True
    )
    replay = _assembly(root / "assemblies", lane="replay", binding=plan["binding"])

    with pytest.raises(ReportRebuildError, match="ownership"):
        verify_partitioned_rebuild(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            reference_manifest_path=reference,
            replay_manifest_path=replay,
            evidence_root=root / "artifacts/final",
        )


def test_partitioned_rebuild_rejects_a_different_assembly_identity(
    tmp_path: Path,
) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    reference = _assembly(
        root / "assemblies", lane="reference", binding=plan["binding"]
    )
    replay = _assembly(root / "assemblies", lane="replay", binding=plan["binding"])
    manifest = json.loads(reference.read_text(encoding="utf-8"))
    manifest["assembly_id"] = "different-reducer"
    reference.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="wrong reducer"):
        verify_partitioned_rebuild(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            reference_manifest_path=reference,
            replay_manifest_path=replay,
            evidence_root=root / "artifacts/final",
        )


def test_fragment_merge_rejects_cross_partition_overlap(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "same.txt").write_text("one\n", encoding="utf-8")
    (second / "same.txt").write_text("two\n", encoding="utf-8")
    policy_path = _policy(tmp_path)
    policy = load_policy(policy_path)

    with pytest.raises(ReportRebuildError, match="overlap"):
        merge_fragment_trees(
            {
                "first": (first, inventory_reports(first, policy)),
                "second": (second, inventory_reports(second, policy)),
            },
            tmp_path / "merged",
        )


def test_manifest_discovery_rejects_symlink_and_unknown_schema(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    valid = root / "valid/manifest.json"
    valid.parent.mkdir(parents=True)
    valid.write_text(
        json.dumps({"schema_version": "partitioned-report-fragment.v1"}),
        encoding="utf-8",
    )
    unknown = root / "unknown/manifest.json"
    unknown.parent.mkdir()
    unknown.write_text(
        json.dumps({"schema_version": "partitioned-report-fragment.v0"}),
        encoding="utf-8",
    )

    with pytest.raises(ReportRebuildError, match="unexpected manifest schema"):
        discover_manifests(root, "partitioned-report-fragment.v1")

    unknown.unlink()
    unknown.symlink_to(valid)
    with pytest.raises(ReportRebuildError, match="regular file"):
        discover_manifests(root, "partitioned-report-fragment.v1")


def test_fragment_loading_rejects_an_extra_manifest_from_another_lane(
    tmp_path: Path,
) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    fragments = root / "fragment-artifacts"
    for partition_id in plan["partition_ids"]:
        _fragment(
            fragments,
            partition_id=partition_id,
            relative_path=_fragment_path(partition_id),
            binding=plan["binding"],
        )
    wrong_lane = fragments / "wrong-lane/manifest.json"
    wrong_lane.parent.mkdir()
    extra = json.loads((fragments / "world/manifest.json").read_text(encoding="utf-8"))
    extra["lane"] = "replay"
    wrong_lane.write_text(json.dumps(extra), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="wrong lane"):
        load_fragments(
            artifacts_root=fragments,
            expected_ids=tuple(plan["partition_ids"]),
            lane="reference",
            binding=parse_binding(plan["binding"], "plan binding"),
            policy=load_policy(policy_path),
        )
