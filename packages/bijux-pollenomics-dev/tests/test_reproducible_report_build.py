from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
from pathlib import Path
import sys
from typing import cast

import pytest

from bijux_pollenomics_dev.ci.rebuild_reports import (
    CommandResult,
    ReproducibleReportError,
    Runner,
    inventory_inputs,
    load_policy,
    verify_reproducible_reports,
)


def _write_policy(root: Path, *, volatile: bool = False) -> Path:
    config = root / "policy.json"
    rule = (
        [
            {
                "id": "generated-date",
                "path_globs": ["**/*.json"],
                "pattern": '("generated_on": ")\\d{4}-\\d{2}-\\d{2}(")',
                "replacement": "\\1<GENERATED-DATE>\\2",
            }
        ]
        if volatile
        else []
    )
    config.write_text(
        json.dumps(
            {
                "schema_version": "reproducible-report-build-policy.v1",
                "generator": {
                    "module": "fixture_reporter",
                    "arguments": ["--output-root", "{output_root}"],
                },
                "input_paths": ["policy.json", "source.txt"],
                "allowed_input_symlinks": {},
                "excluded_input_globs": ["**/__pycache__", "**/*.pyc"],
                "require_clean_repository": False,
                "tracked_report_root": "docs/report",
                "volatile_text_rules": rule,
            }
        ),
        encoding="utf-8",
    )
    return config


def _fixture_repo(tmp_path: Path, *, volatile: bool = False) -> tuple[Path, Path]:
    (tmp_path / "docs/report").mkdir(parents=True)
    (tmp_path / "source.txt").write_text("source\n", encoding="utf-8")
    policy = _write_policy(tmp_path, volatile=volatile)
    return tmp_path, policy


def _assert_isolated_command(command: Sequence[str]) -> None:
    assert command[1:4] == ("-I", "-B", "-X")
    cache_option = command[4]
    assert cache_option.startswith("pycache_prefix=")
    assert not Path(cache_option.removeprefix("pycache_prefix=")).exists()


def _runner_with(payloads: list[dict[str, object]]) -> Runner:
    calls = iter(payloads)

    def run(command: Sequence[str], cwd: Path) -> CommandResult:
        del cwd
        _assert_isolated_command(command)
        output = Path(command[command.index("--output-root") + 1])
        output.mkdir()
        (output / "report.json").write_text(
            json.dumps(next(calls), sort_keys=True) + "\n", encoding="utf-8"
        )
        return CommandResult(0, "generated\n", "")

    return run


def test_two_builds_and_tracked_tree_must_match(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    payload: dict[str, object] = {"records": 3}
    (root / "docs/report/report.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=root / "artifacts/evidence",
        runner=_runner_with([payload, payload]),
    )

    assert report["status"] == "PASS"
    assert report["differences"] == []
    assert (root / "artifacts/evidence/evidence.json").is_file()
    assert (root / "artifacts/evidence/results.junit.xml").is_file()
    assert (root / "artifacts/evidence/diff.txt").is_file()


def test_replay_content_change_fails(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    payload: dict[str, object] = {"records": 3}
    (root / "docs/report/report.json").write_text(
        json.dumps(payload, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=root / "artifacts/evidence",
        runner=_runner_with([payload, {"records": 4}]),
    )

    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert any(row["comparison"] == "reference_vs_replay" for row in differences)


def test_tracked_inventory_path_change_fails(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    (root / "docs/report/old.json").write_text("{}\n", encoding="utf-8")

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=root / "artifacts/evidence",
        runner=_runner_with([{}, {}]),
    )

    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert {row["kind"] for row in differences} == {
        "additional",
        "missing",
    }


def test_declared_generated_date_is_the_only_tracked_volatility(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path, volatile=True)
    tracked = {"generated_on": "2020-01-01", "records": 3}
    rebuilt = {"generated_on": "2030-02-03", "records": 3}
    (root / "docs/report/report.json").write_text(
        json.dumps(tracked, sort_keys=True) + "\n", encoding="utf-8"
    )

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=root / "artifacts/evidence",
        runner=_runner_with([rebuilt, rebuilt]),
    )

    assert report["status"] == "PASS"
    inventories = cast(dict[str, list[dict[str, object]]], report["inventories"])
    assert inventories["tracked"][0]["sha256"] != inventories["reference"][0]["sha256"]
    assert (
        inventories["tracked"][0]["canonical_sha256"]
        == inventories["reference"][0]["canonical_sha256"]
    )


def test_input_change_during_build_fails(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    (root / "docs/report/report.json").write_text("{}\n", encoding="utf-8")
    calls = 0

    def mutating_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        nonlocal calls
        calls += 1
        output = Path(command[command.index("--output-root") + 1])
        output.mkdir()
        (output / "report.json").write_text("{}\n", encoding="utf-8")
        if calls == 2:
            (cwd / "source.txt").write_text("changed\n", encoding="utf-8")
        return CommandResult(0, "", "")

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=root / "artifacts/evidence",
        runner=mutating_runner,
    )

    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert differences[0]["kind"] == "changed_during_build"


def test_output_root_is_never_overwritten(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    evidence = root / "artifacts/evidence"
    evidence.mkdir(parents=True)

    with pytest.raises(ReproducibleReportError, match="already exists"):
        verify_reproducible_reports(
            repo_root=root,
            policy_path=policy,
            evidence_root=evidence,
            runner=_runner_with([]),
        )


def test_generator_failure_emits_machine_and_human_evidence(tmp_path: Path) -> None:
    root, policy = _fixture_repo(tmp_path)
    evidence = root / "artifacts/evidence"

    def failed_runner(command: Sequence[str], cwd: Path) -> CommandResult:
        del command, cwd
        return CommandResult(7, "", "generation failed\n")

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy,
        evidence_root=evidence,
        runner=failed_runner,
    )

    assert report["status"] == "FAIL"
    assert (evidence / "evidence.json").is_file()
    assert (evidence / "results.junit.xml").is_file()
    assert "generator" in (evidence / "diff.txt").read_text(encoding="utf-8")


def test_unapproved_input_symlink_is_rejected(tmp_path: Path) -> None:
    root, policy_path = _fixture_repo(tmp_path)
    source = root / "source.txt"
    source.unlink()
    source.symlink_to("real-source.txt")
    (root / "real-source.txt").write_text("source\n", encoding="utf-8")

    with pytest.raises(ReproducibleReportError, match="unapproved input symlink"):
        inventory_inputs(root, load_policy(policy_path))


def test_repository_policy_binds_canonical_report_command() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    policy_path = repo_root / "configs/ci/reproducible-report-build.json"
    policy = load_policy(policy_path)
    generator = policy["generator"]

    assert isinstance(generator, dict)
    assert generator["module"] == "bijux_pollenomics"
    assert generator["arguments"] == [
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
    ]
    assert policy["schema_version"] == "reproducible-report-build-policy.v2"
    assert policy["partitioning"] == {
        "schema_version": "published-report-partition-policy.v1",
        "country_group_size": 2,
    }
    input_paths = policy["input_paths"]
    assert isinstance(input_paths, list)
    assert ".github/workflows/scientific-verification.yml" in input_paths
    assert (
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild"
        in input_paths
    )
    assert sys.version_info >= (3, 11)


@pytest.mark.parametrize(
    ("filename", "payload"),
    (
        ("source.txt", b"\xef\xbb\xbfliteral\r\n"),
        ("source.txt", "Málaga 🙂\r\n".encode()),
        ("source.txt", b'{"generated_on": "2026-11-09"}\n'),
        ("source.json", b'\xff{"generated_on": "2026-11-09"}\r\n'),
        ("source.txt", b""),
    ),
)
def test_input_inventory_keeps_literal_content_when_not_normalized(
    tmp_path: Path, filename: str, payload: bytes
) -> None:
    root, policy_path = _fixture_repo(tmp_path, volatile=True)
    policy = load_policy(policy_path)
    policy["input_paths"] = ["policy.json", filename]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    (root / filename).write_bytes(payload)

    entry = next(
        row
        for row in inventory_inputs(root, load_policy(policy_path))
        if row.path == filename
    )
    digest = hashlib.sha256(payload).hexdigest()
    assert entry.as_json() == {
        "path": filename,
        "kind": "file",
        "size": len(payload),
        "sha256": digest,
        "canonical_sha256": digest,
    }


@pytest.mark.parametrize("suffix", (".json", ".md", ".html"))
def test_matching_rewrites_keep_order_unicode_and_line_endings(
    tmp_path: Path, suffix: str
) -> None:
    root, policy_path = _fixture_repo(tmp_path)
    filename = "source" + suffix
    policy = load_policy(policy_path)
    policy["input_paths"] = ["policy.json", filename]
    policy["volatile_text_rules"] = [
        {
            "id": "date-token",
            "path_globs": ["**/*" + suffix],
            "pattern": "generated [0-9]{4}-[0-9]{2}-[0-9]{2}",
            "replacement": "generated <DAY>",
        },
        {
            "id": "canonical-date",
            "path_globs": ["**/*" + suffix],
            "pattern": "<DAY>",
            "replacement": "<GENERATED-DATE>",
        },
    ]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    payload = "\ufeffMálaga 🙂 generated 2026-11-09\r\n".encode()
    expected = payload.replace(b"2026-11-09", b"<GENERATED-DATE>")
    (root / filename).write_bytes(payload)

    entry = next(
        row
        for row in inventory_inputs(root, load_policy(policy_path))
        if row.path == filename
    )
    assert entry.as_json() == {
        "path": filename,
        "kind": "file",
        "size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "canonical_sha256": hashlib.sha256(expected).hexdigest(),
    }


def test_date_only_input_drift_refuses_even_with_equal_canonical_hashes(
    tmp_path: Path,
) -> None:
    root, policy_path = _fixture_repo(tmp_path, volatile=True)
    policy = load_policy(policy_path)
    policy["input_paths"] = ["policy.json", "source.json"]
    policy_path.write_text(json.dumps(policy), encoding="utf-8")
    source = root / "source.json"
    source.write_text('{"generated_on": "2020-01-01"}\n', encoding="utf-8")
    (root / "docs/report/report.json").write_text("{}\n", encoding="utf-8")
    before = next(
        row for row in inventory_inputs(root, policy) if row.path == "source.json"
    )
    calls = 0

    def mutate_date(command: Sequence[str], cwd: Path) -> CommandResult:
        nonlocal calls
        calls += 1
        output = Path(command[command.index("--output-root") + 1])
        output.mkdir()
        (output / "report.json").write_text("{}\n", encoding="utf-8")
        if calls == 2:
            (cwd / "source.json").write_text(
                '{"generated_on": "2030-02-03"}\n', encoding="utf-8"
            )
        return CommandResult(0, "", "")

    report = verify_reproducible_reports(
        repo_root=root,
        policy_path=policy_path,
        evidence_root=root / "artifacts/evidence",
        runner=mutate_date,
    )
    after = next(
        row for row in inventory_inputs(root, policy) if row.path == "source.json"
    )
    assert before.canonical_sha256 == after.canonical_sha256
    assert before.sha256 != after.sha256
    assert report["status"] == "FAIL"
    differences = cast(list[dict[str, object]], report["differences"])
    assert any(row["kind"] == "changed_during_build" for row in differences)
