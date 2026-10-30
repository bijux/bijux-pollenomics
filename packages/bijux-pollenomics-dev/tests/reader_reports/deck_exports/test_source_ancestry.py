"""Keep original deck execution IDs separate from reachable retained storage."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[5]
ORIGINAL = "0caba19fdca39e183dce2b1a3929d1b94495cc21"
STORAGE = "417480948b34b6661bba2acfa0d5b82a23d3e2e4"
SPEC = importlib.util.spec_from_file_location(
    "scientific_deck_downloads", ROOT / "configs/docs/science_downloads.py"
)
assert SPEC is not None and SPEC.loader is not None
HOOK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOOK)


def test_mapped_storage_ancestry_uses_real_no_replace_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = []

    def resolve(repository: Path, revision: str) -> str:
        assert repository == ROOT and revision == ORIGINAL
        return STORAGE

    def command(argv: list[str], **kwargs: Any) -> SimpleNamespace:
        calls.append(argv)
        assert kwargs["check"] is True and kwargs["timeout"] == 30
        return SimpleNamespace(stdout=b"reachable storage\n")

    monkeypatch.setattr(HOOK, "source_revision", resolve)
    monkeypatch.setattr(HOOK.subprocess, "run", command)
    assert (
        HOOK._retained_export_git(ROOT, "merge-base", "--is-ancestor", ORIGINAL, "HEAD")
        == b"reachable storage\n"
    )
    assert calls == [
        [
            "git",
            "--no-replace-objects",
            "-C",
            str(ROOT),
            "merge-base",
            "--is-ancestor",
            STORAGE,
            "HEAD",
        ]
    ]


@pytest.mark.parametrize(
    "arguments",
    [
        ("rev-parse", "--verify", "HEAD"),
        ("ls-tree", "-r", "-z", "b" * 40, "--", "presentation/developer.tex"),
        ("merge-base", "--is-ancestor", ORIGINAL, "other-ref"),
        ("merge-base", "--is-ancestor", ORIGINAL, "HEAD", "extra"),
    ],
)
def test_other_git_operations_are_forwarded_without_revision_substitution(
    monkeypatch: pytest.MonkeyPatch, arguments: tuple[str, ...]
) -> None:
    def unexpected(*args: Any) -> str:
        pytest.fail("Non-storage operation attempted source revision resolution")

    def command(repository: Path, *args: str) -> bytes:
        assert repository == ROOT and args == arguments
        return b"unchanged Git operation"

    monkeypatch.setattr(HOOK, "source_revision", unexpected)
    monkeypatch.setattr(HOOK, "_git", command)
    assert HOOK._retained_export_git(ROOT, *arguments) == b"unchanged Git operation"


@pytest.mark.parametrize(
    "failure", ["unmapped", "nonancestor", "missing_storage", "bad_index"]
)
def test_missing_or_invalid_storage_custody_still_refuses(
    monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    calls = []

    def resolve(repository: Path, revision: str) -> str:
        assert repository == ROOT and revision == ORIGINAL
        if failure == "bad_index":
            raise ValueError("Pinned source retention index changed")
        return ORIGINAL if failure == "unmapped" else STORAGE

    def command(repository: Path, *args: str) -> bytes:
        assert repository == ROOT
        calls.append(args)
        raise subprocess.CalledProcessError(
            128 if failure == "missing_storage" else 1,
            ["git", *args],
        )

    monkeypatch.setattr(HOOK, "source_revision", resolve)
    monkeypatch.setattr(HOOK, "_git", command)
    with pytest.raises((ValueError, subprocess.CalledProcessError)):
        HOOK._retained_export_git(ROOT, "merge-base", "--is-ancestor", ORIGINAL, "HEAD")
    if failure == "bad_index":
        assert calls == []
    else:
        assert calls == [
            (
                "merge-base",
                "--is-ancestor",
                ORIGINAL if failure == "unmapped" else STORAGE,
                "HEAD",
            )
        ]


def test_current_deck_build_retains_its_recorded_epoch_and_source_custody() -> None:
    path = ROOT / HOOK.MANIFEST
    before = path.read_bytes()
    build = json.loads(before)["deck_build"]
    revision = build["source_revision"]
    assert (
        HOOK._retained_export_git(ROOT, "merge-base", "--is-ancestor", revision, "HEAD")
        == b""
    )
    assert (
        int(HOOK._retained_export_git(ROOT, "show", "-s", "--format=%ct", revision))
        == build["source_date_epoch"]
    )
    evidence = HOOK.retained_deck_sources(ROOT)
    assert evidence["context"] == build
    assert [row["path"] for row in evidence["current_inputs"]] == build["inputs"]
    assert path.read_bytes() == before
