from __future__ import annotations

import copy

from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.roundtrip import (
    SURFACES,
    native_hierarchy,
    reconcile_hierarchy,
)
from tests.support.neotoma import download_row
from tests.support.neotoma.relational_shapes import mapping, nested, rows, tables


def test_native_roundtrip_detects_changed_datum_and_parent() -> None:
    raw = download_row()
    snapshot = build_neotoma_relational_snapshot(
        [raw], source_snapshot_id="sha256:fixture", build_id="fixture-build"
    )
    native = native_hierarchy([raw])
    assert reconcile_hierarchy(
        native, tables(snapshot, SURFACES), rows(snapshot["conflicts"])
    )["match"]

    changed = copy.deepcopy(snapshot)
    mapping(rows(changed["observations"])[0]["source_payload"])["value"] = 999
    result = reconcile_hierarchy(
        native, tables(changed, SURFACES), rows(changed["conflicts"])
    )
    assert nested(result, "surfaces", "observations")["missing_rows"] == 1
    assert nested(result, "surfaces", "observations")["unexpected_rows"] == 1

    changed = copy.deepcopy(snapshot)
    rows(changed["observations"])[0]["sample_id"] = "neotoma:sample:other"
    result = reconcile_hierarchy(
        native, tables(changed, SURFACES), rows(changed["conflicts"])
    )
    assert not nested(result, "surfaces", "observations")["match"]
