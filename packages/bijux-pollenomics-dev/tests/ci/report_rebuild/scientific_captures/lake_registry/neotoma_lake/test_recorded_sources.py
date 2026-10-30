"""Authenticate nine retained producer bindings without current-source substitution."""

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.neotoma_lake.members import (
    validate_recorded_source_bindings,
)


def _nine_bindings() -> tuple[dict[str, Any], dict[str, Any], dict[str, bytes]]:
    """Declare nine tiny source identities instead of a retained real capsule."""
    bindings = {}
    members = {}
    bodies = {}
    for index in range(9):
        name = f"packages/own/source_{index}.py"
        body = f"VALUE = {index}\n".encode()
        pin = {"bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}
        bindings[name] = pin
        members["source/" + name] = dict(pin)
        bodies["source/" + name] = body
    return bindings, members, bodies


def test_recorded_lake_sources_are_authenticated_at_their_own_epoch() -> None:
    bindings, members, bodies = _nine_bindings()
    validate_recorded_source_bindings(bindings, members, bodies.__getitem__)


@pytest.mark.parametrize(
    "damage", ["missing", "extra", "member", "bytes", "hash", "body"]
)
def test_recorded_lake_source_binding_refuses_population_or_identity_drift(
    damage: str,
) -> None:
    bindings, members, bodies = _nine_bindings()
    validate_recorded_source_bindings(bindings, members, bodies.__getitem__)
    name = next(iter(bindings))
    logical = "source/" + name
    if damage == "missing":
        bindings.pop(name)
    elif damage == "extra":
        bindings[name + ".extra"] = bindings[name]
    elif damage == "member":
        members.pop(logical)
    elif damage in {"bytes", "hash"}:
        members[logical]["bytes" if damage == "bytes" else "sha256"] = (
            -1 if damage == "bytes" else "0" * 64
        )
    else:
        bodies[logical] = b"VALUE = 9\n"
    with pytest.raises(ReportRebuildError):
        validate_recorded_source_bindings(bindings, members, bodies.__getitem__)
