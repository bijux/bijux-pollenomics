"""Counting exports preserve exact original API bytes within named capture roles."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    linux_r_reference as linux,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as chronology,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as source,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid import (
    admission as author_grid,
)
from bijux_pollenomics_dev.lra_validation.native_reference import (
    source_layout_adoption as layout,
)


@dataclass
class OwnCapsule:
    """Expose only the byte, member and freshness seams used by the guard."""

    repository: Path
    prefix: str
    descriptor: SimpleNamespace
    detached: frozenset[str]
    logical: str
    captured: bytes
    stale: bool = False

    def fresh(self) -> None:
        """Reject a synthetic changed authority before correspondence completes."""
        if self.stale:
            raise ReportRebuildError("own capsule changed")

    def read_source(self, logical: str) -> bytes:
        """Return the one own byte string through its declared member only."""
        assert logical in self.descriptor.members
        return self.captured


def own_case(
    root: Path,
    monkeypatch: pytest.MonkeyPatch,
    prefix: str,
    name: str = layout.API_PATH,
) -> tuple[dict[str, object], str, OwnCapsule]:
    """Construct a tiny API and its explicit synthetic historical identity."""
    root.mkdir(exist_ok=True)
    old = b"def retained(value=17):\n    return value\n"
    insertion = b"ADDED_COUNTING_EXPORT = True\n"
    monkeypatch.setattr(
        layout, "_FIXED_BACKGROUND_COUNTING_SPANS", {name: (insertion,)}
    )
    identity = {"sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old)}
    monkeypatch.setattr(
        source,
        "_COUNTING_API_IDENTITIES",
        {name: (identity["sha256"], identity["bytes"])},
    )
    if prefix in source._COUNTING_API_CAPTURE_BINDINGS:
        checksum, member_prefix = source._COUNTING_API_CAPTURE_BINDINGS[prefix]
        aliases = {member_prefix + name}
    else:
        checksum, lanes = source._COUNTING_API_AUTHOR_BINDINGS[prefix]
        aliases = {
            "executions/" + lane + "/first-party-inputs/" + name for lane in lanes
        }
        member_prefix = "executions/" + lanes[0] + "/first-party-inputs/"
    logical = member_prefix + name
    target = root / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(old + insertion)
    capsule = OwnCapsule(
        root,
        prefix,
        SimpleNamespace(
            capture={"sha256": checksum},
            members={member: dict(identity) for member in aliases},
            groups=[{"resolved_paths": [(member, name) for member in sorted(aliases)]}],
        ),
        frozenset(aliases),
        logical,
        old,
    )
    return {"path": name, **identity}, logical, capsule


@pytest.mark.parametrize(
    "prefix",
    [*source._COUNTING_API_CAPTURE_BINDINGS, *source._COUNTING_API_AUTHOR_BINDINGS],
)
@pytest.mark.parametrize("name", [layout.API_PATH, layout.ROOT_API_PATH])
def test_only_named_captures_admit_exact_counting_additions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> None:
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix, name)
    role = source.validated_current_scientific_source(
        capsule.repository, row, logical, cast(SourceCapsule, capsule)
    )
    assert role is not None
    assert role["classification"] == "finite_counting_api_addition"
    assert role["historical"] == {"sha256": row["sha256"], "bytes": row["bytes"]}
    assert role["whole_current_descriptor_equal_old_claimed"] is False
    assert role["native_execution_or_browser_equivalence_claimed"] is False
    assert role["new_counting_api_requires_separate_current_qualification"] is True


@pytest.mark.parametrize(
    "fault",
    [
        "capture",
        "prefix",
        "repository",
        "logical",
        "physical_member",
        "catalogue",
        "mapping",
        "duplicate_mapping",
        "old_sha",
        "old_size",
        "boolean_size",
        "extra_identity_field",
        "old_body",
        "unknown_path",
        "stale",
        "symlink",
        "ancestor_symlink",
        "hardlink",
        "oversized",
        "current_math",
        "current_comment",
        "current_import",
    ],
)
def test_counting_capture_binding_and_unrelated_source_changes_refuse(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, fault: str
) -> None:
    prefix = "data/method-certification/author-optimizer-diagnostic-source-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix)
    repository = capsule.repository
    target = repository / layout.API_PATH
    assert (
        source._counting_api_source_correspondence(
            repository, row, logical, cast(SourceCapsule, capsule)
        )["classification"]
        == "finite_counting_api_addition"
    )
    if fault == "capture":
        capsule.descriptor.capture["sha256"] = "0" * 64
    elif fault == "prefix":
        capsule.prefix += "-other"
    elif fault == "repository":
        capsule.repository = tmp_path
    elif fault == "logical":
        logical = "different/" + layout.API_PATH
    elif fault == "physical_member":
        capsule.detached = frozenset()
    elif fault == "catalogue":
        capsule.descriptor.members[logical] = {
            "sha256": "0" * 64,
            "bytes": row["bytes"],
        }
    elif fault == "mapping":
        capsule.descriptor.groups = [{"resolved_paths": [(logical, "wrong/source.py")]}]
    elif fault == "duplicate_mapping":
        capsule.descriptor.groups *= 2
    elif fault == "old_sha":
        row["sha256"] = "0" * 64
    elif fault == "old_size":
        row["bytes"] = 1
    elif fault == "boolean_size":
        row["bytes"] = True
    elif fault == "extra_identity_field":
        row["unknown"] = 1
    elif fault == "old_body":
        capsule.captured += b"# changed old body\n"
    elif fault == "unknown_path":
        row["path"] = "packages/unreviewed_math.py"
    elif fault == "stale":
        capsule.stale = True
    elif fault == "symlink":
        backing = repository / "own_backing.py"
        target.rename(backing)
        target.symlink_to(backing)
    elif fault == "ancestor_symlink":
        backing = repository / "own_package"
        target.parent.rename(backing)
        target.parent.symlink_to(backing, target_is_directory=True)
    elif fault == "hardlink":
        os.link(target, repository / "own_link.py")
    elif fault == "oversized":
        target.write_bytes(b"#" * 32769)
    elif fault == "current_math":
        target.write_bytes(
            target.read_bytes().replace(b"return value", b"return value + 1")
        )
    elif fault == "current_comment":
        target.write_bytes(target.read_bytes() + b"# unrelated source edit\n")
    else:
        target.write_bytes(target.read_bytes() + b"import unreviewed\n")
    expected = (
        ReportOwnershipError
        if fault in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        source._counting_api_source_correspondence(
            repository, row, logical, cast(SourceCapsule, capsule)
        )


def test_counting_counterpart_change_during_read_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prefix = "data/method-certification/author-optimizer-diagnostic-source-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix)
    repository = capsule.repository
    target = repository / layout.API_PATH
    assert (
        source._counting_api_source_correspondence(
            repository, row, logical, cast(SourceCapsule, capsule)
        )["classification"]
        == "finite_counting_api_addition"
    )
    original_read = Path.read_bytes
    changed = False

    def changing(path: Path) -> bytes:
        nonlocal changed
        raw = original_read(path)
        if path == target and not changed:
            changed = True
            path.write_bytes(raw + b"# concurrent change\n")
        return raw

    monkeypatch.setattr(Path, "read_bytes", changing)
    with pytest.raises(ReportRebuildError, match="changed during"):
        source._counting_api_source_correspondence(
            repository, row, logical, cast(SourceCapsule, capsule)
        )


def test_linux_dispatch_uses_only_its_exact_counting_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prefix = "data/method-certification/linux-r-source-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix)
    role = linux._require_scientific_projection(
        capsule.repository,
        layout.API_PATH,
        row,
        capsule.captured,
        source_buffer=cast(SourceCapsule, capsule),
    )
    assert role is not None and role["classification"] == "finite_counting_api_addition"
    capsule.descriptor.capture["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError, match="capture binding"):
        linux._require_scientific_projection(
            capsule.repository,
            layout.API_PATH,
            row,
            capsule.captured,
            source_buffer=cast(SourceCapsule, capsule),
        )


def test_chronology_dispatch_keeps_its_original_source_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prefix = "data/atlas/sample-chronology-source-view-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix)
    chronology._validate_current_source(
        capsule.repository,
        layout.API_PATH,
        logical,
        capsule.captured,
        str(row["sha256"]),
        capsule.detached,
        source_buffer=cast(SourceCapsule, capsule),
    )
    with pytest.raises(ReportRebuildError, match="captured source bytes"):
        chronology._validate_current_source(
            capsule.repository,
            layout.API_PATH,
            logical,
            capsule.captured + b"# changed\n",
            str(row["sha256"]),
            capsule.detached,
            source_buffer=cast(SourceCapsule, capsule),
        )


@pytest.mark.parametrize("name", [layout.API_PATH, layout.ROOT_API_PATH])
@pytest.mark.parametrize(
    "fault",
    ["missing_alias", "alias_identity", "alias_mapping", "wrong_lane", "alias_bytes"],
)
def test_author_api_all_original_lane_aliases_remain_exact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, fault: str
) -> None:
    prefix = "data/method-certification/author-site-evaluation-source-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix, name)
    assert source._counting_api_source_correspondence(
        capsule.repository, row, logical, cast(SourceCapsule, capsule)
    )["original_aliases"] == sorted(capsule.detached)
    other = next(member for member in sorted(capsule.detached) if member != logical)
    if fault == "missing_alias":
        capsule.detached = capsule.detached - {other}
    elif fault == "alias_identity":
        capsule.descriptor.members[other] = {"bytes": 1, "sha256": "0" * 64}
    elif fault == "alias_mapping":
        capsule.descriptor.groups[0]["resolved_paths"] = [
            (member, "wrong.py" if member == other else path)
            for member, path in capsule.descriptor.groups[0]["resolved_paths"]
        ]
    elif fault == "wrong_lane":
        logical = "executions/other/first-party-inputs/" + name
    else:
        read_source = capsule.read_source
        monkeypatch.setattr(
            capsule,
            "read_source",
            lambda member: (
                read_source(member)
                + (b"# changed old alias" if member == other else b"")
            ),
        )
    with pytest.raises(ReportRebuildError, match="author counting API"):
        source._counting_api_source_correspondence(
            capsule.repository, row, logical, cast(SourceCapsule, capsule)
        )


@pytest.mark.parametrize("name", [layout.API_PATH, layout.ROOT_API_PATH])
def test_author_grid_dispatch_uses_the_existing_exact_counting_law(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Keep original grid source bytes while qualifying only named API exports."""
    prefix = "data/publication-replay/landclim-author-example-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix, name)
    projected = {**row, "captured_path": logical}
    role = author_grid._current_numerical_source_role(
        capsule.repository,
        projected,
        capsule.descriptor.members,
        cast(SourceCapsule, capsule),
    )
    assert role is not None and role["classification"] == "finite_counting_api_addition"
    assert role["original_member"] == "numerical-source/" + name
    assert role["old_noninserted_bytes_and_bindings_exact"] is True
    assert role["native_execution_or_browser_equivalence_claimed"] is False


@pytest.mark.parametrize("name", [layout.API_PATH, layout.ROOT_API_PATH])
@pytest.mark.parametrize(
    "fault",
    [
        "capture",
        "prefix",
        "logical",
        "detached",
        "member",
        "mapping",
        "old_body",
        "current_math",
        "current_comment",
        "hardlink",
        "stale",
    ],
)
def test_author_grid_api_binding_or_unclassified_source_drift_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, fault: str
) -> None:
    """Every invalid grid binding starts from the real successful guarded route."""
    prefix = "data/publication-replay/landclim-author-example-capture"
    row, logical, capsule = own_case(tmp_path / "repository", monkeypatch, prefix, name)
    repository = capsule.repository
    projected = {**row, "captured_path": logical}
    members = {key: dict(value) for key, value in capsule.descriptor.members.items()}
    assert (
        author_grid._current_numerical_source_role(
            repository, projected, members, cast(SourceCapsule, capsule)
        )
        is not None
    )
    target = repository / name
    if fault == "capture":
        capsule.descriptor.capture["sha256"] = "0" * 64
    elif fault == "prefix":
        capsule.prefix += "-other"
    elif fault == "logical":
        projected["captured_path"] = "other/" + name
        members[str(projected["captured_path"])] = dict(members[logical])
        capsule.descriptor.members[str(projected["captured_path"])] = dict(
            members[logical]
        )
    elif fault == "detached":
        capsule.detached = frozenset()
    elif fault == "member":
        capsule.descriptor.members[logical] = {
            "sha256": "0" * 64,
            "bytes": row["bytes"],
        }
    elif fault == "mapping":
        capsule.descriptor.groups = [{"resolved_paths": [(logical, "wrong.py")]}]
    elif fault == "old_body":
        capsule.captured += b"# changed historical bytes\n"
    elif fault == "current_math":
        target.write_bytes(
            target.read_bytes().replace(b"return value", b"return value + 1")
        )
    elif fault == "current_comment":
        target.write_bytes(target.read_bytes() + b"# unclassified change\n")
    elif fault == "hardlink":
        os.link(target, repository / "own_extra_link.py")
    else:
        capsule.stale = True
    with pytest.raises(ReportRebuildError):
        author_grid._current_numerical_source_role(
            repository, projected, members, cast(SourceCapsule, capsule)
        )


def test_author_grid_other_numerical_sources_keep_raw_default_equality(
    tmp_path: Path,
) -> None:
    """An unrelated numerical source cannot borrow the named API certificate."""
    repository = tmp_path / "repository"
    name = "packages/own/numerical_source.py"
    logical = "numerical-source/" + name
    target = repository / name
    target.parent.mkdir(parents=True)
    old = b"# Own inert numerical source\n"
    target.write_bytes(old)
    identity = {"sha256": hashlib.sha256(old).hexdigest(), "bytes": len(old)}
    row = {"path": name, "captured_path": logical, **identity}
    capsule = cast(SourceCapsule, SimpleNamespace())
    assert (
        author_grid._current_numerical_source_role(
            repository, row, {logical: identity}, capsule
        )
        is None
    )
    target.write_bytes(old + b"# unrelated edit\n")
    with pytest.raises(ValueError, match="numerical source changed"):
        author_grid._current_numerical_source_role(
            repository, row, {logical: identity}, capsule
        )
