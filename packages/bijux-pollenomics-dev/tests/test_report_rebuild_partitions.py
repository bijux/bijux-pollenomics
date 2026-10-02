from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import (
    inventory_reports,
    load_policy,
)
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    ReportRebuildError,
    parse_binding,
    sha256_bytes,
)
from bijux_pollenomics_dev.ci.report_rebuild.evidence import (
    discover_manifests,
    inventory_json,
    merge_fragment_trees,
)
from bijux_pollenomics_dev.ci.report_rebuild.execution import load_fragments
from bijux_pollenomics_dev.ci.report_rebuild.workflow import (
    assemble_partition_lane,
    build_owner_output,
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
    owner_root = root.parent / "artifacts/owners" / lane
    owner_manifests = sorted(
        path
        for path in owner_root.rglob("manifest.json")
        if not {"output", "producer-output"}.intersection(
            path.relative_to(owner_root).parts
        )
    )
    if owner_manifests:
        manifest["schema_version"] = "partitioned-report-assembly.v2"
        manifest["owner_paths"] = {
            path.parent.relative_to(owner_root).as_posix(): [
                entry["path"]
                for entry in json.loads(path.read_text(encoding="utf-8"))["inventory"]
            ]
            for path in owner_manifests
        }
        manifest["owner_manifest_sha256"] = {
            path.parent.relative_to(owner_root).as_posix(): sha256_bytes(
                path.read_bytes()
            )
            for path in owner_manifests
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
    from bijux_pollenomics_dev.ci.report_rebuild import execution

    root, policy_path, plan_path = _fixture(tmp_path)

    def mutate_input(request: dict[str, object]) -> dict[str, object]:
        output_root = Path(str(request["output_root"]))
        (output_root / "world").mkdir(parents=True)
        (output_root / "world/report.txt").write_text("report\n", encoding="utf-8")
        (root / "source.txt").write_text("mutated\n", encoding="utf-8")
        return {"partition_id": "world", "relative_paths": ["world/report.txt"]}

    monkeypatch.setattr(execution, "run_runtime_command", mutate_input)

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
    from bijux_pollenomics_dev.ci.report_rebuild import execution

    root, policy_path, plan_path = _fixture(tmp_path)

    def generate(request: dict[str, object]) -> dict[str, object]:
        output_root = Path(str(request["output_root"]))
        (output_root / "world").mkdir(parents=True)
        (output_root / "world/a.txt").write_text("a\n", encoding="utf-8")
        (output_root / "world/z.txt").write_text("z\n", encoding="utf-8")
        return {
            "partition_id": "world",
            "relative_paths": ["world/z.txt", "world/a.txt"],
        }

    monkeypatch.setattr(execution, "run_runtime_command", generate)

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
    from bijux_pollenomics_dev.ci.report_rebuild import execution

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

    def mutate_input(request: dict[str, object]) -> dict[str, object]:
        output_root = Path(str(request["output_root"]))
        _write_complete_tree(output_root, plan_path=plan_path, report_payload="world\n")
        (root / "source.txt").write_text("mutated\n", encoding="utf-8")
        return {"output_root": str(output_root)}

    monkeypatch.setattr(execution, "run_runtime_command", mutate_input)

    with pytest.raises(ReportRebuildError, match="post-assembly"):
        assemble_partition_lane(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            lane="reference",
            partition_artifacts_root=fragments,
            evidence_root=root / "artifacts/assembly",
        )


def test_lane_assembly_passes_checked_owner_inputs_to_reducer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild import execution

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
    owner_manifest = _owner(
        root,
        lane="reference",
        source_paths={"summary.csv": "method/summary.csv"},
    )

    def assemble(request: dict[str, object]) -> dict[str, object]:
        owner_input_root = Path(str(request["owner_input_root"]))
        assert (owner_input_root / "method/summary.csv").read_text() == "summary.csv\n"
        output_root = Path(str(request["output_root"]))
        _write_complete_tree(output_root, plan_path=plan_path, report_payload="world\n")
        return {"output_root": str(output_root)}

    monkeypatch.setattr(execution, "run_runtime_command", assemble)
    manifest = assemble_partition_lane(
        repo_root=root,
        policy_path=policy_path,
        plan_path=plan_path,
        lane="reference",
        partition_artifacts_root=fragments,
        evidence_root=root / "artifacts/assembly",
        owner_artifacts_root=owner_manifest.parent.parent,
        owner_ids=("petrkunes",),
    )

    assert manifest["schema_version"] == "partitioned-report-assembly.v2"
    assert manifest["owner_paths"] == {"petrkunes": ["method/summary.csv"]}
    assert manifest["owner_manifest_sha256"] == {
        "petrkunes": sha256_bytes(owner_manifest.read_bytes())
    }
    assert not (root / "artifacts/assembly/output/method/summary.csv").exists()


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


def test_partitioned_rebuild_keeps_authenticated_r_source_out_of_generated_owners(
    tmp_path: Path,
) -> None:
    root, policy_path, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    prefix = Path("method-certification/original-r-reference/reference-bundle")
    repository = Path(__file__).resolve().parents[3]
    shutil.copytree(repository / "docs/report" / prefix, root / "docs/report" / prefix)
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
        retain_original_r_reference=True,
    )

    assert report["status"] == "PASS"
    assert report["schema_version"] == "reproducible-report-build-evidence.v3"
    assert report["owners"] == {"reference": {}, "replay": {}}
    sources = report["retained_sources"]
    assert isinstance(sources, dict)
    retained = sources["original_r_reference"]
    assert len(retained["paths"]) == 125
    assert all(path.startswith(prefix.as_posix() + "/") for path in retained["paths"])

    (root / "docs/report" / prefix / "oracle/C0000.csv").write_text(
        "changed\n", encoding="utf-8"
    )
    with pytest.raises(ReportRebuildError, match="retained source validation failed"):
        verify_partitioned_rebuild(
            repo_root=root,
            policy_path=policy_path,
            plan_path=plan_path,
            reference_manifest_path=reference,
            replay_manifest_path=replay,
            evidence_root=root / "artifacts/changed-reference",
            retain_original_r_reference=True,
        )


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


def _owner(
    root: Path,
    *,
    lane: str,
    source_paths: dict[str, str],
    produced: tuple[str, ...] | None = None,
    owner_id: str = "petrkunes",
) -> Path:
    payload = "from pathlib import Path; import sys; root=Path(sys.argv[1]); "
    payload += "[(root / name).write_text(name + '\\n', encoding='utf-8') "
    payload += "for name in sys.argv[2:]]"
    output = root / "artifacts" / "owners" / lane / owner_id
    source = root / "external-source.txt"
    if not source.exists():
        source.write_text("source identity\n", encoding="utf-8")
    build_owner_output(
        repo_root=root,
        policy_path=root / "policy.json",
        plan_path=root / "plan.json",
        lane=lane,
        owner_id=owner_id,
        producer_command=(
            sys.executable,
            "-c",
            payload,
            "{output_root}",
            *(produced if produced is not None else tuple(source_paths)),
        ),
        producer_inputs={"external-source": source},
        source_paths=source_paths,
        evidence_root=output,
    )
    return output / "manifest.json"


def _reference_owners(report: dict[str, object]) -> dict[str, object]:
    owners = report["owners"]
    assert isinstance(owners, dict)
    reference = owners["reference"]
    assert isinstance(reference, dict)
    return reference


def _verify_with_owner(
    root: Path, *, owner_ids: tuple[str, ...] = ("petrkunes",)
) -> dict[str, object]:
    plan = json.loads((root / "plan.json").read_text(encoding="utf-8"))
    reference = _assembly(
        root / "assemblies", lane="reference", binding=plan["binding"]
    )
    replay = _assembly(root / "assemblies", lane="replay", binding=plan["binding"])
    return verify_partitioned_rebuild(
        repo_root=root,
        policy_path=root / "policy.json",
        plan_path=root / "plan.json",
        reference_manifest_path=reference,
        replay_manifest_path=replay,
        reference_owners_root=root / "artifacts/owners/reference",
        replay_owners_root=root / "artifacts/owners/replay",
        owner_ids=owner_ids,
        evidence_root=root / "artifacts/final",
    )


def test_mixed_owner_rebuild_covers_four_generated_outputs(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    directory = "method-certification/petrkunes-r-comparison"
    paths = {
        name: f"{directory}/{name}"
        for name in (
            "summary.csv",
            "taxa.csv",
            "bootstrap-full-grid.csv",
            "native-report.json",
        )
    }
    for lane in ("reference", "replay"):
        _owner(root, lane=lane, source_paths=paths)
    for name, target in paths.items():
        destination = root / "docs/report" / target
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(name + "\n", encoding="utf-8")

    report = _verify_with_owner(root)

    assert report["status"] == "PASS"
    assert set(_reference_owners(report)) == {"petrkunes"}
    owner = _reference_owners(report)["petrkunes"]
    assert isinstance(owner, dict)
    assert owner["producer_argv"][0] == sys.executable
    assert owner["producer_inputs"]["external-source"]["size"] == len(
        "source identity\n"
    )
    assert owner["producer_inputs"]["external-source"]["path"] == (
        "external-source.txt"
    )


def test_mixed_owner_requires_assembly_input_receipt(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    for lane in ("reference", "replay"):
        _owner(root, lane=lane, source_paths={"summary.csv": "method/summary.csv"})
    for lane in ("reference", "replay"):
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        manifest_path = _assembly(
            root / "assemblies", lane=lane, binding=plan["binding"]
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["schema_version"] = "partitioned-report-assembly.v1"
        del manifest["owner_paths"]
        del manifest["owner_manifest_sha256"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="did not consume owner inputs"):
        verify_partitioned_rebuild(
            repo_root=root,
            policy_path=root / "policy.json",
            plan_path=plan_path,
            reference_manifest_path=root / "assemblies/reference/manifest.json",
            replay_manifest_path=root / "assemblies/replay/manifest.json",
            reference_owners_root=root / "artifacts/owners/reference",
            replay_owners_root=root / "artifacts/owners/replay",
            owner_ids=("petrkunes",),
            evidence_root=root / "artifacts/final",
        )


def test_mixed_owner_accepts_a_report_named_manifest(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    target = "method/manifest.json"
    for lane in ("reference", "replay"):
        _owner(root, lane=lane, source_paths={"manifest.json": target})
    destination = root / "docs/report" / target
    destination.parent.mkdir(parents=True)
    destination.write_text("manifest.json\n", encoding="utf-8")

    assert _verify_with_owner(root)["status"] == "PASS"


def test_owner_stage_reuses_the_publisher_input_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, _, _ = _fixture(tmp_path)
    from bijux_pollenomics_dev.ci.report_rebuild import planning

    def refuse_reinventory(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("owner stage must reuse the bound publisher inventory")

    monkeypatch.setattr(planning, "inventory_inputs", refuse_reinventory)

    assert _owner(
        root,
        lane="reference",
        source_paths={"summary.csv": "method/summary.csv"},
    ).is_file()


@pytest.mark.parametrize("produced", [(), ("summary.csv", "extra.csv")])
def test_owner_producer_requires_exact_generated_file_set(
    tmp_path: Path, produced: tuple[str, ...]
) -> None:
    root, _, _ = _fixture(tmp_path)
    with pytest.raises(ReportRebuildError, match="coverage is not exact"):
        _owner(
            root,
            lane="reference",
            source_paths={"summary.csv": "method/summary.csv"},
            produced=produced,
        )


def test_owner_evidence_cannot_use_tracked_report_tree(tmp_path: Path) -> None:
    root, _, _ = _fixture(tmp_path)
    with pytest.raises(ReportRebuildError, match="below repository artifacts"):
        build_owner_output(
            repo_root=root,
            policy_path=root / "policy.json",
            plan_path=root / "plan.json",
            lane="reference",
            owner_id="petrkunes",
            producer_command=(sys.executable, "-c", "pass", "{output_root}"),
            producer_inputs={"source": root / "source.txt"},
            source_paths={"summary.csv": "method/summary.csv"},
            evidence_root=root / "docs/report",
        )


def test_owner_cannot_repackage_its_tracked_result_as_a_generated_output(
    tmp_path: Path,
) -> None:
    root, _, plan_path = _fixture(tmp_path)
    target = root / "docs/report/method/summary.csv"
    target.parent.mkdir(parents=True)
    target.write_text("retained result\n", encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="claimed tracked output"):
        build_owner_output(
            repo_root=root,
            policy_path=root / "policy.json",
            plan_path=plan_path,
            lane="reference",
            owner_id="method",
            producer_command=(sys.executable, "-c", "pass", "{output_root}"),
            producer_inputs={"copied-result": target},
            source_paths={"summary.csv": "method/summary.csv"},
            evidence_root=root / "artifacts/owners/reference/method",
        )


def test_verifier_rejects_a_self_fed_owner_receipt(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    target = root / "docs/report/method/summary.csv"
    target.parent.mkdir(parents=True)
    target.write_text("summary.csv\n", encoding="utf-8")
    for lane in ("reference", "replay"):
        manifest_path = _owner(
            root, lane=lane, source_paths={"summary.csv": "method/summary.csv"}
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["producer_inputs"] = {
            "copied-result": {
                "path": "docs/report/method/summary.csv",
                "sha256": sha256_bytes(target.read_bytes()),
                "size": target.stat().st_size,
            }
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="claimed tracked output"):
        _verify_with_owner(root)


def test_mixed_owner_rebuild_rejects_missing_owner(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    for lane in ("reference", "replay"):
        (root / "artifacts/owners" / lane).mkdir(parents=True)

    with pytest.raises(ReportRebuildError, match="coverage is not exact"):
        _verify_with_owner(root)


def test_mixed_owner_rebuild_rejects_changed_external_input(tmp_path: Path) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    target = "method/summary.csv"
    for lane in ("reference", "replay"):
        _owner(root, lane=lane, source_paths={"summary.csv": target})
    (root / "external-source.txt").write_text("changed\n", encoding="utf-8")

    with pytest.raises(ReportRebuildError, match="producer inputs changed"):
        _verify_with_owner(root)


@pytest.mark.parametrize("mutation", ["binding", "bytes", "inputs", "argv", "overlap"])
def test_mixed_owner_rebuild_rejects_changed_evidence(
    tmp_path: Path, mutation: str
) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    target = "method/summary.csv"
    (root / "docs/report/method").mkdir()
    (root / "docs/report" / target).write_text("summary.csv\n", encoding="utf-8")
    for lane in ("reference", "replay"):
        _owner(root, lane=lane, source_paths={"summary.csv": target})
    reference_manifest = root / "artifacts/owners/reference/petrkunes/manifest.json"
    if mutation == "binding":
        manifest = json.loads(reference_manifest.read_text(encoding="utf-8"))
        manifest["binding"]["inputs_sha256"] = "stale"
        reference_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "bytes":
        (reference_manifest.parent / "output" / target).write_text(
            "changed\n", encoding="utf-8"
        )
    elif mutation == "inputs":
        manifest = json.loads(reference_manifest.read_text(encoding="utf-8"))
        manifest["producer_inputs"]["external-source"]["sha256"] = "0" * 64
        reference_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    elif mutation == "argv":
        manifest = json.loads(reference_manifest.read_text(encoding="utf-8"))
        manifest["producer_argv"][-1] = "other.csv"
        reference_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    else:
        for lane in ("reference", "replay"):
            path = root / f"artifacts/owners/{lane}/petrkunes/manifest.json"
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["source_paths"] = {"summary.csv": _fragment_path("world")}
            manifest["inventory"][0]["path"] = _fragment_path("world")
            path.write_text(json.dumps(manifest), encoding="utf-8")
            destination = path.parent / "output" / _fragment_path("world")
            destination.parent.mkdir(parents=True)
            (path.parent / "output" / target).rename(destination)
    with pytest.raises(
        ReportRebuildError, match="binding|manifest|overlaps|changed|argv"
    ):
        _verify_with_owner(root)


@pytest.mark.parametrize(
    "owner_id",
    [
        "neotoma/pollen-screen/compact-summary",
        "countries/denmark/solsoe-source-lineage/root-lineage",
    ],
)
def test_mixed_owner_rebuild_accepts_nested_domain_identity(
    tmp_path: Path, owner_id: str
) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    target = "method/manifest.json"
    for lane in ("reference", "replay"):
        _owner(
            root, lane=lane, owner_id=owner_id, source_paths={"manifest.json": target}
        )
    destination = root / "docs/report" / target
    destination.parent.mkdir(parents=True)
    destination.write_text("manifest.json\n", encoding="utf-8")
    report = _verify_with_owner(root, owner_ids=(owner_id,))
    assert report["status"] == "PASS"
    assert set(_reference_owners(report)) == {owner_id}


@pytest.mark.parametrize(
    "owner_id",
    ["../escape", "/absolute", "domain//leaf", "domain/./leaf", "domain\\leaf"],
)
def test_owner_producer_rejects_unsafe_identity_before_execution(
    tmp_path: Path, owner_id: str
) -> None:
    root, _, _ = _fixture(tmp_path)
    with pytest.raises(ReportRebuildError, match="safe relative path"):
        _owner(
            root,
            lane="reference",
            owner_id=owner_id,
            source_paths={"summary.csv": "method/summary.csv"},
        )
    assert not (root / "artifacts/owners").exists()


@pytest.mark.parametrize(
    "mutation", ["symlink", "empty", "file", "identity", "manifest-directory"]
)
def test_nested_owner_loader_rejects_invalid_namespace(
    tmp_path: Path, mutation: str
) -> None:
    from bijux_pollenomics_dev.ci.report_rebuild.verification import _load_owner_outputs

    root, policy_path, plan_path = _fixture(tmp_path)
    manifest_path = _owner(
        root,
        lane="reference",
        owner_id="domain/leaf",
        source_paths={"summary.csv": "method/summary.csv"},
    )
    owners_root = root / "artifacts/owners/reference"
    if mutation == "symlink":
        namespace = owners_root / "domain"
        namespace.rename(owners_root / "retained")
        namespace.symlink_to(owners_root / "retained", target_is_directory=True)
    elif mutation == "empty":
        (owners_root / "missing/deep").mkdir(parents=True)
    elif mutation == "file":
        (owners_root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
    elif mutation == "manifest-directory":
        manifest_path.unlink()
        manifest_path.mkdir()
    else:
        record = json.loads(manifest_path.read_text(encoding="utf-8"))
        record["owner_id"] = "other/leaf"
        manifest_path.write_text(json.dumps(record), encoding="utf-8")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    with pytest.raises(
        ReportRebuildError, match="artifact directory|manifest|differs from identity"
    ):
        _load_owner_outputs(
            artifacts_root=owners_root,
            repo_root=root,
            lane="reference",
            binding=parse_binding(plan["binding"], "test binding"),
            policy=load_policy(policy_path),
            publisher_ids=set(plan["partition_ids"]),
        )


def test_mixed_owner_rebuild_keeps_same_leaf_in_distinct_domains(
    tmp_path: Path,
) -> None:
    root, _, plan_path = _fixture(tmp_path)
    _write_complete_tree(root / "docs/report", plan_path=plan_path)
    identities = ("countries/denmark/summary", "source-relations/neotoma/summary")
    for index, identity in enumerate(identities):
        target = f"method/{index}/summary.csv"
        for lane in ("reference", "replay"):
            _owner(
                root, lane=lane, owner_id=identity, source_paths={"summary.csv": target}
            )
        destination = root / "docs/report" / target
        destination.parent.mkdir(parents=True)
        destination.write_text("summary.csv\n", encoding="utf-8")
    report = _verify_with_owner(root, owner_ids=identities)
    assert report["status"] == "PASS"
    assert set(_reference_owners(report)) == set(identities)
