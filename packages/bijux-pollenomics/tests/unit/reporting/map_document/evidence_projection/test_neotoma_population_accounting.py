"""Published source details reconcile separately from country-excluded rows."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.neotoma.materialization import (
    materialize_neotoma_relational_snapshot,
)
from bijux_pollenomics.collection.sources.neotoma.relational import (
    build_neotoma_relational_snapshot,
)
from bijux_pollenomics.reporting.map_document.evidence_projection.neotoma import (
    _project_neotoma,
)
from tests.support.neotoma import country_decisions, download_row, set_row_identity
from tests.support.neotoma.relational_shapes import nested, rows


def test_country_excluded_rows_are_denominators_not_published_details(
    tmp_path: Path,
) -> None:
    admitted = download_row()
    excluded = download_row()
    set_row_identity(excluded, 40)
    sample = rows(nested(excluded, "site", "collectionunit", "dataset")["samples"])[0]
    observations = rows(sample["datum"])
    observations.append(
        {**deepcopy(observations[0]), "taxonid": 9999, "variablename": "Excluded taxon"}
    )
    sample["datum"] = observations
    snapshot = build_neotoma_relational_snapshot(
        [admitted, excluded],
        source_snapshot_id="sha256:" + "c" * 64,
        build_id="sha256:" + "b" * 64,
        country_by_site_id=country_decisions([admitted]),
    )
    (tmp_path / "neotoma").mkdir()
    materialize_neotoma_relational_snapshot(
        tmp_path / "neotoma/relational", snapshot, rows_per_part=1
    )

    records, raw_accounting, _ = _project_neotoma(
        tmp_path, {"features": [{"evidence_row_id": "20"}]}
    )
    accounting = cast(dict[str, Any], raw_accounting)
    assert [record["record_id"] for record in records] == ["neotoma:site:20"]
    assert accounting["excluded_unassigned_site_ids"] == ["neotoma:site:40"]
    assert accounting["detail_row_counts"] == {
        "collection_units": 1,
        "datasets": 1,
        "samples": 1,
        "age_claims": 2,
        "observations": 2,
        "variables": 2,
        "chronologies": 2,
        "chronology_controls": 1,
    }
    assert accounting["detail_row_denominators"] == {
        "collection_units": 2,
        "datasets": 2,
        "samples": 2,
        "age_claims": 4,
        "observations": 5,
        "variables": 3,
        "chronologies": 4,
        "chronology_controls": 2,
    }
    assert accounting["excluded_detail_row_counts"] == {
        "collection_units": 1,
        "datasets": 1,
        "samples": 1,
        "age_claims": 2,
        "observations": 3,
        "variables": 1,
        "chronologies": 2,
        "chronology_controls": 1,
    }
    assert accounting["detail_row_exclusion_reason_code"] == (
        "site_without_governed_country_assignment"
    )
    assert accounting["variable_count_semantics"] == (
        "unique_variable_ids; excluded_counts_include_only_ids_absent_from_projected_sites"
    )
    for name, denominator in accounting["detail_row_denominators"].items():
        assert denominator == (
            accounting["detail_row_counts"][name]
            + accounting["excluded_detail_row_counts"][name]
        )
