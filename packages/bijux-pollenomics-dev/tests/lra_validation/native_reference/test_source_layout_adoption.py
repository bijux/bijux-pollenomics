"""Named operation/path custody never accepts unrelated source or API changes."""

from __future__ import annotations

from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.lra_validation.native_reference import (
    source_layout_adoption as layout,
)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    maintained = Path(__file__).resolve().parents[5]
    root = tmp_path / "repository"
    paths = [
        layout.PROOF_PATH,
        layout.PREIMAGE_PATH,
        layout.API_PATH,
        layout.ROOT_API_PATH,
        *layout.RELOCATIONS.values(),
        "configs/ci/report-capture-projections/atlas-source-view-api.json",
        "configs/ci/report-capture-projections/atlas-source-view-root-api.json",
        "data/atlas/source-view-capture/source/" + layout.API_PATH,
        "data/atlas/source-view-capture/source/" + layout.ROOT_API_PATH,
    ]
    for name in paths:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(maintained / name, target)
    return root


def test_exact_named_layout_retains_original_api_preimage(repository: Path) -> None:
    proof = layout.validated_source_layout(repository)
    assert proof["native_R_executed"] is False
    assert proof["scientific_admission"] is False
    assert (
        layout.api_adoption_preimage(repository, repository / layout.API_PATH)
        == repository / layout.PREIMAGE_PATH
    )


@pytest.mark.parametrize("name", list(layout.RELOCATIONS))
def test_changed_operation_bytes_refuse(repository: Path, name: str) -> None:
    target = repository / layout.RELOCATIONS[name]
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ReportRebuildError, match="operation source bytes"):
        layout.validated_source_layout(repository)


def test_duplicate_old_operation_owner_refuses(repository: Path) -> None:
    before, after = next(iter(layout.RELOCATIONS.items()))
    target = repository / before
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((repository / after).read_bytes())
    with pytest.raises(ReportRebuildError, match="old operation path"):
        layout.validated_source_layout(repository)


@pytest.mark.parametrize(
    "name", [layout.PROOF_PATH, layout.PREIMAGE_PATH, layout.API_PATH]
)
def test_changed_api_or_certificate_bytes_refuse(repository: Path, name: str) -> None:
    path = repository / name
    path.write_bytes(path.read_bytes() + b"\n")
    with pytest.raises(ReportRebuildError):
        layout.validated_source_layout(repository)


def test_exact_older_api_additions_remain_separate_from_layout(
    repository: Path,
) -> None:
    captured = repository / ("data/atlas/source-view-capture/source/" + layout.API_PATH)
    import hashlib

    layout.validate_current_native_source(
        repository, layout.API_PATH, hashlib.sha256(captured.read_bytes()).hexdigest()
    )
    captured_root = repository / (
        "data/atlas/source-view-capture/source/" + layout.ROOT_API_PATH
    )
    layout.validate_current_native_source(
        repository,
        layout.ROOT_API_PATH,
        hashlib.sha256(captured_root.read_bytes()).hexdigest(),
    )


def test_unchanged_import_ast_outside_named_moves_is_required() -> None:
    prefix = "\n".join("from " + name + " import X" for name in layout.MODULES)
    original = (prefix + "\ndef retained():\n return 1\n").encode()
    current = original
    for old, new in layout.MODULES.items():
        current = current.replace(old.encode(), new.encode())
    assert layout._imports_and_remaining(
        original, moved=False
    ) == layout._imports_and_remaining(current, moved=True)
    assert layout._imports_and_remaining(
        original, moved=False
    ) != layout._imports_and_remaining(
        current.replace(b"return 1", b"return 2"), moved=True
    )


def test_renamed_api_import_alias_is_not_accepted() -> None:
    current = "\n".join(
        "from " + name + " import X as Renamed" for name in layout.MODULES.values()
    )
    with pytest.raises(ReportRebuildError, match="alias differs"):
        layout._imports_and_remaining(current.encode(), moved=True)


@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_current_operation_file_alias_refuses(repository: Path, alias: str) -> None:
    import os

    target = repository / next(iter(layout.RELOCATIONS.values()))
    backing = repository / "backing.py"
    target.rename(backing)
    if alias == "symlink":
        target.symlink_to(backing)
    else:
        os.link(backing, target)
    expected_error = ReportOwnershipError if alias == "symlink" else ReportRebuildError
    with pytest.raises(expected_error):
        layout.validated_source_layout(repository)


@pytest.mark.parametrize("moved", [False, True])
def test_duplicate_named_import_is_refused(moved: bool) -> None:
    names = layout.MODULES.values() if moved else layout.MODULES
    statements = ["from " + name + " import X" for name in names]
    current = "\n".join([*statements, statements[0]])
    with pytest.raises(ReportRebuildError, match="duplicate"):
        layout._imports_and_remaining(current.encode(), moved=moved)
