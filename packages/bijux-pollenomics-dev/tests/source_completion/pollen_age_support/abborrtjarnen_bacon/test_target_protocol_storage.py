"""Read one exact target protocol without replaying the source job or sampler."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon import (
    sampler_accuracy as subject,
)
from bijux_pollenomics_dev.source_completion.pollen_age_support.abborrtjarnen_bacon.inputs import (
    PROTOCOL,
)

EXECUTION = "0d374ce2190e5e44f70c8b28f18612809688af76"
ROOT = next(parent for parent in Path(__file__).parents if (parent / ".git").is_dir())


def _git(repository: Path, *arguments: str) -> bytes:
    return subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "-C",
            str(repository),
            "-c",
            "user.name=bijux",
            "-c",
            "user.email=bijux@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "-c",
            "core.attributesFile=/dev/null",
            *arguments,
        ],
        stderr=subprocess.PIPE,
        timeout=10,
    )


@pytest.fixture
def own_protocol(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, bytes]:
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(repository, "init", "-q")
    path = repository / PROTOCOL
    path.parent.mkdir(parents=True)
    body = b'{"model":{"owned_control":1},"execution":{"seeds":[1,2]}}\n'
    path.write_bytes(body)
    _git(repository, "add", "--", str(PROTOCOL))
    _git(repository, "commit", "-q", "-m", "test(protocol): retain owned metadata")
    revision = _git(repository, "rev-parse", "HEAD").decode().strip()
    blob = _git(repository, "rev-parse", f"HEAD:{PROTOCOL}").decode().strip()
    monkeypatch.setattr(
        subject,
        "_ORIGINAL_TARGET_PROTOCOL",
        (
            EXECUTION,
            revision,
            str(PROTOCOL),
            "100644",
            blob,
            len(body),
            hashlib.sha256(body).hexdigest(),
        ),
    )
    return repository, body


@pytest.mark.parametrize(
    "damage", [None, "execution", "path", "nonancestor", "blob", "mode", "size", "sha"]
)
def test_owned_protocol_storage_keeps_every_binding_strict(
    own_protocol: tuple[Path, bytes],
    monkeypatch: pytest.MonkeyPatch,
    damage: str | None,
) -> None:
    repository, body = own_protocol
    assert subject._original_target_protocol_bytes(repository, EXECUTION) == body
    execution, revision, path, mode, blob, size, digest = (
        subject._ORIGINAL_TARGET_PROTOCOL
    )
    supplied: object = EXECUTION
    if damage == "execution":
        supplied = "another original execution"
    elif damage == "path":
        path += ".unknown"
    elif damage == "nonancestor":
        _git(repository, "checkout", "--orphan", "owned-unbound-root")
        _git(
            repository,
            "commit",
            "-q",
            "--allow-empty",
            "-m",
            "test(protocol): isolate owned root",
        )
    elif damage == "blob":
        blob = "0" * 40
    elif damage == "mode":
        _git(repository, "update-index", "--chmod=+x", "--", path)
        _git(
            repository,
            "commit",
            "-q",
            "-m",
            "test(protocol): retain incorrect owned mode",
        )
        revision = _git(repository, "rev-parse", "HEAD").decode().strip()
    elif damage == "size":
        size += 1
    elif damage == "sha":
        digest = "0" * 64
    monkeypatch.setattr(
        subject,
        "_ORIGINAL_TARGET_PROTOCOL",
        (execution, revision, path, mode, blob, size, digest),
    )
    if damage is None:
        assert subject._original_target_protocol_bytes(repository, supplied) == body
    else:
        with pytest.raises((ValueError, subprocess.CalledProcessError)):
            subject._original_target_protocol_bytes(repository, supplied)
    assert (repository / PROTOCOL).read_bytes() == body


def test_real_target_metadata_uses_reachable_normal_git_storage_only() -> None:
    expected = (
        EXECUTION,
        "f3a4ff64c2db06cb0d3d832d9b7e67159b63c439",
        "reports/science/chronology/abborrtjarnen-bacon/physical-rate-protocol.json",
        "100644",
        "1f2d4961f835da2fd5984e3f63f35ce6d13b1b9b",
        14653,
        "9853d0f6387428589f2a9ce6f81e9bd8096c161b70e9732d8dd21165cd525a1d",
    )
    assert expected == subject._ORIGINAL_TARGET_PROTOCOL
    before = (ROOT / PROTOCOL).read_bytes()
    value = subject._original_target_protocol_bytes(ROOT, EXECUTION)
    assert len(value) == expected[5]
    assert hashlib.sha256(value).hexdigest() == expected[6]
    assert isinstance(json.loads(value), dict)
    assert value == before
    assert (ROOT / PROTOCOL).read_bytes() == before
