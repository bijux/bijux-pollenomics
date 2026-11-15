"""Known null aggregates retain raw source evidence without fabricated targets."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.facets import (
    capture_neotoma_dataset_facets,
    read_neotoma_facet_body,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.links import (
    discover_neotoma_facet_links,
)
from bijux_pollenomics.collection.sources.neotoma.capture.facets.qualification import (
    qualify_neotoma_facet_capture,
)

from ...resources.native_payloads import response, spec
from ..parent_scope.native_sources import source_inputs
from .test_profiles import EMPTY_LITHOLOGY, NULL_TAXA


@pytest.mark.parametrize(
    "dataset_id,facet,raw,raw_rows",
    [(7861, "taxa", NULL_TAXA, 1), (10508, "lithology", EMPTY_LITHOLOGY, 0)],
)
def test_empty_population_source_access_retains_bytes_and_discovers_no_targets(
    tmp_path: Path, dataset_id: int, facet: str, raw: bytes, raw_rows: int
) -> None:
    plan, scope = source_inputs(
        tmp_path / "inputs", (spec(dataset_id),), facets=(facet,)
    )
    root = tmp_path / "capture"
    captured = capture_neotoma_dataset_facets(
        root, plan=plan, scope=scope, fetch=lambda url, **_: response(url, raw)
    )
    before = {path.name: path.read_bytes() for path in root.iterdir()}
    scopes = {plan.roster_sha256: scope}
    derived = qualify_neotoma_facet_capture(
        root, expected_manifest_sha256=captured.manifest_sha256, scope_inputs=scopes
    )
    assert derived["entries"][0]["qualification_status"] == "qualified_source_schema"
    assert derived["entries"][0]["raw_row_count"] == raw_rows
    body = read_neotoma_facet_body(
        root,
        facet_key=captured.facets[0]["facet_key"],
        expected_manifest_sha256=captured.manifest_sha256,
        scope_inputs=scopes,
    )
    assert body.body == raw
    for higher in (False, True):
        links = discover_neotoma_facet_links(
            root,
            include_higher_taxa=higher,
            expected_manifest_sha256=captured.manifest_sha256,
            scope_inputs=scopes,
        )
        assert (
            links["links"] == []
            and links["targets"] == []
            and links["higher_taxon_leads"] == []
        )
        assert links["unavailable"] == []
    assert before == {path.name: path.read_bytes() for path in root.iterdir()}
