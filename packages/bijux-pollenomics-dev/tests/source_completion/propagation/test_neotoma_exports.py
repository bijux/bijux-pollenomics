"""Reject every non-URL export mutation and preserve exact named physical custody."""

from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest


def module() -> ModuleType:
    root = next(
        p
        for p in Path(__file__).parents
        if (
            p
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/propagation/neotoma_exports.py"
        ).is_file()
    )
    path = (
        root
        / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/propagation/neotoma_exports.py"
    )
    spec = importlib.util.spec_from_file_location("neotoma_export_custody", path)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def export() -> dict[str, Any]:
    return {
        "selection": {"shared_url": "reference", "window": [0, 100]},
        "records": [{"id": "native1", "count": 4}, {"id": "native2", "count": 0}],
        "claims": {"scientific_admission": False},
    }


def test_exact_declared_leaf_transition_preserves_every_other_value() -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = "captured"
    assert (
        len(module().validate_selection_transition(old, new, "reference", "captured"))
        == 64
    )
    assert old == export()


@pytest.mark.parametrize(
    "mutation",
    [
        "count",
        "sample-id",
        "order",
        "bool-as-int",
        "extra-key",
        "missing-key",
        "window",
        "provenance",
    ],
)
def test_other_export_mutations_refuse(mutation: str) -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = "captured"
    if mutation == "count":
        new["records"][0]["count"] = 5
    elif mutation == "sample-id":
        new["records"][0]["id"] = "other"
    elif mutation == "order":
        new["records"].reverse()
    elif mutation == "bool-as-int":
        new["claims"]["scientific_admission"] = 0
    elif mutation == "extra-key":
        new["extra"] = None
    elif mutation == "missing-key":
        del new["claims"]
    elif mutation == "window":
        new["selection"]["window"][0] = 1
    else:
        new["provenance"] = {"source": "invented"}
    with pytest.raises(ValueError, match="outside /selection/shared_url"):
        module().validate_selection_transition(old, new, "reference", "captured")


def test_object_field_order_change_refuses() -> None:
    old = export()
    new = dict(reversed(list(deepcopy(old).items())))
    new["selection"]["shared_url"] = "captured"
    with pytest.raises(ValueError, match="outside"):
        module().validate_selection_transition(old, new, "reference", "captured")


@pytest.mark.parametrize("url", ["reference", "another-port", None, 1])
def test_unknown_url_or_type_refuses(url: object) -> None:
    old = export()
    new = deepcopy(old)
    new["selection"]["shared_url"] = url
    with pytest.raises(ValueError, match="Named shared URL"):
        module().validate_selection_transition(old, new, "reference", "captured")


@pytest.mark.parametrize(
    "raw", [b'{"key":1,"key":2}', b'{"number":NaN}', b'{"number":1e999}', b"[]"]
)
def test_ambiguous_or_nonfinite_json_refuses(raw: bytes) -> None:
    with pytest.raises(ValueError):
        module()._object(raw)


@pytest.mark.parametrize("path", ["../outside", "/outside", "data/../outside"])
def test_confined_physical_custody_refuses_escape(tmp_path: Path, path: str) -> None:
    with pytest.raises(ValueError):
        module()._file(tmp_path, path)


def readiness_reference() -> dict[str, Any]:
    code = module()
    return {
        "source_identity": {
            "export_sha256": {site: before for site, before, _ in code.EXPECTED_EXPORTS}
        },
        "denominators": {"refused": 256, "events": 0, "estimator_invocations": 0},
        "claims": {"first_observed_events_admitted": False},
        "attempts": [{"count": 4}],
    }


def readiness_current() -> dict[str, Any]:
    row = readiness_reference()
    row["source_identity"]["export_sha256"] = {
        site: after for site, _, after in module().EXPECTED_EXPORTS
    }
    return row


def test_only_two_named_readiness_digest_changes_are_permitted() -> None:
    module().validate_readiness_transition(readiness_reference(), readiness_current())


@pytest.mark.parametrize(
    "field",
    [
        "events",
        "refused",
        "estimator_invocations",
        "promotion",
        "attempt",
        "extra-site",
    ],
)
def test_any_other_readiness_scientific_change_refuses(field: str) -> None:
    row = readiness_current()
    if field in row["denominators"]:
        row["denominators"][field] += 1
    elif field == "promotion":
        row["claims"]["first_observed_events_admitted"] = True
    elif field == "attempt":
        row["attempts"][0]["count"] = 5
    else:
        row["source_identity"]["export_sha256"]["another"] = "unknown"
    with pytest.raises(ValueError, match="outside the two export digests"):
        module().validate_readiness_transition(readiness_reference(), row)


def test_physical_reference_symlink_refuses(tmp_path: Path) -> None:
    (tmp_path / "source").write_text("original")
    (tmp_path / "alias").symlink_to(tmp_path / "source")
    with pytest.raises(ValueError, match="confined regular"):
        module()._file(tmp_path, "alias")
