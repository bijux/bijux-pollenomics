"""Immutable source-case plans normalize enumeration, never source byte identity."""

from copy import deepcopy
from importlib import import_module
from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal

from .support import fixture


def implementation():
    return import_module("bijux_pollenomics.analysis.lra.source_cases.contracts")


def test_plan_owns_canonical_case_enumeration(tmp_path: Path) -> None:
    _, value = fixture(tmp_path)
    cls = implementation().SourceCasePlan
    a = cls.from_dict(value)
    b = deepcopy(value)
    b["cases"].reverse()
    assert cls.from_dict(b).sha256 == a.sha256
    value["cases"].clear()
    assert len(a.payload()["cases"]) == 2


@pytest.mark.parametrize(
    "damage",
    ["duplicate", "unsafe_path", "bool_limit", "unknown_design", "unknown_field"],
)
def test_plan_refuses_ambiguous_or_unbounded_declarations(
    tmp_path: Path, damage: str
) -> None:
    _, value = fixture(tmp_path)
    if damage == "duplicate":
        value["cases"].append(deepcopy(value["cases"][0]))
    elif damage == "unsafe_path":
        value["envelope_ref"]["path"] = "../outside.json"
    elif damage == "bool_limit":
        value["limits"]["max_cases"] = True
    elif damage == "unknown_design":
        value["design"] = {"kind": "empirical_posterior"}
    else:
        value["automatic_approval"] = True
    with pytest.raises(LRARefusal):
        implementation().SourceCasePlan.from_dict(value)
