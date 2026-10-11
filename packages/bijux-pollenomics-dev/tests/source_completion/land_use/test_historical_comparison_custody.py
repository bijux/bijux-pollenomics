"""Authenticate the prior Git product and current report before comparison."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.source_completion.land_use import historical_comparison
from bijux_pollenomics_dev.source_completion.sweden_land_use_replay import (
    OUTPUT_FILES,
    PRODUCT,
)


def _git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        (
            "git",
            "-C",
            str(repository),
            "-c",
            "maintenance.auto=false",
            "-c",
            "gc.auto=false",
            *arguments,
        ),
        check=True,
        capture_output=True,
        text=True,
        timeout=15,
    )
    return result.stdout.strip()


def _commit(repository: Path, message: str) -> None:
    _git(repository, "add", "docs", "data", "packages")
    _git(
        repository,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        message,
    )


@pytest.fixture
def governed_repository(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Build a real two-commit repository with authenticated prior product blobs."""
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    files = {}
    for name in OUTPUT_FILES:
        relative = PRODUCT / name
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((name + "\n").encode())
        files[relative.as_posix()] = {
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
    _git(repository, "add", "docs")
    _git(
        repository,
        "-c",
        "user.name=Fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "-qm",
        "prior country product",
    )
    baseline = _git(repository, "rev-parse", "HEAD")
    tree = _git(repository, "rev-parse", f"{baseline}^{{tree}}")
    for relative_name, row in files.items():
        row["git_blob_oid"] = _git(
            repository, "rev-parse", f"{baseline}:{relative_name}"
        )
    policy_root = repository / historical_comparison.POLICY_ROOT
    policy_root.mkdir(parents=True)
    for name in historical_comparison.POLICY_NAMES:
        (policy_root / name).write_text("# policy fixture\n", encoding="utf-8")
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
    _commit(repository, "bind prior product identity")
    (repository / "artifacts/jobs").mkdir(parents=True)

    def compare(_: Path, revision: str, output: Path) -> dict[str, Any]:
        assert revision == baseline
        (output / "historical-comparison.json").write_bytes(b'{"checked":true}\n')
        return {"baseline_revision": revision}

    monkeypatch.setattr(historical_comparison, "compare_historical", compare)
    return repository


def _packet(repository: Path) -> dict[str, Any]:
    payload = json.loads((repository / historical_comparison.PACKET).read_text())
    if not isinstance(payload, dict) or any(
        not isinstance(key, str) for key in payload
    ):
        raise ValueError("fixture packet is not an object with string keys")
    return {str(key): value for key, value in payload.items()}


def _commit_packet(repository: Path, packet: dict[str, Any]) -> None:
    (repository / historical_comparison.PACKET).write_text(
        json.dumps(packet), encoding="utf-8"
    )
    _commit(repository, "test source packet refusal")


def test_real_prior_git_commit_tree_and_blobs_publish_one_output(
    governed_repository: Path,
) -> None:
    repository = governed_repository
    output = repository / "artifacts/jobs/validated.json"
    result = historical_comparison.publish(repository, output)
    assert result["baseline_revision"] == _packet(repository)["baseline_revision"]
    assert output.read_bytes() == b'{"checked":true}\n'
    assert len(tuple((repository / historical_comparison.STAGES).iterdir())) == 1


@pytest.mark.parametrize("corruption", ["commit", "tree", "sha256", "git_blob_oid"])
def test_prior_git_identity_corruption_refuses_before_publication(
    governed_repository: Path, corruption: str
) -> None:
    repository = governed_repository
    packet = _packet(repository)
    if corruption == "commit":
        packet["baseline_revision"] = "f" * 40
    elif corruption == "tree":
        packet["baseline_tree"] = "0" * 40
    else:
        first = next(iter(packet["files"].values()))
        first[corruption] = "0" * 40 if corruption == "git_blob_oid" else "0" * 64
    _commit_packet(repository, packet)
    output = repository / "artifacts/jobs/refused.json"
    if corruption == "commit":
        with pytest.raises(subprocess.CalledProcessError):
            historical_comparison.publish(repository, output)
    elif corruption == "tree":
        with pytest.raises(ValueError, match="source packet identity differs"):
            historical_comparison.publish(repository, output)
    else:
        with pytest.raises(ValueError, match="product Git blob differs"):
            historical_comparison.publish(repository, output)
    assert not output.exists()


def test_dirty_current_product_refuses_before_comparison(
    governed_repository: Path,
) -> None:
    repository = governed_repository
    (repository / PRODUCT / OUTPUT_FILES[0]).write_bytes(b"changed without commit\n")
    output = repository / "artifacts/jobs/dirty.json"
    with pytest.raises(ValueError, match="clean tracked candidate"):
        historical_comparison.publish(repository, output)
    assert not output.exists()


def test_untracked_policy_member_and_direct_source_change_refuse(
    governed_repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = governed_repository
    output = repository / "artifacts/jobs/membership.json"
    (repository / historical_comparison.POLICY_ROOT / "extra.py").write_text(
        "# untracked new policy source\n", encoding="utf-8"
    )
    with pytest.raises(ValueError, match="policy membership differs"):
        historical_comparison.publish(repository, output)
    (repository / historical_comparison.POLICY_ROOT / "extra.py").unlink()
    with monkeypatch.context() as patcher:
        patcher.setattr(
            historical_comparison,
            "SOURCE_PATHS",
            historical_comparison.SOURCE_PATHS[:-1],
        )
        with pytest.raises(ValueError, match="direct source membership differs"):
            historical_comparison.publish(repository, output)
    assert not output.exists()


def test_existing_outside_and_symlink_destinations_refuse(
    governed_repository: Path, tmp_path: Path
) -> None:
    repository = governed_repository
    existing = repository / "artifacts/jobs/existing.json"
    existing.write_bytes(b"existing\n")
    with pytest.raises(ValueError, match="absent under artifacts"):
        historical_comparison.publish(repository, existing)
    assert existing.read_bytes() == b"existing\n"
    with pytest.raises(ValueError, match="absent under artifacts"):
        historical_comparison.publish(repository, repository / "docs/unowned.json")
    external = tmp_path / "external"
    external.mkdir()
    linked = repository / "artifacts/jobs/linked"
    linked.symlink_to(external, target_is_directory=True)
    with pytest.raises(ValueError, match="output parent must be confined"):
        historical_comparison.publish(repository, linked / "report.json")
    assert not (external / "report.json").exists()


def test_packet_symlink_is_not_an_authenticated_repository_source(
    governed_repository: Path, tmp_path: Path
) -> None:
    repository = governed_repository
    packet = repository / historical_comparison.PACKET
    outside = tmp_path / "retained-packet.json"
    outside.write_bytes(packet.read_bytes())
    packet.unlink()
    packet.symlink_to(outside)
    with pytest.raises(ValueError, match="regular"):
        historical_comparison._regular(repository, historical_comparison.PACKET)
