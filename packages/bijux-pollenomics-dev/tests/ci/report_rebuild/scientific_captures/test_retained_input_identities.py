"""Keep source identities typed and confined across independent retained consumers."""

from __future__ import annotations

from copy import deepcopy
import importlib
from types import ModuleType
from typing import Any

import pytest

MODULES = (
    "adna.execution_packet",
    "adna.animal_packet",
    "pollen_source.neotoma_counts.transport",
    "source_accounting.transport",
)


def reader(name: str) -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics_dev.ci.report_rebuild.scientific_captures." + name
    )


@pytest.mark.parametrize("name", MODULES)
def test_constructed_identity_has_exact_typed_source_members(name: str) -> None:
    module = reader(name)
    source = {"path": "/constructed/source/record.json", "sha256": "a" * 64, "bytes": 2}
    assert module.normalized(source) == source
    assert module.indexed([source]) == {source["path"]: source}


@pytest.mark.parametrize("name", MODULES)
@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("path", "relative.json"),
        ("path", "/source/../record"),
        ("path", "/source//record"),
        ("path", "/source\\record"),
        ("bytes", False),
        ("bytes", -1),
        ("bytes", 2.0),
        ("sha256", "bad"),
        ("sha256", "A" * 64),
    ],
)
def test_ambiguous_or_untyped_source_identity_refuses(
    name: str, key: str, value: Any
) -> None:
    source = {"path": "/constructed/source/record.json", "sha256": "a" * 64, "bytes": 2}
    source[key] = value
    with pytest.raises(ValueError):
        reader(name).normalized(source)


@pytest.mark.parametrize("name", MODULES)
def test_repeated_input_paths_refuse_even_when_bytes_match(name: str) -> None:
    source = {"path": "/constructed/source/record.json", "sha256": "a" * 64, "bytes": 2}
    with pytest.raises(ValueError):
        reader(name).indexed([source, deepcopy(source)])


@pytest.mark.parametrize("name", MODULES)
@pytest.mark.parametrize("raw", [b'{"source":1,"source":2}', b'{"source":NaN}'])
def test_duplicate_or_nonfinite_retained_json_refuses(name: str, raw: bytes) -> None:
    with pytest.raises(ValueError):
        reader(name).json_object(raw)


@pytest.mark.parametrize("name", MODULES)
@pytest.mark.parametrize(("left", "right"), [(False, 0), (None, 0), (1.0, 1)])
def test_source_type_aliases_never_compare_equal(
    name: str, left: object, right: object
) -> None:
    with pytest.raises(ValueError):
        reader(name).same(left, right)
