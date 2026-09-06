from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
from pathlib import Path
import shutil
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_sead_evidence import (
    CommandResult,
    GitIdentity,
    InventoryEntry,
    Runner,
    compare_inventories,
    verify_governed_sead_evidence_fixed_point,
)

_RUN_ID = "sead-full-evidence-39bfff6a-ce80714e"


def _write_bundle(root: Path) -> Path:
    root.mkdir(parents=True)
    for index in range(52):
        (root / f"part-{index:02d}.json").write_text(
            json.dumps({"index": index}, sort_keys=True) + "\n", encoding="utf-8"
        )
    manifest = root / "evidence_materialization_manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": "sead-evidence-materialization-manifest.v1",
                "source_run_id": _RUN_ID,
                "build_id": "sha256:" + "b" * 64,
                "acquisition_manifest_sha256": "a" * 64,
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    return manifest


def _fixture_repository(tmp_path: Path) -> tuple[Path, dict[str, tuple[str, ...]]]:
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "source.txt").write_text("stable\n", encoding="utf-8")
    tracked = tmp_path / f"data/sead/normalized/acquisitions/{_RUN_ID}"
    _write_bundle(tracked)
    return tmp_path, {
        "data": ("source.txt",),
        "tracked_evidence": (f"data/sead/normalized/acquisitions/{_RUN_ID}",),
    }


def _clean_git_identity(
    repository_root: Path, input_paths: Sequence[str]
) -> GitIdentity:
    del repository_root, input_paths
    return GitIdentity("c" * 40, "t" * 40, ())


def _copying_runner(repository_root: Path) -> Runner:
    tracked = repository_root / f"data/sead/normalized/acquisitions/{_RUN_ID}"
    manifest = tracked / "evidence_materialization_manifest.json"
    manifest_sha256 = hashlib.sha256(manifest.read_bytes()).hexdigest()
    tracked_payload = json.loads(manifest.read_text(encoding="utf-8"))

    def run(command: Sequence[str], cwd: Path) -> CommandResult:
        assert cwd == repository_root
        assert command[1:4] == ("-I", "-B", "-X")
        output = Path(command[command.index("--output-root") + 1])
        shutil.copytree(tracked, output)
        summary = {
            "schema_version": "sead-governed-evidence-rebuild.v1",
            "status": "PASS",
            "source_run_id": tracked_payload["source_run_id"],
            "build_id": tracked_payload["build_id"],
            "acquisition_manifest_sha256": tracked_payload[
                "acquisition_manifest_sha256"
            ],
            "evidence_manifest_sha256": manifest_sha256,
            "file_count": 53,
            "network_policy": "forbidden",
            "output_root": str(output),
        }
        return CommandResult(0, json.dumps(summary, sort_keys=True) + "\n", "")

    return run


def test_fixed_point_pass_cleans_candidates_and_retains_proof(tmp_path: Path) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=_copying_runner(repository),
        git_identity_reader=_clean_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "PASS"
    assert report["candidate_retention"] == "deleted_after_complete_proof"
    assert not (evidence / "candidates").exists()
    assert (evidence / "evidence.json").is_file()
    assert (evidence / "results.junit.xml").is_file()
    assert (evidence / "logs/reference.stdout.log").is_file()
    inventories = cast(dict[str, list[dict[str, object]]], report["bundle_inventories"])
    assert {name: len(rows) for name, rows in inventories.items()} == {
        "reference": 53,
        "replay": 53,
        "tracked": 53,
    }


def test_replay_mismatch_fails_and_retains_candidates(tmp_path: Path) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"
    base_runner = _copying_runner(repository)
    calls = 0

    def mismatching_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        nonlocal calls
        calls += 1
        result = base_runner(command, cwd)
        if calls == 2:
            output = Path(command[command.index("--output-root") + 1])
            (output / "part-07.json").write_text("changed\n", encoding="utf-8")
        return result

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=mismatching_runner,
        git_identity_reader=_clean_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "FAIL"
    assert report["candidate_retention"] == "retained_for_failure"
    assert (evidence / "candidates/reference").is_dir()
    assert (evidence / "candidates/replay").is_dir()
    differences = cast(list[dict[str, object]], report["differences"])
    assert any(
        row["comparison"] == "reference_vs_replay"
        and row["kind"] == "sha256_mismatch"
        and row["path"] == "part-07.json"
        for row in differences
    )


def test_matching_rebuilds_that_drift_from_tracked_evidence_fail(
    tmp_path: Path,
) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"
    base_runner = _copying_runner(repository)

    def stale_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        result = base_runner(command, cwd)
        output = Path(command[command.index("--output-root") + 1])
        (output / "part-11.json").write_text("same rebuilt drift\n", encoding="utf-8")
        return result

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=stale_runner,
        git_identity_reader=_clean_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert not any(row["comparison"] == "reference_vs_replay" for row in differences)
    assert any(
        row["comparison"] == "tracked_vs_reference" and row["kind"] == "sha256_mismatch"
        for row in differences
    )


def test_input_mutation_invalidates_matching_candidates(tmp_path: Path) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"
    base_runner = _copying_runner(repository)
    calls = 0

    def mutating_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        nonlocal calls
        calls += 1
        result = base_runner(command, cwd)
        if calls == 2:
            (repository / "source.txt").write_text("mutated\n", encoding="utf-8")
        return result

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=mutating_runner,
        git_identity_reader=_clean_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert any(row["kind"] == "input_changed_during_build" for row in differences)
    assert (evidence / "candidates").is_dir()


def test_dirty_governed_input_refuses_generation(tmp_path: Path) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"
    generator_called = False

    def runner(command: Sequence[str], cwd: Path) -> CommandResult:
        nonlocal generator_called
        del command, cwd
        generator_called = True
        return CommandResult(0, "", "")

    def dirty_git_identity(
        repository_root: Path, input_paths: Sequence[str]
    ) -> GitIdentity:
        del repository_root, input_paths
        return GitIdentity("c" * 40, "t" * 40, (" M source.txt",))

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=runner,
        git_identity_reader=dirty_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "FAIL"
    assert generator_called is False
    assert (evidence / "candidates").is_dir()
    differences = cast(list[dict[str, object]], report["differences"])
    assert any(row["kind"] == "relevant_input_not_committed" for row in differences)


def test_generator_failure_keeps_partial_candidate_and_logs(tmp_path: Path) -> None:
    repository, input_groups = _fixture_repository(tmp_path)
    evidence = repository / "artifacts/proof"

    def failed_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        del cwd
        output = Path(command[command.index("--output-root") + 1])
        output.mkdir()
        (output / "partial.json").write_text("{}\n", encoding="utf-8")
        return CommandResult(7, "", "generator failed\n")

    report = verify_governed_sead_evidence_fixed_point(
        repository_root=repository,
        evidence_root=evidence,
        runner=failed_runner,
        git_identity_reader=_clean_git_identity,
        input_groups=input_groups,
    )

    assert report["status"] == "FAIL"
    assert (evidence / "candidates/reference/partial.json").is_file()
    assert (evidence / "logs/reference.stderr.log").read_text(encoding="utf-8") == (
        "generator failed\n"
    )
    assert (evidence / "evidence.json").is_file()


def test_inventory_differences_have_deterministic_order() -> None:
    left = (
        InventoryEntry("b.json", 1, "b"),
        InventoryEntry("a.json", 1, "a"),
    )
    right = (
        InventoryEntry("c.json", 1, "c"),
        InventoryEntry("b.json", 2, "x"),
    )

    differences = compare_inventories(left, right, comparison="proof")

    assert [(row["path"], row["kind"]) for row in differences] == [
        ("a.json", "missing"),
        ("b.json", "byte_count_mismatch"),
        ("b.json", "sha256_mismatch"),
        ("c.json", "additional"),
    ]


def test_make_exposes_the_repository_fixed_point_command() -> None:
    repository_root = Path(__file__).resolve().parents[3]
    makefile = (repository_root / "makes/pollenomics-verification.mk").read_text(
        encoding="utf-8"
    )

    assert "verify-sead-evidence-fixed-point: root-check-env" in makefile
    assert "-m bijux_pollenomics_dev.ci.rebuild_sead_evidence" in makefile
