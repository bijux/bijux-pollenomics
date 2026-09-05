"""Repository Identity tests."""

from __future__ import annotations
import os
from pathlib import Path
import subprocess
from typing import cast
import pytest
from bijux_pollenomics.provenance import (
    ArtifactInput,
    ReleaseEvidenceError,
    hash_repository_object,
)
from bijux_pollenomics.provenance.release_evidence import artifacts as release_artifacts
from bijux_pollenomics.provenance.release_evidence import (
    repository as release_repository,
)
from .support import _artifacts, _build, _digest


def test_producer_tree_digest_excludes_python_runtime_cache(tmp_path: Path) -> None:
    producer = tmp_path / "producer"
    producer.mkdir()
    (producer / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    cache = producer / "__pycache__"
    cache.mkdir()
    cached_bytecode = cache / "source.cpython-311.pyc"
    cached_bytecode.write_bytes(b"first runtime cache")
    optimized_bytecode = cache / "source.cpython-311.pyo"
    optimized_bytecode.write_bytes(b"first optimized runtime cache")
    nested_source = cache / "real_source.py"
    nested_source.write_text("CACHE_HELPER = 1\n", encoding="utf-8")
    suffix_directory = producer / "owned.pyc"
    suffix_directory.mkdir()
    suffix_source = suffix_directory / "real_source.py"
    suffix_source.write_text("SUFFIX_HELPER = 1\n", encoding="utf-8")
    digest = cast(
        str,
        release_repository._hash_repository_object(
            tmp_path,
            "producer",
            exclude_python_cache=True,
        )["output_digest"],
    )
    artifact = ArtifactInput(
        identity="producer",
        role="producer",
        path="producer",
        media_type="text/x-python",
        schema_version="producer.v1",
        parents=(),
        config_digests=(),
        producer_digest=digest,
        output_digest=digest,
    )

    before = release_artifacts._artifact_record(tmp_path, artifact)
    generic_before = hash_repository_object(tmp_path, "producer")
    cached_bytecode.write_bytes(b"different runtime cache")
    optimized_bytecode.write_bytes(b"different optimized runtime cache")
    after = release_artifacts._artifact_record(tmp_path, artifact)

    assert before == after
    assert hash_repository_object(tmp_path, "producer") != generic_before
    nested_source.write_text("CACHE_HELPER = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_artifacts._artifact_record(tmp_path, artifact)
    nested_source.write_text("CACHE_HELPER = 1\n", encoding="utf-8")
    suffix_source.write_text("SUFFIX_HELPER = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_artifacts._artifact_record(tmp_path, artifact)
    suffix_source.write_text("SUFFIX_HELPER = 1\n", encoding="utf-8")
    (producer / "source.py").write_text("VALUE = 2\n", encoding="utf-8")
    with pytest.raises(ReleaseEvidenceError, match="artifact digest changed"):
        release_artifacts._artifact_record(tmp_path, artifact)


def test_producer_tree_cache_exclusion_does_not_hide_symlink(
    tmp_path: Path,
) -> None:
    producer = tmp_path / "producer"
    producer.mkdir()
    (producer / "source.py").write_text("VALUE = 1\n", encoding="utf-8")
    (producer / "linked.pyc").symlink_to(producer / "source.py")

    with pytest.raises(ReleaseEvidenceError, match="safely open"):
        release_repository._hash_repository_object(
            tmp_path,
            "producer",
            exclude_python_cache=True,
        )


def test_fixture_policy_is_refused_inside_a_git_worktree(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    (tmp_path / ".git").mkdir()

    with pytest.raises(
        ReleaseEvidenceError, match="fixture release policy is forbidden"
    ):
        _build(tmp_path, artifacts=artifacts)


def test_product_repository_state_binds_git_and_untracked_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    untracked = tmp_path / "untracked.txt"
    untracked.write_text("untracked bytes\n", encoding="utf-8")
    commit = "a" * 40
    tree = "b" * 40
    responses = {
        ("rev-parse", "--show-toplevel"): f"{tmp_path}\n".encode(),
        ("rev-parse", "HEAD"): f"{commit}\n".encode(),
        ("rev-parse", "HEAD^{tree}"): f"{tree}\n".encode(),
        ("status", "--porcelain=v1", "-z", "--untracked-files=all"): (
            b"?? untracked.txt\0"
        ),
        ("ls-files", "-z"): b"tracked.txt\0",
        ("diff", "--binary", "HEAD", "--"): b"tracked diff\n",
        ("ls-files", "--others", "--exclude-standard", "-z"): (b"untracked.txt\0"),
    }
    calls: list[tuple[str, ...]] = []

    def fake_run(
        argv: tuple[str, ...], **_kwargs: object
    ) -> subprocess.CompletedProcess[bytes]:
        assert argv[:3] == ("git", "-C", str(tmp_path))
        arguments = argv[3:]
        calls.append(arguments)
        return subprocess.CompletedProcess(argv, 0, responses[arguments], b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    state = release_repository._repository_state(tmp_path, "product")

    assert state["head_commit"] == commit
    assert state["head_tree"] == tree
    assert state["dirty"] is True
    assert state["untracked_objects"] == [
        {"path": "untracked.txt", **hash_repository_object(tmp_path, "untracked.txt")}
    ]
    assert calls == list(responses)


def test_tree_hash_is_stable_and_accounts_for_members(tmp_path: Path) -> None:
    _artifacts(tmp_path)

    observed = hash_repository_object(tmp_path, "snapshot")

    assert observed["object_type"] == "tree"
    assert observed["file_count"] == 1
    assert observed["byte_size"] == len(b"record_id,value\n1,2\n")


def test_descriptor_relative_hashing_resists_parent_substitution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    governed = tmp_path / "governed"
    governed.mkdir()
    (governed / "input.txt").write_text("governed\n", encoding="utf-8")
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    (attacker / "input.txt").write_text("attacker\n", encoding="utf-8")
    original_open = os.open
    substituted = False

    def swapping_open(
        path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
        flags: int,
        mode: int = 0o777,
        *,
        dir_fd: int | None = None,
    ) -> int:
        nonlocal substituted
        if path == "input.txt" and dir_fd is not None and not substituted:
            governed.rename(tmp_path / "governed-original")
            governed.symlink_to(attacker, target_is_directory=True)
            substituted = True
        return original_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", swapping_open)

    observed = hash_repository_object(tmp_path, "governed/input.txt")

    assert substituted is True
    assert observed["output_digest"] == _digest(b"governed\n")


def test_paths_cannot_escape_or_traverse_symlinks(tmp_path: Path) -> None:
    artifacts = _artifacts(tmp_path)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    escaped = ArtifactInput(**{**receipt.__dict__, "path": "../receipt.json"})
    artifacts[artifacts.index(receipt)] = escaped
    with pytest.raises(ReleaseEvidenceError, match="escapes repository"):
        _build(tmp_path, artifacts=artifacts)

    artifacts = _artifacts(tmp_path)
    outside = tmp_path.parent / "outside-release-evidence.txt"
    outside.write_text("outside\n", encoding="utf-8")
    link = tmp_path / "linked-receipt.json"
    link.symlink_to(outside)
    receipt = next(item for item in artifacts if item.identity == "receipt")
    artifacts[artifacts.index(receipt)] = ArtifactInput(
        **{
            **receipt.__dict__,
            "path": "linked-receipt.json",
            "output_digest": _digest(b"outside\n"),
        }
    )
    with pytest.raises(ReleaseEvidenceError, match="unsafe"):
        _build(tmp_path, artifacts=artifacts)
