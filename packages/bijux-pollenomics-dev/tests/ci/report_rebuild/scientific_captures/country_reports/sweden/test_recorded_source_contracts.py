"""Keep the fifty-one recorded producer identities and current source roles distinct."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden.metadata import (
    validate_recorded_source_contracts,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    documentation,
)

DOC = "packages/bijux-pollenomics/src/bijux_pollenomics/adna/domain/locality.py"
TEMPLATE = "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/template.py"


def _contracts(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[list[dict[str, Any]], Any, dict[str, bytes]]:
    """Construct only tiny source strings, with a controlled descriptor identity."""
    rows = []
    members = {}
    paths = []
    bodies = {}
    for index in range(51):
        name = (
            DOC
            if index == 1
            else TEMPLATE
            if index == 2
            else f"packages/own/contract_{index}.py"
        )
        body = f"VALUE = {index}\n".encode()
        digest = hashlib.sha256(body).hexdigest()
        row = {"path": name, "bytes": len(body), "sha256": digest}
        logical = "members/" + digest
        rows.append(row)
        members[logical] = {key: row[key] for key in ("sha256", "bytes")}
        paths.append((logical, name))
        bodies[logical] = body
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(body)
    (root / DOC).write_bytes(
        b'"""Own module documentation."""\n\n' + bodies["members/" + rows[1]["sha256"]]
    )
    (root / TEMPLATE).write_bytes(b"CHANGED_CURRENT_TEMPLATE = 9\n")
    monkeypatch.setattr(
        documentation,
        "DOCUMENTED_SOURCE_STRINGS",
        {DOC: {"<module>": "Own module documentation."}},
    )
    fresh_calls = []
    resolver = SimpleNamespace(
        repository=root,
        descriptor=SimpleNamespace(members=members, groups=[{"resolved_paths": paths}]),
        read_source=bodies.__getitem__,
        fresh=lambda: fresh_calls.append(True),
        fresh_calls=fresh_calls,
    )
    return rows, resolver, bodies


def test_recorded_source_and_current_meaning_are_both_preserved(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rows, resolver, bodies = _contracts(tmp_path, monkeypatch)
    facts = validate_recorded_source_contracts(
        tmp_path, rows, cast(SourceCapsule, resolver)
    )
    assert facts["original_source_contracts_authenticated"] == 51
    assert facts["current_default_exact_sources"] == 49
    assert facts["exact_named_documentation_sources"] == [DOC]
    assert facts["historical_renderer_sources"] == [TEMPLATE]
    assert facts["current_browser_or_native_equivalence_claimed"] is False
    assert resolver.fresh_calls == [True, True]
    assert len(bodies) == 51


@pytest.mark.parametrize(
    "damage",
    [
        "missing_row",
        "duplicate_path",
        "unknown_field",
        "escaped_path",
        "false_bytes",
        "missing_member",
        "wrong_stored_path",
        "old_bytes",
        "current_math",
        "documentary_math",
        "wrong_documentary_literal",
        "missing_current",
        "symlink",
        "hardlink",
    ],
)
def test_source_binding_math_and_ownership_refusals_remain_strict(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    rows, resolver, bodies = _contracts(tmp_path, monkeypatch)
    row = rows[0]
    logical = "members/" + row["sha256"]
    current = tmp_path / row["path"]
    if damage == "missing_row":
        rows.pop()
    elif damage == "duplicate_path":
        rows[-1]["path"] = row["path"]
    elif damage == "unknown_field":
        row["extra"] = "unowned"
    elif damage == "escaped_path":
        row["path"] = "../private.py"
    elif damage == "false_bytes":
        row["bytes"] = False
    elif damage == "missing_member":
        resolver.descriptor.members.pop(logical)
    elif damage == "wrong_stored_path":
        resolver.descriptor.groups[0]["resolved_paths"][0] = (
            logical,
            "packages/wrong.py",
        )
    elif damage == "old_bytes":
        bodies[logical] = b"CHANGED_OLD_VALUE = 9\n"
    elif damage == "current_math":
        current.write_bytes(b"VALUE = 9\n")
    elif damage == "documentary_math":
        (tmp_path / DOC).write_bytes(b'"""Own module documentation."""\n\nVALUE = 9\n')
    elif damage == "wrong_documentary_literal":
        (tmp_path / DOC).write_bytes(b'"""Unapproved documentation."""\n\nVALUE = 1\n')
    elif damage == "missing_current":
        current.unlink()
    else:
        target = tmp_path / "own-alias-reference"
        target.write_bytes(current.read_bytes())
        current.unlink()
        if damage == "symlink":
            current.symlink_to(target)
        else:
            current.hardlink_to(target)
    with pytest.raises((ValueError, OSError)):
        validate_recorded_source_contracts(
            tmp_path, rows, cast(SourceCapsule, resolver)
        )
