"""Refuse source drift outside two explicitly bound collector extensions."""

from __future__ import annotations

import copy
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as source,
)

ROOTSI = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/rootsi_input_closure.py"
NEOTOMA = "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/__init__.py"
CAPTURE = "data/method-certification/author-optimizer-diagnostic-source-capture"
CAPTURE_SHA = "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"


def _texts(name: str) -> tuple[bytes, bytes]:
    if name == NEOTOMA:
        old = b'import re\nPATTERNS = (re.compile(r"(?:^|\\s)cf\\.\\s", re.IGNORECASE),)\nSCOPE = "source labels"\n'
        return old, old.replace(b"cf\\.\\s", b"cf\\.?\\s")
    old = (
        b"def _publication_matches(inputs):\n"
        b"    result = {}\n"
        b"    for publication in inputs.publication.records:\n"
        b"        observed = tuple(\n"
        b"            candidate\n"
        b"            for rootsi in inputs.rootsi\n"
        b"            if (candidate := _match(rootsi, publication)) is not None\n"
        b"        )\n"
        b"        result[publication.worksheet_row] = observed\n"
        b"    return result\n"
    )
    current = old.replace(
        b"    result = {}\n", b"    result = {}\n" + source._ROOTSI_INDEX_INITIALIZATION
    )
    current = current.replace(
        b"        observed = tuple(\n",
        source._ROOTSI_INDEX_LOOKUP + b"        observed = tuple(\n",
    )
    current = current.replace(
        b"            for rootsi in inputs.rootsi\n",
        b"            for index in sorted(indexes)\n",
    )
    return old, current.replace(
        b"_match(rootsi, publication)", b"_match(inputs.rootsi[index], publication)"
    )


class _Resolver:
    def __init__(self, repository: Path, name: str, old: bytes) -> None:
        self.repository = repository
        self.prefix = CAPTURE
        self.logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
        self.detached = frozenset({self.logical})
        expected = {"bytes": len(old), "sha256": hashlib.sha256(old).hexdigest()}
        self.descriptor = SimpleNamespace(
            capture={"sha256": CAPTURE_SHA},
            members={self.logical: expected},
            groups=[{"resolved_paths": [(self.logical, name)]}],
        )
        self.old = old
        self.fresh_calls = 0
        self.mutate: Path | None = None

    def read_source(self, logical: str) -> bytes:
        assert logical == self.logical
        return self.old

    def fresh(self) -> None:
        self.fresh_calls += 1
        if self.fresh_calls == 2 and self.mutate is not None:
            self.mutate.write_bytes(self.mutate.read_bytes() + b"# changed\n")


@pytest.fixture(params=[ROOTSI, NEOTOMA], ids=["Rootsi-index", "Neotoma-qualifier"])
def admitted(
    request: pytest.FixtureRequest, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, str, dict[str, object], _Resolver, Path]:
    name = cast(str, request.param)
    old, current = _texts(name)
    repository = tmp_path.resolve()
    path = repository / name
    path.parent.mkdir(parents=True)
    path.write_bytes(current)
    monkeypatch.setattr(
        source,
        "_COLLECTOR_SOURCE_IDENTITIES",
        {name: (hashlib.sha256(old).hexdigest(), len(old))},
    )
    row: dict[str, object] = {
        "path": name,
        "bytes": len(old),
        "sha256": hashlib.sha256(old).hexdigest(),
    }
    return repository, name, row, _Resolver(repository, name, old), path


def _check(
    values: tuple[Path, str, dict[str, object], _Resolver, Path],
) -> dict[str, object]:
    repository, _, row, resolver, _ = values
    return source._collector_source_extension_correspondence(
        repository, row, resolver.logical, cast(Any, resolver)
    )


def test_finite_extension_has_truthful_source_scope(
    admitted: tuple[Path, str, dict[str, object], _Resolver, Path],
) -> None:
    result = _check(admitted)
    assert result["classification"] == "finite_collector_source_extension"
    assert result["old_noninserted_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["current_classifier_native_or_browser_equivalence_claimed"] is False
    assert admitted[3].fresh_calls == 2
    assert result["original_bytes"] == admitted[2]["bytes"]
    assert result["original_sha256"] == admitted[2]["sha256"]


@pytest.mark.parametrize(
    "mutation",
    [
        "old-hash",
        "old-size",
        "boolean-size",
        "extra-field",
        "wrong-path",
        "capture-prefix",
        "capture-hash",
        "wrong-repository",
        "logical-prefix",
        "non-detached",
        "wrong-member-size",
        "path-alias",
        "duplicate-binding",
        "old-body",
    ],
)
def test_old_source_binding_refuses_every_mismatch(
    admitted: tuple[Path, str, dict[str, object], _Resolver, Path], mutation: str
) -> None:
    repository, name, row, resolver, _ = admitted
    if mutation == "old-hash":
        row["sha256"] = "0" * 64
    elif mutation == "old-size":
        row["bytes"] = cast(int, row["bytes"]) + 1
    elif mutation == "boolean-size":
        row["bytes"] = True
    elif mutation == "extra-field":
        row["scope"] = "extra"
    elif mutation == "wrong-path":
        row["path"] = "packages/unknown_math.py"
    elif mutation == "capture-prefix":
        resolver.prefix = CAPTURE + "-other"
    elif mutation == "capture-hash":
        resolver.descriptor.capture["sha256"] = "0" * 64
    elif mutation == "wrong-repository":
        resolver.repository = repository.parent
    elif mutation == "logical-prefix":
        resolver.logical = "source/" + name
    elif mutation == "non-detached":
        resolver.detached = frozenset()
    elif mutation == "wrong-member-size":
        resolver.descriptor.members[resolver.logical]["bytes"] += 1
    elif mutation == "path-alias":
        resolver.descriptor.groups[0]["resolved_paths"] = [
            (resolver.logical, "aliases/" + name)
        ]
    elif mutation == "duplicate-binding":
        resolver.descriptor.groups.append(copy.deepcopy(resolver.descriptor.groups[0]))
    else:
        resolver.old += b"# different old body\n"
    with pytest.raises(ReportRebuildError):
        _check(admitted)


@pytest.mark.parametrize(
    "suffix",
    [
        b"\n# unknown comment\n",
        b"\nimport math\n",
        b"\nCONSTANT = 2\n",
        b"\ndef new_definition(): return 1\n",
        b" \n",
    ],
)
def test_unrelated_current_bytes_are_not_waived(
    admitted: tuple[Path, str, dict[str, object], _Resolver, Path], suffix: bytes
) -> None:
    path = admitted[4]
    path.write_bytes(path.read_bytes() + suffix)
    with pytest.raises(ReportRebuildError):
        _check(admitted)


@pytest.mark.parametrize(
    "kind", ["symlink", "hardlink", "ancestor-symlink", "concurrent-change"]
)
def test_current_source_confinement_and_freshness(
    admitted: tuple[Path, str, dict[str, object], _Resolver, Path],
    kind: str,
    tmp_path: Path,
) -> None:
    path = admitted[4]
    if kind == "concurrent-change":
        admitted[3].mutate = path
    elif kind == "hardlink":
        os.link(path, tmp_path / "second-link.py")
    elif kind == "symlink":
        saved = path.read_bytes()
        path.unlink()
        target = tmp_path / "source-target.py"
        target.write_bytes(saved)
        path.symlink_to(target)
    else:
        parent = path.parent
        moved = parent.with_name(parent.name + "-outside")
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    with pytest.raises(ReportRebuildError):
        _check(admitted)


@pytest.mark.parametrize("path", [ROOTSI, NEOTOMA])
def test_unknown_extension_path_has_no_fallback(path: str) -> None:
    old, current = _texts(path)
    assert not source.collector_source_extension_matches(
        "packages/unknown_math.py", old, current
    )


@pytest.mark.parametrize("path", [ROOTSI, NEOTOMA])
def test_declared_span_changes_are_not_widened(path: str) -> None:
    old, current = _texts(path)
    replacement = (
        current.replace(b"IGNORECASE", b"ASCII")
        if path == NEOTOMA
        else current.replace(b"sorted(indexes)", b"list(indexes)")
    )
    assert not source.collector_source_extension_matches(path, old, replacement)
