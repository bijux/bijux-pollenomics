"""Historical displays keep raw authority without qualifying a newer renderer."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    atlas_source_views as historical,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as current,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.presentation_source_roles import (
    HISTORICAL_RENDERING_SOURCES,
)

from .test_atlas_source_capture import _STATES
from .test_atlas_source_capture import packet as packet


def test_rendering_roles_are_shared_explicit_six_path_boundaries() -> None:
    assert (
        vars(historical)["HISTORICAL_RENDERING_SOURCES"] is HISTORICAL_RENDERING_SOURCES
    )
    assert vars(current)["HISTORICAL_RENDERING_SOURCES"] is HISTORICAL_RENDERING_SOURCES
    assert len(HISTORICAL_RENDERING_SOURCES) == 6
    assert (
        not HISTORICAL_RENDERING_SOURCES & historical.HISTORICAL_PORTAL_READER_SOURCES
    )
    assert not HISTORICAL_RENDERING_SOURCES & set(
        current.DOCUMENTED_CAPTURE_DEFINITIONS
    )


def test_new_rendering_is_not_relabelled_as_the_captured_browser_epoch(
    packet: tuple[Path, Path, dict[str, Any]],
) -> None:
    root, _, document = packet
    original = (root / historical.CAPTURE_PATH).read_bytes()
    for name in HISTORICAL_RENDERING_SOURCES:
        (root / name).write_bytes(b"new current display implementation\n")
    checked = historical.validated_atlas_source_views(root)
    assert checked.document == document
    assert checked.document["source_candidate"] == historical.SOURCE_CANDIDATE
    assert checked.document["scientific_admission"] is False
    assert checked.document["numerical_execution"] is False
    assert (root / historical.CAPTURE_PATH).read_bytes() == original


@pytest.mark.parametrize("name", sorted(HISTORICAL_RENDERING_SOURCES))
def test_display_witness_git_bytes_are_still_authenticated(
    packet: tuple[Path, Path, dict[str, Any]], name: str
) -> None:
    root, _, _ = packet
    _STATES[root].bodies[name] = b"tampered historical display witness\n"
    with pytest.raises((ReportRebuildError, ValueError)):
        historical.validated_atlas_source_views(root)


@pytest.mark.parametrize("name", sorted(HISTORICAL_RENDERING_SOURCES))
@pytest.mark.parametrize(
    "defect",
    [
        "missing",
        "directory",
        "symlink",
        "hardlink",
        "wrong_logical",
        "runtime_role",
        "not_detached",
        "captured_hash",
    ],
)
def test_current_profile_refuses_display_custody_defects(
    tmp_path: Path, name: str, defect: str
) -> None:
    raw = b"original browser display source\n"
    expected = hashlib.sha256(raw).hexdigest()
    logical = "source/" + name
    detached = frozenset({logical})
    target = tmp_path / name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"new current display implementation\n")
    if defect == "missing":
        target.unlink()
    elif defect == "directory":
        target.unlink()
        target.mkdir()
    elif defect in {"symlink", "hardlink"}:
        other = tmp_path / "own-display-reference"
        other.write_bytes(target.read_bytes())
        target.unlink()
        if defect == "symlink":
            target.symlink_to(other)
        else:
            target.hardlink_to(other)
    elif defect == "wrong_logical":
        logical += ".other"
        detached = frozenset({logical})
    elif defect == "runtime_role":
        logical = "runtime/" + name
        detached = frozenset({logical})
    elif defect == "not_detached":
        detached = frozenset()
    elif defect == "captured_hash":
        expected = "0" * 64
    with pytest.raises((ReportRebuildError, ValueError)):
        current._validate_current_source(
            tmp_path, name, logical, raw, expected, detached
        )


@pytest.mark.parametrize("name", sorted(HISTORICAL_RENDERING_SOURCES))
def test_current_profile_authenticates_own_historical_display_role(
    tmp_path: Path, name: str
) -> None:
    raw = b"original browser display source\n"
    target = tmp_path / name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"separately maintained current renderer\n")
    logical = "source/" + name
    current._validate_current_source(
        tmp_path,
        name,
        logical,
        raw,
        hashlib.sha256(raw).hexdigest(),
        frozenset({logical}),
    )


@pytest.mark.parametrize(
    "name",
    [
        "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/unlisted.py",
        "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra_validation/spatial/model.py",
    ],
)
def test_other_executable_sources_cannot_borrow_a_display_role(
    tmp_path: Path, name: str
) -> None:
    raw = b"unchanged scientific implementation\n"
    target = tmp_path / name
    target.parent.mkdir(parents=True)
    target.write_bytes(b"unauthorized changed scientific implementation\n")
    logical = "source/" + name
    with pytest.raises(ReportRebuildError, match="source footprint differs"):
        current._validate_current_source(
            tmp_path,
            name,
            logical,
            raw,
            hashlib.sha256(raw).hexdigest(),
            frozenset({logical}),
        )
