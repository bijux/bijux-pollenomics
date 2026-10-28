"""Keep exact source-comment custody separate from historical memory measurements."""

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]


def verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "native_memory_custody", ROOT / "reports/verify.py"
    )
    assert spec is not None and spec.loader is not None
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def fixture(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ModuleType, bytes, dict[str, Any], dict[str, Any]]:
    api = verifier()
    prefix = b"import subprocess  # nosec B404\n"
    original = prefix + b"#" + b"x" * (1887 - len(prefix) - 2) + b"\n"
    current = original.replace(prefix, b"import subprocess\n")
    source_names = [
        "package/helper.py",
        "package/compare.py",
        "package/kernel.cpp",
        "package/profile.py",
        "package/worker.py",
    ]
    sources = {
        name: (current if i == 0 else b"fixture source\n")
        for i, name in enumerate(source_names)
    }
    old_hash = hashlib.sha256(original).hexdigest()
    historical = {
        name: (old_hash if i == 0 else hashlib.sha256(sources[name]).hexdigest())
        for i, name in enumerate(source_names)
    }
    payload = json.dumps({"source_sha256": historical}).encode()
    context = {
        "measurement": {"sha256": hashlib.sha256(payload).hexdigest()},
        "historical_sources": historical,
        "security_comment_delta": {
            "path": source_names[0],
            "historical_source_path": "retired/source.txt",
            "historical_git_blob": hashlib.sha1(
                b"blob 1887\0" + original, usedforsecurity=False
            ).hexdigest(),
            "historical_sha256": old_hash,
            "current_sha256": hashlib.sha256(current).hexdigest(),
        },
    }
    raw = json.dumps(context).encode()
    for path, value in sources.items():
        file = root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(value)
    file = root / api.NATIVE_MEMORY_SOURCE_CONTEXT_PATH
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(raw)
    monkeypatch.setattr(api, "NATIVE_MEMORY_SOURCE_CONTEXT", copy.deepcopy(context))
    monkeypatch.setattr(
        api, "NATIVE_MEMORY_SOURCE_CONTEXT_SHA256", hashlib.sha256(raw).hexdigest()
    )
    calls = []

    def recorded(repository: Path, member: object) -> bytes:
        calls.append((repository, member))
        return original

    monkeypatch.setattr(api, "read_historical_python_correspondence", recorded)
    return api, payload, context, {"original": original, "calls": calls}


def test_guard_uses_original_git_source_without_physical_code_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    api, payload, context, observed = fixture(tmp_path, monkeypatch)
    api.verify_native_memory_sources(tmp_path, payload)
    assert not (
        tmp_path / context["security_comment_delta"]["historical_source_path"]
    ).exists()
    assert len(observed["calls"]) == 1
    _, member = observed["calls"][0]
    assert member.repository_path == context["security_comment_delta"]["path"]
    assert member.bytes == 1887
    assert member.source_revision == "ae4e0a08ba6ae379e0ebaac41bf3147cf017c023"


@pytest.mark.parametrize(
    "damage", ["measurement", "context", "helper", "other_source", "wrong_original"]
)
def test_exact_context_measurement_and_every_source_remain_guarded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    api, payload, context, _ = fixture(tmp_path, monkeypatch)
    if damage == "measurement":
        payload += b" "
    elif damage == "context":
        with (tmp_path / api.NATIVE_MEMORY_SOURCE_CONTEXT_PATH).open("ab") as stream:
            stream.write(b" ")
    elif damage in {"helper", "other_source"}:
        relative = (
            context["security_comment_delta"]["path"]
            if damage == "helper"
            else "package/compare.py"
        )
        with (tmp_path / relative).open("ab") as stream:
            stream.write(b" ")
    else:
        monkeypatch.setattr(
            api,
            "read_historical_python_correspondence",
            lambda *_args: b"wrong historical source",
        )
    with pytest.raises(ValueError):
        api.verify_native_memory_sources(tmp_path, payload)


@pytest.mark.parametrize(
    "damage",
    [
        "extra_comment",
        "whitespace",
        "runtime",
        "different_suppression",
        "duplicate_original",
    ],
)
def test_exact_single_comment_delta_is_not_general_ast_equivalence(damage: str) -> None:
    api = verifier()
    original = b"import subprocess  # nosec B404\n"
    current = b"import subprocess\n"
    api._native_memory_helper_delta(original, current)
    if damage == "extra_comment":
        current += b"# another comment\n"
    elif damage == "whitespace":
        current = b"import subprocess  \n"
    elif damage == "runtime":
        current += b"raise RuntimeError('changed')\n"
    elif damage == "different_suppression":
        current = b"import subprocess  # nosec B311\n"
    else:
        original += original
    with pytest.raises(ValueError, match="exact comment"):
        api._native_memory_helper_delta(original, current)


@pytest.mark.parametrize(
    "relative",
    [
        "../outside",
        "/absolute",
        "reports//alias",
        "reports/./alias",
        "reports\\alias",
        "reports/null\0",
    ],
)
def test_noncanonical_source_paths_refuse(tmp_path: Path, relative: str) -> None:
    with pytest.raises(ValueError, match="not canonical"):
        verifier()._native_memory_source(tmp_path, relative)


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "directory"])
def test_nonregular_sources_refuse_without_real_source_fixtures(
    tmp_path: Path, kind: str
) -> None:
    source = tmp_path / "source.py"
    source.write_bytes(b"synthetic")
    if kind == "symlink":
        source.rename(tmp_path / "original.py")
        source.symlink_to(tmp_path / "original.py")
    elif kind == "hardlink":
        (tmp_path / "alias.py").hardlink_to(source)
    else:
        source.unlink()
        source.mkdir()
    with pytest.raises(ValueError, match="linked or nonregular"):
        verifier()._native_memory_source(tmp_path, "source.py")
