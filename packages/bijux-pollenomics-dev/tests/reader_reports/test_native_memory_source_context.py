"""Preserve historical memory observations while qualifying one security comment."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[4]
REPORT = "docs/report/numerical-performance/native-memory/report.json"
CONTEXT = "docs/report/numerical-performance/native-memory/source-context.json"
HISTORICAL = (
    "docs/report/numerical-performance/native-memory/retained-trusted-process.txt"
)
HELPER = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/trusted_process.py"


@pytest.fixture
def verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "native_memory_source_context", ROOT / "reports/verify.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    """Copy only the exact small retained readset, without Git or native binaries."""
    root = tmp_path / "repository"
    report = json.loads((ROOT / REPORT).read_bytes())
    for relative in [REPORT, CONTEXT, HISTORICAL, *report["source_sha256"]]:
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes((ROOT / relative).read_bytes())
    return root


def test_exact_security_comment_context_preserves_saved_measurements(
    verifier: ModuleType, source_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = {
        path.relative_to(source_root).as_posix(): path.read_bytes()
        for path in source_root.rglob("*")
        if path.is_file()
    }
    monkeypatch.setattr(verifier, "ROOT", source_root)
    monkeypatch.setattr(verifier, "NATIVE_MEMORY", source_root / Path(REPORT).parent)
    verifier.verify_native_memory()
    assert not (source_root / ".git").exists()
    assert before == {
        path.relative_to(source_root).as_posix(): path.read_bytes()
        for path in source_root.rglob("*")
        if path.is_file()
    }
    report = json.loads(before[REPORT])
    assert len(report["source_sha256"]) == 5
    assert report["source_sha256"][HELPER] != hashlib.sha256(before[HELPER]).hexdigest()
    assert (
        report["source_sha256"][HELPER]
        == hashlib.sha256(before[HISTORICAL]).hexdigest()
    )


@pytest.mark.parametrize("defect", ["measurement", "historical_source_repin"])
def test_historical_timing_or_source_repin_refused(
    verifier: ModuleType, source_root: Path, defect: str
) -> None:
    report = json.loads((source_root / REPORT).read_bytes())
    if defect == "measurement":
        report["cases"][0]["observations"]["native"][0]["single_call_seconds"] += 0.01
    else:
        report["source_sha256"][HELPER] = hashlib.sha256(
            (source_root / HELPER).read_bytes()
        ).hexdigest()
    with pytest.raises(ValueError, match="historical measurement"):
        verifier.verify_native_memory_sources(source_root, json.dumps(report).encode())


@pytest.mark.parametrize(
    "defect", ["missing", "unknown", "revision", "current_hash", "duplicate"]
)
def test_unreviewed_source_context_refused(
    verifier: ModuleType, source_root: Path, defect: str
) -> None:
    path = source_root / CONTEXT
    context = json.loads(path.read_bytes())
    if defect == "missing":
        path.unlink()
    elif defect == "duplicate":
        path.write_bytes(b'{"schema_version":"substituted",' + path.read_bytes()[1:])
    else:
        if defect == "unknown":
            context["unreviewed"] = True
        elif defect == "revision":
            context["security_comment_delta"]["revision"] = "0" * 40
        else:
            context["security_comment_delta"]["current_sha256"] = "0" * 64
        path.write_text(json.dumps(context))
    with pytest.raises(ValueError):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


@pytest.mark.parametrize("target", [HELPER, HISTORICAL])
def test_helper_source_substitution_refused(
    verifier: ModuleType, source_root: Path, target: str
) -> None:
    path = source_root / target
    path.write_bytes(path.read_bytes() + b"# Unreviewed source substitution\n")
    with pytest.raises(ValueError, match="helper source identity"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


@pytest.mark.parametrize(
    "name",
    ["memory_compare.py", "forward_compare.py", "forward_kernel.cpp", "profiling.py"],
)
def test_other_measured_source_cannot_change(
    verifier: ModuleType, source_root: Path, name: str
) -> None:
    relative = (
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/native_backend/"
        + name
    )
    path = source_root / relative
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="outside security comment"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


@pytest.mark.parametrize(
    "defect",
    [
        "extra_comment",
        "whitespace",
        "runtime",
        "different_suppression",
        "duplicate_original",
    ],
)
def test_only_exact_raw_comment_delta_is_allowed(
    verifier: ModuleType, defect: str
) -> None:
    original = (ROOT / HISTORICAL).read_bytes()
    current = (ROOT / HELPER).read_bytes()
    verifier._native_memory_helper_delta(original, current)
    if defect == "extra_comment":
        current += b"# Another runtime-neutral comment\n"
    elif defect == "whitespace":
        current = current.replace(b"import subprocess\n", b"import subprocess  \n")
    elif defect == "runtime":
        current += b"raise RuntimeError('unreviewed')\n"
    elif defect == "different_suppression":
        current = current.replace(
            b"import subprocess\n", b"import subprocess  # nosec B311\n"
        )
    else:
        original += b"import subprocess  # nosec B404\n"
    with pytest.raises(ValueError, match="exact comment"):
        verifier._native_memory_helper_delta(original, current)


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
def test_unsafe_source_path_refused(
    verifier: ModuleType, source_root: Path, relative: str
) -> None:
    with pytest.raises(ValueError, match="not canonical"):
        verifier._native_memory_source(source_root, relative)


@pytest.mark.parametrize("relative", [CONTEXT, HISTORICAL, HELPER])
def test_symlinked_source_member_refused(
    verifier: ModuleType, source_root: Path, relative: str
) -> None:
    path = source_root / relative
    destination = path.with_name(path.name + ".saved")
    path.rename(destination)
    path.symlink_to(destination)
    with pytest.raises(ValueError, match="linked or nonregular"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


def test_hardlinked_source_refused(verifier: ModuleType, source_root: Path) -> None:
    path = source_root / HELPER
    os.link(path, path.with_name("linked-source.py"))
    with pytest.raises(ValueError, match="linked or nonregular"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


def test_linked_source_ancestor_refused(
    verifier: ModuleType, source_root: Path
) -> None:
    parent = source_root / "packages"
    saved = source_root / "source-packages"
    parent.rename(saved)
    parent.symlink_to(saved, target_is_directory=True)
    with pytest.raises(ValueError, match="linked or nonregular"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )


def test_nonregular_source_member_refused(
    verifier: ModuleType, source_root: Path
) -> None:
    source = source_root / HELPER
    source.unlink()
    source.mkdir()
    with pytest.raises(ValueError, match="linked or nonregular"):
        verifier.verify_native_memory_sources(
            source_root, (source_root / REPORT).read_bytes()
        )
