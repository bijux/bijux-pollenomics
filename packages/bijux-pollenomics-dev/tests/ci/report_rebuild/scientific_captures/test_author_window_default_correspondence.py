"""Refuse unclassified changes to the finite author-window default correspondence."""

from __future__ import annotations

import ast
import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as source,
)


def _own_source_spans() -> tuple[bytes, bytes, bytes]:
    """Compose declared tiny syntax spans without copying a source package fixture."""
    pairs = source._AUTHOR_DEFAULT_SOURCE_REPLACEMENTS
    before = b"\n".join(previous for _, previous in pairs)
    after = b"\n".join(inserted for inserted, _ in pairs)
    return (
        before,
        after,
        (
            ast.unparse(
                ast.fix_missing_locations(source._author_window_selector_contract())
            )
            + "\n"
        ).encode(),
    )


def test_declared_source_spans_reconstruct_exact_bytes() -> None:
    """Exercise every inverse span against its own explicitly declared predecessor."""
    before, after, selector = _own_source_spans()
    assert source._restore_author_default_source(before, after)
    assert source._author_window_selector_matches(selector)


@pytest.mark.parametrize("index", range(9))
def test_unclassified_inverse_span_changes_refuse(index: int) -> None:
    """A changed emitted field, call or selector span cannot borrow the role."""
    before, after, selector = _own_source_spans()
    inserted, _ = source._AUTHOR_DEFAULT_SOURCE_REPLACEMENTS[index]
    assert not source._restore_author_default_source(
        before, after.replace(inserted, inserted + b"unclassified = 1\n", 1)
    )


@pytest.mark.parametrize(
    ("original", "replacement"),
    (
        ("20732", "20733"),
        ("5, '1500', 1250, 1750", "5, '1500', 1250, 1751"),
        ("('EXEBRID', 'WHH11')", "('EXEBRID', 'WHH05')"),
        ("return (radius, counts)", "return (radius, list(reversed(counts)))"),
        ("len(taxa) != 31", "len(taxa) != 30"),
        ("model != '2'", "model != '1'"),
        ("@dataclass(frozen=True)", "@dataclass(frozen=False)"),
        ("index: int", "index: str"),
        ("import math", "import cmath as math"),
    ),
)
def test_selector_contract_changes_refuse(original: str, replacement: str) -> None:
    """Close constants, bindings, signatures, dataflow and strengthened refusals."""
    _, _, selector = _own_source_spans()
    text = selector.decode()
    assert original in text
    changed = text.replace(original, replacement, 1).encode()
    assert source._author_window_selector_matches(selector)
    assert not source._author_window_selector_matches(changed)


@pytest.mark.parametrize(
    "statement",
    (
        "import os\n",
        "unexpected = 1\n",
        "raise RuntimeError('unexpected')\n",
    ),
)
def test_extra_selector_statements_refuse(statement: str) -> None:
    """Additional import-time actions cannot hide outside the consumed helper bodies."""
    _, _, selector = _own_source_spans()
    assert source._author_window_selector_matches(selector)
    assert not source._author_window_selector_matches(selector + statement.encode())


@pytest.mark.parametrize(
    "suffix", (b"# changed unclassified bytes\n", b"unexpected = 1\n")
)
def test_unclassified_wrapper_bytes_refuse(suffix: bytes) -> None:
    """Every byte outside the nine declared inverse spans remains strict."""
    before, after, _ = _own_source_spans()
    assert source._restore_author_default_source(before, after)
    assert not source._restore_author_default_source(before, after + suffix)


@pytest.mark.parametrize("value", (b"", b"x = 1\n" * 4000, b"\xff"))
def test_selector_size_and_encoding_refuse(value: bytes) -> None:
    """Malformed and oversized selectors cannot enter correspondence analysis."""
    assert not source._author_window_selector_matches(value)


def _own_custody(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[SimpleNamespace, JsonObject, bytes, bytes, Path]:
    """Create small owned files and a declared identity without copying a package."""
    old = b"historical_value = 1\n"
    current = b"current_value = 2\n"
    identity = {"bytes": len(old), "sha256": hashlib.sha256(old).hexdigest()}
    monkeypatch.setattr(source, "AUTHOR_DEFAULT_IDENTITY", identity)
    wrapper = root / source.AUTHOR_DEFAULT_SOURCE
    selector = root / source.AUTHOR_WINDOW_SOURCE
    wrapper.parent.mkdir(parents=True)
    wrapper.write_bytes(current)
    selector.write_bytes(b"own_selector = 3\n")
    logical = "source/" + source.AUTHOR_DEFAULT_SOURCE
    fake = SimpleNamespace(
        repository=root.resolve(),
        detached=frozenset({logical}),
        descriptor=SimpleNamespace(members={logical: dict(identity)}),
        read_source=lambda name: old if name == logical else b"wrong member",
    )
    historical: JsonObject = {"path": source.AUTHOR_DEFAULT_SOURCE, **identity}
    # Custody checks are the subject; pure syntax matching has separate controls.
    monkeypatch.setattr(source, "_author_default_source_matches", lambda *_: True)
    return fake, historical, old, current, selector


def _check_custody(
    root: Path,
    fake: SimpleNamespace,
    historical: JsonObject,
    old: bytes,
    current: bytes,
) -> JsonObject:
    """Call the maintained entrypoint with a synthetic capsule and own byte identity."""
    return source._author_default_source_correspondence(
        root.resolve(),
        historical,
        old,
        current,
        "source/" + source.AUTHOR_DEFAULT_SOURCE,
        cast(SourceCapsule, fake),
    )


def test_own_custody_entrypoint_checks_real_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A declared own-file counterpart reaches the finite custody result."""
    fake, historical, old, current, _ = _own_custody(tmp_path, monkeypatch)
    result = _check_custody(tmp_path, fake, historical, old, current)
    assert result["classification"] == "finite_author_default_window_specialization"
    assert result["native_execution_claimed"] is False


@pytest.mark.parametrize(
    "defect",
    (
        "not_detached",
        "wrong_member",
        "wrong_bytes",
        "wrong_repository",
        "wrong_identity",
    ),
)
def test_detached_custody_binding_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    """Wrong declared members and old identities cannot use a counterpart role."""
    fake, historical, old, current, _ = _own_custody(tmp_path, monkeypatch)
    logical = "source/" + source.AUTHOR_DEFAULT_SOURCE
    if defect == "not_detached":
        fake.detached = frozenset()
    elif defect == "wrong_member":
        fake.descriptor.members[logical] = {"bytes": len(old), "sha256": "0" * 64}
    elif defect == "wrong_bytes":
        fake.read_source = lambda _: old + b"changed"
    elif defect == "wrong_repository":
        fake.repository = tmp_path / "another-repository"
    else:
        historical["sha256"] = "0" * 64
    with pytest.raises(
        ReportRebuildError, match="historical source binding|detached member"
    ):
        _check_custody(tmp_path, fake, historical, old, current)


@pytest.mark.parametrize("defect", ("symlink", "hardlink", "wrapper_mismatch"))
def test_current_counterpart_custody_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, defect: str
) -> None:
    """Aliases and a wrapper differing from the caller's bytes remain refused."""
    fake, historical, old, current, selector = _own_custody(tmp_path, monkeypatch)
    if defect == "symlink":
        target = tmp_path / "own-selector-target.py"
        target.write_bytes(selector.read_bytes())
        selector.unlink()
        selector.symlink_to(target)
    elif defect == "hardlink":
        os.link(selector, tmp_path / "own-selector-link.py")
    else:
        (tmp_path / source.AUTHOR_DEFAULT_SOURCE).write_bytes(current + b"changed")
    with pytest.raises(
        (ReportRebuildError, ReportOwnershipError),
        match="regular file|custody differs",
    ):
        _check_custody(tmp_path, fake, historical, old, current)


@pytest.mark.parametrize("changed_file", ("helper", "wrapper"))
def test_counterpart_change_during_verification_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, changed_file: str
) -> None:
    """A helper or wrapper modified during matching fails the final freshness check."""
    fake, historical, old, current, selector = _own_custody(tmp_path, monkeypatch)
    target = (
        selector
        if changed_file == "helper"
        else tmp_path / source.AUTHOR_DEFAULT_SOURCE
    )

    def change_after_read(*_: object) -> bool:
        target.write_bytes(target.read_bytes() + b"# changed during validation\n")
        return True

    monkeypatch.setattr(source, "_author_default_source_matches", change_after_read)
    with pytest.raises(ReportRebuildError, match="changed during verification"):
        _check_custody(tmp_path, fake, historical, old, current)
