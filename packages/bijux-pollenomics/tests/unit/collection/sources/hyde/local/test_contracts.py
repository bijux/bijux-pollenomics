"""Resource and retained scalar limits reject ambiguous or unbounded values."""

from dataclasses import replace

import pytest

from bijux_pollenomics.collection.sources.hyde.local import LocalInventoryLimits
from bijux_pollenomics.collection.sources.hyde.local.contracts import (
    decode,
    integer,
    relative_path,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


@pytest.mark.parametrize(
    "field,value",
    [
        ("chunk_bytes", 0),
        ("chunk_bytes", True),
        ("chunk_bytes", 10**9),
        ("maximum_files", 100001),
        ("maximum_metadata_total_bytes", -1),
        ("maximum_retained_bytes", 10**400),
    ],
)
def test_resource_limits_are_bounded_integers(field: str, value: int) -> None:
    with pytest.raises(IntakeRefusal):
        replace(LocalInventoryLimits(), **{field: value})


@pytest.mark.parametrize(
    "path", ["../raw", "/raw", "./raw", "raw//name", "raw/../name", "raw\x00name"]
)
def test_relative_names_never_escape_or_normalize_silently(path: str) -> None:
    with pytest.raises(IntakeRefusal):
        relative_path(path)


def test_duplicate_json_and_boolean_counts_refuse() -> None:
    with pytest.raises(ValueError):
        decode(b'{"a":1,"a":2}\n')
    with pytest.raises(IntakeRefusal):
        integer(False, "count")
