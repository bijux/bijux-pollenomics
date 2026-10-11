"""Keep concurrent comparison stages and final publication exclusive."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
from threading import Barrier
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.land_use import historical_comparison
from bijux_pollenomics_dev.source_completion.sweden_land_use_replay import (
    OUTPUT_FILES,
    PRODUCT,
)


@pytest.fixture
def comparison_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Supply fixed Git responses while exercising the actual file publication route."""
    repository = tmp_path / "repository"
    (repository / "artifacts/jobs").mkdir(parents=True)
    policy = repository / historical_comparison.POLICY_ROOT
    policy.mkdir(parents=True)
    for name in historical_comparison.POLICY_NAMES:
        (policy / name).write_text("# fixed policy fixture\n", encoding="utf-8")
    baseline = "b" * 40
    tree = "c" * 40
    blob = "d" * 40
    files: dict[str, dict[str, str | int]] = {}
    baseline_bytes: dict[str, bytes] = {}
    for name in OUTPUT_FILES:
        relative = (PRODUCT / name).as_posix()
        contents = (name + "\n").encode()
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(contents)
        baseline_bytes[relative] = contents
        files[relative] = {
            "sha256": hashlib.sha256(contents).hexdigest(),
            "git_blob_oid": blob,
            "bytes": len(contents),
        }
    packet = repository / historical_comparison.PACKET
    packet.parent.mkdir(parents=True)
    packet.write_text(
        json.dumps(
            {
                "schema_version": "sweden-land-use-prior-product.v1",
                "baseline_revision": baseline,
                "baseline_tree": tree,
                "files": files,
            }
        ),
        encoding="utf-8",
    )

    def git(_: Path, *arguments: str) -> bytes:
        if arguments == ("status", "--porcelain=v1", "--untracked-files=no"):
            return b""
        if arguments == ("rev-parse", "--verify", f"{baseline}^{{commit}}"):
            return (baseline + "\n").encode()
        if arguments == ("rev-parse", f"{baseline}^{{tree}}"):
            return (tree + "\n").encode()
        if arguments[:1] == ("rev-parse",) and arguments[1].startswith(baseline + ":"):
            return (blob + "\n").encode()
        if arguments[:1] == ("show",) and arguments[1].startswith(baseline + ":"):
            return baseline_bytes[arguments[1].split(":", 1)[1]]
        if arguments[:1] == ("show",) and arguments[1].startswith("HEAD:"):
            return (repository / arguments[1][5:]).read_bytes()
        raise AssertionError(f"unexpected Git query: {arguments}")

    def compare(_: Path, revision: str, output: Path) -> dict[str, Any]:
        assert revision == baseline
        (output / "historical-comparison.json").write_bytes(b'{"fixed":true}\n')
        return {"baseline_revision": revision}

    monkeypatch.setattr(historical_comparison, "_git", git)
    monkeypatch.setattr(historical_comparison, "compare_historical", compare)
    return repository


def test_two_distinct_destinations_share_ancestor_without_sharing_stage(
    comparison_repository: Path,
) -> None:
    repository = comparison_repository
    stages = repository / historical_comparison.STAGES
    start = Barrier(2)

    def publish(name: str) -> dict[str, object]:
        start.wait(timeout=5)
        output = repository / "artifacts/jobs" / name
        return historical_comparison.publish(repository, output)

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(publish, "first.json")
        second = pool.submit(publish, "second.json")
        assert first.result(timeout=20)["baseline_revision"] == "b" * 40
        assert second.result(timeout=20)["baseline_revision"] == "b" * 40
    assert sorted(path.name for path in stages.iterdir()) == sorted(
        hashlib.sha256(name.encode()).hexdigest()
        for name in ("jobs/first.json", "jobs/second.json")
    )
    for name in ("first.json", "second.json"):
        assert (
            repository / "artifacts/jobs" / name
        ).read_bytes() == b'{"fixed":true}\n'
        assert not (repository / "artifacts/jobs" / f"{name}.part").exists()


def test_final_publish_refuses_competing_destination_and_cleans_partial(
    comparison_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = comparison_repository
    output = repository / "artifacts/jobs/claimed.json"
    original_link = os.link

    def competing_link(source: os.PathLike[str], target: os.PathLike[str]) -> None:
        Path(target).write_bytes(b"competing writer\n")
        original_link(source, target)

    monkeypatch.setattr(os, "link", competing_link)
    with pytest.raises(FileExistsError):
        historical_comparison.publish(repository, output)
    assert output.read_bytes() == b"competing writer\n"
    assert not output.with_name(output.name + ".part").exists()


def test_compare_failure_leaves_no_final_or_partial_output(
    comparison_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = comparison_repository
    output = repository / "artifacts/jobs/failed.json"

    def failed(_: Path, __: str, ___: Path) -> dict[str, object]:
        raise RuntimeError("source comparison failed")

    monkeypatch.setattr(historical_comparison, "compare_historical", failed)
    with pytest.raises(RuntimeError, match="source comparison failed"):
        historical_comparison.publish(repository, output)
    assert not output.exists()
    assert not output.with_name(output.name + ".part").exists()
    assert len(tuple((repository / historical_comparison.STAGES).iterdir())) == 1


def test_staged_read_failure_removes_exclusive_partial(
    comparison_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = comparison_repository
    output = repository / "artifacts/jobs/unreadable.json"
    original_read = Path.read_bytes

    def read(self: Path) -> bytes:
        if (
            self.name == "historical-comparison.json"
            and self.parent.parent == repository / historical_comparison.STAGES
        ):
            raise OSError("staged report became unreadable")
        return original_read(self)

    monkeypatch.setattr(Path, "read_bytes", read)
    with pytest.raises(OSError, match="staged report became unreadable"):
        historical_comparison.publish(repository, output)
    assert not output.exists()
    assert not output.with_name(output.name + ".part").exists()
