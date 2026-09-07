"""Checkout-independent AADR source identity tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.species.homo_sapiens.materialization.reconciliation import (
    reconcile_aadr_panels,
)
from bijux_pollenomics.collection.sources.aadr.materialization.accountability import (
    build_aadr_accountability_stream_descriptor,
)
from bijux_pollenomics.collection.sources.aadr.materialization.source_rows import (
    load_aadr_source_table,
    validate_aadr_logical_source_path,
)

_SOURCE = (
    b"Genetic ID\tPolitical Entity\tMethod for Determining Date\t"
    b"Date mean in BP\tDate standard deviation in BP\tFull Date\tLatitude\tLongitude\n"
    b"ID-1\tSweden\tDirect\t0\t0\t1-0 BP\t0\t0\n"
)


def test_logical_path_keeps_identity_and_stream_digest_checkout_independent(
    tmp_path: Path,
) -> None:
    first_path = tmp_path / "checkout-a" / "panel.anno"
    second_path = tmp_path / "checkout-b" / "panel.anno"
    first_path.parent.mkdir()
    second_path.parent.mkdir()
    first_path.write_bytes(_SOURCE)
    second_path.write_bytes(_SOURCE)
    logical_path = "data/aadr/v66/ho/v66.HO.aadr.PUB.anno"

    first = load_aadr_source_table(
        first_path,
        source_release="v66",
        dataset_name="ho",
        logical_source_path=logical_path,
    )
    second = load_aadr_source_table(
        second_path,
        source_release="v66",
        dataset_name="ho",
        logical_source_path=logical_path,
    )

    assert first == second
    assert first.source.source_path == logical_path
    assert first.source.key == second.source.key
    assert all(row.source is first.source for row in first.rows)
    assert build_aadr_accountability_stream_descriptor(
        reconcile_aadr_panels((first,))
    ) == build_aadr_accountability_stream_descriptor(reconcile_aadr_panels((second,)))


@pytest.mark.parametrize(
    "value",
    (
        "",
        "/data/aadr/v66/panel.anno",
        "../data/aadr/v66/panel.anno",
        "data/aadr/../v66/panel.anno",
        "./data/aadr/v66/panel.anno",
        "data\\aadr\\v66\\panel.anno",
        "data//aadr/v66/panel.anno",
    ),
)
def test_logical_path_rejects_checkout_or_noncanonical_identity(value: str) -> None:
    with pytest.raises(ValueError, match="logical source path"):
        validate_aadr_logical_source_path(value)
