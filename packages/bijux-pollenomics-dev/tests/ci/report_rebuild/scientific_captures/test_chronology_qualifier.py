"""Keep the chronology qualifier exception finite and source-bound."""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as source,
)

NAME = "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/__init__.py"
PREFIX = "data/atlas/sample-chronology-source-view-capture"
CAPTURE_SHA = "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62"


class _Resolver:
    def __init__(self, repository: Path, old: bytes) -> None:
        self.repository = repository
        self.prefix = PREFIX
        self.logical = "source/" + NAME
        self.detached = frozenset({self.logical})
        self.descriptor = SimpleNamespace(
            capture={"sha256": CAPTURE_SHA},
            members={
                self.logical: {
                    "sha256": hashlib.sha256(old).hexdigest(),
                    "bytes": len(old),
                }
            },
            groups=[{"resolved_paths": [(self.logical, NAME)]}],
        )
        self.fresh_calls = 0
        self.change_on: int | None = None
        self.path: Path | None = None

    def fresh(self) -> None:
        self.fresh_calls += 1
        if self.change_on == self.fresh_calls:
            assert self.path is not None
            self.path.write_bytes(self.path.read_bytes() + b"# concurrent\n")


@pytest.fixture
def admitted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, bytes, bytes, str, _Resolver, Path]:
    repository = tmp_path.resolve()
    old = b'import re\nPATTERNS = (re.compile(r"(?:^|\\s)cf\\.\\s", re.IGNORECASE),)\nSCOPE = "source labels"\n'
    current = old.replace(b"cf\\.\\s", b"cf\\.?\\s")
    checksum = hashlib.sha256(old).hexdigest()
    monkeypatch.setattr(source, "_NEOTOMA_QUALIFIER_IDENTITY", (checksum, len(old)))
    path = repository / NAME
    path.parent.mkdir(parents=True)
    path.write_bytes(current)
    return repository, old, current, checksum, _Resolver(repository, old), path


def _check(
    values: tuple[Path, bytes, bytes, str, _Resolver, Path],
    *,
    name: str = NAME,
    with_resolver: bool = True,
) -> None:
    repository, old, _, expected, resolver, _ = values
    source._validate_current_source(
        repository,
        name,
        resolver.logical,
        old,
        expected,
        resolver.detached,
        source_buffer=cast(Any, resolver) if with_resolver else None,
    )


def test_one_literal_extension_is_source_bound(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path],
) -> None:
    _check(admitted)
    assert admitted[4].fresh_calls == 2


@pytest.mark.parametrize(
    "mutation",
    [
        "missing-resolver",
        "capture-prefix",
        "capture-hash",
        "repository",
        "logical-prefix",
        "non-detached",
        "member-size",
        "path-alias",
        "duplicate-binding",
        "captured-body",
        "expected-hash",
    ],
)
def test_chronology_source_binding_refuses_mismatch(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path], mutation: str
) -> None:
    _check(admitted)
    repository, old, current, expected, resolver, path = admitted
    with_resolver = True
    if mutation == "missing-resolver":
        with_resolver = False
    elif mutation == "capture-prefix":
        resolver.prefix += "-other"
    elif mutation == "capture-hash":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif mutation == "repository":
        resolver.repository = repository.parent
    elif mutation == "logical-prefix":
        resolver.logical = "alias/" + NAME
    elif mutation == "non-detached":
        resolver.detached = frozenset()
    elif mutation == "member-size":
        resolver.descriptor.members[resolver.logical]["bytes"] += 1
    elif mutation == "path-alias":
        resolver.descriptor.groups[0]["resolved_paths"] = [
            (resolver.logical, "aliases/" + NAME)
        ]
    elif mutation == "duplicate-binding":
        resolver.descriptor.groups.append(copy.deepcopy(resolver.descriptor.groups[0]))
    elif mutation == "captured-body":
        old += b"# other capture\n"
    else:
        expected = "0" * 64
    changed = repository, old, current, expected, resolver, path
    with pytest.raises(ReportRebuildError):
        _check(changed, with_resolver=with_resolver)


@pytest.mark.parametrize(
    "suffix",
    [
        b"\n# unrelated comment\n",
        b"\nimport math\n",
        b"\nNUMBER = 2\n",
        b"\ndef another(): return 1\n",
        b" \n",
    ],
)
def test_no_other_current_byte_is_admitted(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path], suffix: bytes
) -> None:
    _check(admitted)
    admitted[5].write_bytes(admitted[5].read_bytes() + suffix)
    with pytest.raises(ReportRebuildError):
        _check(admitted)


@pytest.mark.parametrize(
    "kind", ["symlink", "ancestor-symlink", "hardlink", "concurrent-change"]
)
def test_regular_single_link_stable_source_is_required(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path], kind: str, tmp_path: Path
) -> None:
    _check(admitted)
    resolver, path = admitted[4:]
    if kind == "symlink":
        saved = path.read_bytes()
        path.unlink()
        target = tmp_path / "source-target.py"
        target.write_bytes(saved)
        path.symlink_to(target)
    elif kind == "ancestor-symlink":
        parent = path.parent
        moved = parent.with_name(parent.name + "-outside")
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    elif kind == "hardlink":
        os.link(path, tmp_path / "second-link.py")
    else:
        resolver.path = path
        resolver.change_on = resolver.fresh_calls + 2
    error = (
        ReportOwnershipError
        if kind in {"symlink", "ancestor-symlink"}
        else ReportRebuildError
    )
    with pytest.raises(error):
        _check(admitted)


def test_unknown_path_cannot_use_qualifier_law(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path],
) -> None:
    _check(admitted)
    repository = admitted[0]
    name = "packages/unknown_math.py"
    path = repository / name
    path.write_bytes(admitted[2])
    with pytest.raises(ReportRebuildError):
        _check(admitted, name=name)


def test_other_pattern_edit_is_not_a_qualifier_extension(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path],
) -> None:
    _check(admitted)
    admitted[5].write_bytes(admitted[2].replace(b"IGNORECASE", b"ASCII"))
    with pytest.raises(ReportRebuildError):
        _check(admitted)


def test_existing_equal_source_needs_no_new_role(
    admitted: tuple[Path, bytes, bytes, str, _Resolver, Path],
) -> None:
    admitted[5].write_bytes(admitted[1])
    _check(admitted, with_resolver=False)
    assert admitted[4].fresh_calls == 0
