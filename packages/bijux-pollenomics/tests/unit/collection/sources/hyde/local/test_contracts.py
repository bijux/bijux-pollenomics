"""Resource and retained scalar limits reject ambiguous or unbounded values."""

from dataclasses import replace
from pathlib import Path

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


def test_bound_archive_member_rejects_cross_parent_occurrence(tmp_path: Path) -> None:
    from dataclasses import replace

    from bijux_pollenomics.collection.sources.hyde.local import (
        prepare_local_hyde_inventory,
        select_local_hyde_archive_member,
    )

    from .test_inventory import source_fixture

    source = source_fixture(tmp_path / "raw")
    product = prepare_local_hyde_inventory(source, tmp_path / "custody")
    selected = select_local_hyde_archive_member(
        product, archive_path="native.zip", member_index=1
    )
    with pytest.raises(IntakeRefusal):
        replace(selected, archive_sha256="0" * 64)


@pytest.mark.parametrize(
    "field,value",
    [
        ("decoded_filename", "different.asc"),
        ("symlink", True),
        ("extra_hex", "xyz"),
        ("date_time", [1, 2]),
    ],
)
def test_bound_occurrence_shares_full_custody_semantic_admission(
    tmp_path: Path, field: str, value: object
) -> None:
    from dataclasses import replace
    import json

    from bijux_pollenomics.collection.sources.hyde.local import (
        prepare_local_hyde_inventory,
        select_local_hyde_archive_member,
    )
    from bijux_pollenomics.collection.sources.hyde.local.contracts import encode

    from .test_inventory import source_fixture

    source = source_fixture(tmp_path / "raw")
    custody = prepare_local_hyde_inventory(source, tmp_path / "custody")
    selected = select_local_hyde_archive_member(
        custody, archive_path="native.zip", member_index=1
    )
    row = json.loads(selected.occurrence_json)
    row[field] = value
    with pytest.raises(IntakeRefusal):
        replace(selected, occurrence_json=encode(row).decode("ascii"))
