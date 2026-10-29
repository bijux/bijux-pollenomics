"""Keep named documentation and historical metadata separate from current science."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as source,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    documentation,
    readers,
)


def _identity(name: str, raw: bytes) -> dict[str, object]:
    """Build an own-string authority, without importing a real source packet."""
    return {"path": name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def test_named_module_class_and_function_docs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Permit exactly declared literal docs and their adjacent blank separators."""
    name = "packages/example/source.py"
    old = b"class Example:\n    def value(self):\n        return 4\n"
    new = b'"""Module ownership."""\n\nclass Example:\n    """Class ownership."""\n\n    def value(self):\n        """Return the original value."""\n        return 4\n'
    monkeypatch.setattr(
        documentation,
        "DOCUMENTED_SOURCE_STRINGS",
        {
            name: {
                "<module>": "Module ownership.",
                "Example": "Class ownership.",
                "Example.value": "Return the original value.",
            }
        },
    )
    assert documentation._documented_source_matches(name, old, new)
    assert not documentation._documented_source_matches("packages/other.py", old, new)


@pytest.mark.parametrize(
    "suffix", [b"\n# unrelated comment\n", b"\nraise RuntimeError()\n", b"\n\n\n"]
)
def test_undeclared_source_suffix_refuses(
    monkeypatch: pytest.MonkeyPatch, suffix: bytes
) -> None:
    """Reject bytes unrelated to the exact named documentation insertion."""
    name = "packages/example/source.py"
    old = b"def value():\n    return 4\n"
    new = b'def value():\n    """Return four."""\n    return 4\n'
    monkeypatch.setattr(
        documentation, "DOCUMENTED_SOURCE_STRINGS", {name: {"value": "Return four."}}
    )
    assert not documentation._documented_source_matches(name, old, new + suffix)


@pytest.mark.parametrize(
    "new",
    [
        b'def value():\n    """Return five."""\n    return 4\n',
        b'def value():\n    """Return four."""\n    return 5\n',
        b'def renamed():\n    """Return four."""\n    return 4\n',
        b'def value():\n    """Return four."""; danger()\n    return 4\n',
        b'def value():\n    """Return four."""\n    # changed implementation comment\n    return 4\n',
    ],
)
def test_named_doc_or_executable_drift_refuses(
    monkeypatch: pytest.MonkeyPatch, new: bytes
) -> None:
    """Reject a changed literal, definition, action, value or noninserted comment."""
    name = "packages/example/source.py"
    monkeypatch.setattr(
        documentation, "DOCUMENTED_SOURCE_STRINGS", {name: {"value": "Return four."}}
    )
    assert not documentation._documented_source_matches(
        name, b"def value():\n    return 4\n", new
    )


def test_existing_doc_cannot_be_replaced(monkeypatch: pytest.MonkeyPatch) -> None:
    """Preserve original documentary and executable bytes beside an insertion."""
    name = "packages/example/source.py"
    monkeypatch.setattr(
        documentation, "DOCUMENTED_SOURCE_STRINGS", {name: {"value": "Return four."}}
    )
    old = b'def value():\n    """Original."""\n    return 4\n'
    new = b'def value():\n    """Return four."""\n    return 4\n'
    assert not documentation._documented_source_matches(name, old, new)


def test_three_named_protocol_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Permit only the three typed ellipsis expansions, preserving all signatures."""
    name = "packages/example/collection/sources/rootsi/cells/biff.py"
    signatures = [
        "    def dirlist(self) -> Sequence[DirectoryEntry]:",
        "    def get_named_stream(self, name: str) -> bytes | None:",
        "    def __call__(self, payload: bytes, *, logfile: TextIO) -> CompoundBook:",
    ]
    old = (
        "class Reader:\n" + "\n".join(s + " ..." for s in signatures) + "\n"
    ).encode()
    new = (
        "class Reader:\n"
        + "\n".join(
            s + '\n        """Own typed source."""\n        ...' for s in signatures
        )
        + "\n"
    ).encode()
    monkeypatch.setattr(
        documentation,
        "DOCUMENTED_SOURCE_STRINGS",
        {
            name: {
                "Reader.dirlist": "Own typed source.",
                "Reader.get_named_stream": "Own typed source.",
                "Reader.__call__": "Own typed source.",
            }
        },
    )
    assert documentation._documented_source_matches(name, old, new)
    assert not documentation._documented_source_matches(
        name, old, new.replace(b"        ...", b"        return None", 1)
    )


def test_historical_presentation_is_not_current_equality(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Keep old metadata exact while current semantic qualification is separate."""
    name = "packages/example/presentation.py"
    current = tmp_path / name
    current.parent.mkdir(parents=True)
    current.write_bytes(b"current schema, separately qualified")
    old = b"historical schema"
    logical = "source/" + name
    monkeypatch.setattr(source, "HISTORICAL_PRESENTATION_SOURCES", frozenset({name}))
    result = source._historical_metadata_source_role(
        tmp_path, _identity(name, old), old, logical, frozenset({logical})
    )
    assert result is not None
    assert result["old_current_source_equality_claimed"] is False
    assert result["native_execution_claimed"] is False


@pytest.mark.parametrize(
    "mutation",
    ["digest", "bytes", "boolean_bytes", "unlisted", "wrong_logical", "extra_key"],
)
def test_historical_presentation_binding_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """Require complete typed member identity and declared detached membership."""
    name = "packages/example/presentation.py"
    current = tmp_path / name
    current.parent.mkdir(parents=True)
    current.write_bytes(b"current")
    old = b"historical"
    logical = "source/" + name
    detached = frozenset({logical})
    row = _identity(name, old)
    if mutation == "digest":
        row["sha256"] = "0" * 64
    elif mutation == "bytes":
        row["bytes"] = len(old) + 1
    elif mutation == "boolean_bytes":
        row["bytes"] = True
    elif mutation == "unlisted":
        detached = frozenset()
    elif mutation == "wrong_logical":
        logical = "source/other.py"
        detached = frozenset({logical})
    else:
        row["unapproved"] = True
    monkeypatch.setattr(source, "HISTORICAL_PRESENTATION_SOURCES", frozenset({name}))
    with pytest.raises(ReportRebuildError):
        source._historical_metadata_source_role(tmp_path, row, old, logical, detached)


@pytest.mark.parametrize("entry", ["regular", "dangling_link", "directory"])
def test_retired_control_reintroduction_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, entry: str
) -> None:
    """Historical-only private control must stay absent, including dangling aliases."""
    name = "packages/example/private_control.py"
    current = tmp_path / name
    current.parent.mkdir(parents=True)
    old = b"own-string old private control, never executed"
    monkeypatch.setattr(source, "RETIRED_PRIVATE_CONTROL_SOURCE", name)
    monkeypatch.setattr(
        source,
        "RETIRED_PRIVATE_CONTROL_IDENTITY",
        {k: v for k, v in _identity(name, old).items() if k != "path"},
    )
    logical = "source/" + name
    assert (
        source._historical_metadata_source_role(
            tmp_path, _identity(name, old), old, logical, frozenset({logical})
        )
        is not None
    )
    if entry == "regular":
        current.write_bytes(b"reintroduced")
    elif entry == "dangling_link":
        current.symlink_to(current.parent / "absent.py")
    else:
        current.mkdir()
    with pytest.raises(ReportRebuildError, match="must remain absent"):
        source._historical_metadata_source_role(
            tmp_path, _identity(name, old), old, logical, frozenset({logical})
        )


def test_presentation_hardlink_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Require one physical current counterpart rather than an aliased source."""
    name = "packages/example/presentation.py"
    current = tmp_path / name
    current.parent.mkdir(parents=True)
    current.write_bytes(b"current")
    os.link(current, current.parent / "alias.py")
    old = b"historical"
    logical = "source/" + name
    monkeypatch.setattr(source, "HISTORICAL_PRESENTATION_SOURCES", frozenset({name}))
    with pytest.raises(ReportRebuildError):
        source._historical_metadata_source_role(
            tmp_path, _identity(name, old), old, logical, frozenset({logical})
        )


@pytest.mark.parametrize("mutation", ["none", "vector", "petr", "extra_action"])
def test_diagnostics_exact_source_read_seam(
    monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """Preserve every mathematical byte while changing exactly one source-read loop."""
    name = "packages/example/diagnostics.py"
    old_loop = "        if hashlib.sha256((repository / relative).read_bytes()).hexdigest() != digest:"
    new_loop = "        body = (\n            capture.read_input(relative)\n            if relative in capture.input_sha256\n            else _file(repository, relative)\n        )\n        if hashlib.sha256(body).hexdigest() != digest:"
    old = (
        "def vector_diagnostics(x):\n    return x + 1\n\ndef _csv_vector(x):\n    return x\n\ndef _number(x):\n    return float(x)\n\ndef build_diagnostics(repository, capture):\n    for relative, digest in inputs.items():\n"
        + old_loop
        + "\n            raise ValueError('changed')\n    return result\n"
    ).encode()
    current = old.replace(old_loop.encode(), new_loop.encode())
    if mutation == "vector":
        current = current.replace(b"return x + 1", b"return x + 2")
    elif mutation == "petr":
        current = current.replace(
            b"else _file(repository, relative)", b"else capture.read_input(relative)"
        )
    elif mutation == "extra_action":
        current = current.replace(
            b"    return result",
            b"    result = secretly_change(result)\n    return result",
        )
    monkeypatch.setattr(readers, "MIXED_CUSTODY_READER_SOURCES", frozenset({name}))
    if mutation == "none":
        readers._mixed_custody_contract(name, old, current)
    else:
        with pytest.raises(ReportRebuildError):
            readers._mixed_custody_contract(name, old, current)


@pytest.mark.parametrize("change", [False, True])
def test_independent_metric_functions_stay_exact(
    monkeypatch: pytest.MonkeyPatch, change: bool
) -> None:
    """Separate the IO function from all five independent numerical anchors."""
    name = "packages/example/diagnostics_verification.py"
    functions = ("verify_metrics", "verify", "_npy", "_same", "_encoded")
    old = (
        "\n\n".join("def " + f + "(value):\n    return value" for f in functions)
        + "\n\ndef _raw(path):\n    return old_read(path)\n"
    ).encode()
    current = old.replace(b"old_read(path)", b"declared_source_read(path)")
    if change:
        current = current.replace(
            b"def verify_metrics(value):\n    return value",
            b"def verify_metrics(value):\n    return value * 2",
        )
    monkeypatch.setattr(readers, "MIXED_CUSTODY_READER_SOURCES", frozenset({name}))
    if change:
        with pytest.raises(ReportRebuildError):
            readers._mixed_custody_contract(name, old, current)
    else:
        readers._mixed_custody_contract(name, old, current)


@pytest.mark.parametrize("changed_clause", [-1, *range(9)])
def test_original_native_predicate_blocks_stay_exact(
    monkeypatch: pytest.MonkeyPatch, changed_clause: int
) -> None:
    """Keep all nine complete native receipt/count/source predicates authoritative."""
    name = "packages/example/finite_covariance_capture.py"
    messages = (
        "Actual finite covariance native execution scope differs",
        "Reviewed committed scientific source custody required",
        "Exact native numeric/raw membership differs",
        "Exact execution custody evidence required",
        "Actual terminal or before/after custody differs",
        "Actual native command receipt differs",
        "Exact locked native archive population differs",
        "Cached source provenance differs",
        "Original R certificate changed",
    )
    body = "".join(
        "    if values["
        + repr(str(i))
        + "] != 0:\n        raise ValueError("
        + repr(message)
        + ")\n"
        for i, message in enumerate(messages)
    )
    old = ("def validated_finite_covariance_capture(values):\n" + body).encode()
    current = old.replace(
        b"def validated_finite_covariance_capture",
        b"def _validated_finite_covariance_capture",
    )
    if changed_clause >= 0:
        current = current.replace(
            ("values[" + repr(str(changed_clause)) + "] != 0").encode(),
            ("values[" + repr(str(changed_clause)) + "] != 1").encode(),
        )
    monkeypatch.setattr(readers, "MIXED_CUSTODY_READER_SOURCES", frozenset({name}))
    if changed_clause >= 0:
        with pytest.raises(ReportRebuildError):
            readers._mixed_custody_contract(name, old, current)
    else:
        readers._mixed_custody_contract(name, old, current)


@pytest.mark.parametrize(
    "current_bytes", [b"unchanged", b"unreviewed mathematical drift"]
)
def test_ordinary_source_default_remains_strict(
    tmp_path: Path, current_bytes: bytes
) -> None:
    """New ordinary source names have no metadata or current-postimage escape."""
    from types import SimpleNamespace

    name = "packages/example/numerical.py"
    path = tmp_path / name
    path.parent.mkdir(parents=True)
    path.write_bytes(current_bytes)
    old = b"unchanged"
    logical = "source/" + name
    buffer = SimpleNamespace(
        read_source=lambda selected: old if selected == logical else b"wrong",
        detached=frozenset({logical}),
    )
    if current_bytes == old:
        assert (
            source.validated_current_scientific_source(
                tmp_path, _identity(name, old), logical, cast(Any, buffer)
            )
            is None
        )
    else:
        with pytest.raises(ReportRebuildError):
            source.validated_current_scientific_source(
                tmp_path, _identity(name, old), logical, cast(Any, buffer)
            )
