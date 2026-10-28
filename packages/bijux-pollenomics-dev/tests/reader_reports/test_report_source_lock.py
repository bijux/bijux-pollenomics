"""Separate maintained source editing from scientific evidence integrity."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[4]


@pytest.fixture
def verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "report_source_lock", ROOT / "reports/verify.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def lock(tmp_path: Path, verifier: ModuleType) -> dict[str, Any]:
    maintained = [
        "docs/report/numerical-performance/README.md",
        "packages/bijux-pollenomics/src/algorithm.py",
        "reports/science/account.md",
    ]
    evidence = [
        "data/source/raw.bin",
        "reports/exports/papers/account.pdf",
        *[
            f"docs/report/{family}/result.json"
            for family in verifier.REPORT_SOURCE_FAMILIES
        ],
    ]
    sources = {}
    for relative in [*maintained, *evidence]:
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"Source bytes for {relative}\n")
        if relative in evidence:
            sources[relative] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema_version": "research-report-source-lock.v2",
        "maintained_paths": maintained,
        "reports": ["reports/science/account.md"],
        "sources": sources,
    }


def test_editorial_and_code_edits_preserve_catalog(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any]
) -> None:
    expected = (len(lock["sources"]), len(lock["maintained_paths"]))
    assert verifier.verify_source_lock(tmp_path, lock) == expected
    for relative in lock["maintained_paths"]:
        path = tmp_path / relative
        path.write_bytes(path.read_bytes() + b"Changed maintained prose or code.\n")
    assert verifier.verify_source_lock(tmp_path, lock) == expected


@pytest.mark.parametrize(
    "relative",
    [
        "data/source/raw.bin",
        "docs/report/numerical-performance/result.json",
        "reports/exports/papers/account.pdf",
    ],
)
def test_scientific_raw_and_distributed_bytes_remain_authenticated(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], relative: str
) -> None:
    (tmp_path / relative).write_bytes(b"Substituted evidence\n")
    with pytest.raises(ValueError, match="changed research evidence"):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize("inventory", ["sources", "maintained_paths"])
@pytest.mark.parametrize("defect", ["missing", "escape", "absolute", "symlink"])
def test_source_paths_must_exist_and_stay_confined(
    tmp_path: Path,
    verifier: ModuleType,
    lock: dict[str, Any],
    inventory: str,
    defect: str,
) -> None:
    relative = (
        next(iter(lock[inventory])) if inventory == "sources" else lock[inventory][0]
    )
    path = tmp_path / relative
    replacement = relative
    if defect == "missing":
        path.unlink()
    elif defect == "symlink":
        outside = tmp_path.parent / f"{tmp_path.name}-outside"
        outside.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(outside)
    elif defect == "escape":
        replacement = "../outside.md"
    else:
        replacement = str(path)
    if inventory == "sources":
        lock[inventory][replacement] = lock[inventory].pop(relative)
    else:
        lock[inventory] = sorted(
            replacement if item == relative else item for item in lock[inventory]
        )
    with pytest.raises(ValueError, match="unavailable or unsafe"):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize(
    "defect",
    ["maintained_duplicate", "report_duplicate", "overlap", "digest", "schema"],
)
def test_catalog_refuses_ambiguous_or_malformed_roles(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], defect: str
) -> None:
    if defect == "maintained_duplicate":
        lock["maintained_paths"].append(lock["maintained_paths"][-1])
    elif defect == "report_duplicate":
        lock["reports"].append(lock["reports"][0])
    elif defect == "overlap":
        relative = lock["maintained_paths"][0]
        lock["sources"][relative] = hashlib.sha256(
            (tmp_path / relative).read_bytes()
        ).hexdigest()
    elif defect == "digest":
        lock["sources"][next(iter(lock["sources"]))] = "unbound"
    else:
        lock["schema_version"] = "research-report-source-lock.v1"
    with pytest.raises(ValueError):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize(
    "relative",
    [
        "data/source/account.md",
        "docs/report/reference/original.py",
        "reports/science/result.json",
    ],
)
def test_evidence_cannot_be_relabelled_as_maintained_prose_or_code(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("Evidence cannot become ordinary maintained code or prose\n")
    lock["maintained_paths"] = sorted([*lock["maintained_paths"], relative])
    with pytest.raises(ValueError, match="not maintained prose or code"):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize(
    "defect", ["unowned_family_file", "missing_family_member", "new_report"]
)
def test_family_and_report_populations_remain_exact(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], defect: str
) -> None:
    if defect == "unowned_family_file":
        (tmp_path / "docs/report/numerical-performance/unowned.json").write_text("{}")
    elif defect == "missing_family_member":
        del lock["sources"]["docs/report/numerical-performance/result.json"]
    else:
        (tmp_path / "reports/science/new-account.md").write_text("New report")
    with pytest.raises(ValueError, match="ownership changed|inventory changed"):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize(
    "relative",
    [
        ".github/workflows/scientific-verification.yml",
        "mkdocs.yml",
        "packages/bijux-pollenomics-dev/pyproject.toml",
        "packages/bijux-pollenomics-lra/pyproject.toml",
        "presentation/source-lock.json",
        "pyproject.toml",
        "reports/exports/site-downloads.json",
        "uv.lock",
    ],
)
def test_current_repository_bookkeeping_keeps_exact_paths_without_body_pins(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Current repository bookkeeping")
    lock["maintained_paths"] = sorted([*lock["maintained_paths"], relative])
    before = verifier.verify_source_lock(tmp_path, lock)
    path.write_bytes(b"Changed ordinary current bookkeeping")
    assert verifier.verify_source_lock(tmp_path, lock) == before


@pytest.mark.parametrize(
    "relative",
    [".github/workflows/other.yml", "other.toml", "configs/ci/report-ownership.json"],
)
def test_unlisted_metadata_and_scientific_ownership_cannot_be_unpinned(
    tmp_path: Path, verifier: ModuleType, lock: dict[str, Any], relative: str
) -> None:
    path = tmp_path / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"Unlisted metadata or scientific custody")
    lock["maintained_paths"] = sorted([*lock["maintained_paths"], relative])
    with pytest.raises(ValueError):
        verifier.verify_source_lock(tmp_path, lock)


@pytest.mark.parametrize("suffix", ["py", "json", "yaml", "md"])
def test_registered_atlas_sources_use_authenticated_transport(
    tmp_path: Path, verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, suffix: str
) -> None:
    relative = "data/atlas/source-view-capture/source/configs/own-source." + suffix
    body = b"Own synthetic authenticated source\n"
    calls: list[tuple[Path, str]] = []

    def retained(root: Path, path: str) -> bytes:
        calls.append((root, path))
        return body

    monkeypatch.setattr(verifier, "read_source_path", retained)
    assert verifier._source_bytes(tmp_path, relative) == body
    assert calls == [(tmp_path, relative)]


@pytest.mark.parametrize(
    "member", ["../escape.py", "nested/../../escape.json", "nested\\escape.yaml"]
)
def test_malformed_atlas_members_refuse_before_transport(
    tmp_path: Path, verifier: ModuleType, monkeypatch: pytest.MonkeyPatch, member: str
) -> None:
    def forbidden(root: Path, path: str) -> bytes:
        pytest.fail("Malformed source must not reach retained transport")

    monkeypatch.setattr(verifier, "read_source_path", forbidden)
    with pytest.raises(ValueError, match="unavailable or unsafe"):
        verifier._source_bytes(
            tmp_path, "data/atlas/source-view-capture/source/" + member
        )


def test_missing_atlas_member_keeps_transport_refusal(
    tmp_path: Path, verifier: ModuleType, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing(root: Path, path: str) -> bytes:
        raise verifier.ReportRebuildError("Unknown retained source member")

    monkeypatch.setattr(verifier, "read_source_path", missing)
    with pytest.raises(ValueError, match="unavailable or unsafe"):
        verifier._source_bytes(
            tmp_path, "data/atlas/source-view-capture/source/unknown.json"
        )
