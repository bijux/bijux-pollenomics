"""Lookup-index guarantees for sample-owned locality evidence."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bijux_pollenomics.adna.projects.registry.sites import assembly


def test_index_preserves_normalization_and_lazy_duplicate_refusal() -> None:
    selected = SimpleNamespace(
        site_label="Bunds\u00f8",
        political_entity="Denmark",
        identity="selected",
    )
    null_locality = SimpleNamespace(
        site_label=None,
        political_entity=None,
        identity="null",
    )
    duplicate = SimpleNamespace(
        locality_text="Ignored Site",
        political_entity="Sweden",
        identity="duplicate",
    )
    rows = (
        selected,
        null_locality,
        duplicate,
        SimpleNamespace(**vars(duplicate)),
    )

    index = assembly._LocalityRowIndex(rows)

    assert (
        assembly._matching_indexed_locality_row(index, "BUND-S\u00d8", "denmark")
        is selected
    )
    assert assembly._matching_locality_row(rows, "BUND-S\u00d8", "denmark") is selected
    assert assembly._matching_indexed_locality_row(index, "None", "") is null_locality
    assert assembly._matching_locality_row(rows, "None", "") is null_locality
    assert assembly._matching_indexed_locality_row(index, "", "") is None
    assert assembly._matching_locality_row(rows, "", "") is None
    with pytest.raises(
        ValueError, match="Multiple site evidence rows match the same sample locality"
    ):
        assembly._matching_indexed_locality_row(index, "ignored_site", "SWEDEN")


def test_project_builder_prebuilds_each_evidence_index_once() -> None:
    site_rows = (SimpleNamespace(site_label="Site", political_entity="Country"),)
    provenance_rows = (
        SimpleNamespace(locality_text="Site", political_entity="Country"),
    )

    with (
        patch.object(assembly, "build_project_sample_master_rows", return_value=()),
        patch.object(assembly, "resolve_project_site_evidence", return_value=site_rows),
        patch.object(
            assembly,
            "resolve_project_coordinate_provenance",
            return_value=provenance_rows,
        ),
        patch.object(assembly, "_project_hierarchy_profiles", return_value={}),
        patch.object(
            assembly,
            "_LocalityRowIndex",
            wraps=assembly._LocalityRowIndex,
        ) as index_factory,
    ):
        assert assembly.build_project_sample_site_rows(Path("unused"), "PROJECT") == ()

    assert [call.args for call in index_factory.call_args_list] == [
        (site_rows,),
        (provenance_rows,),
    ]


def test_index_reads_each_evidence_locality_once_across_many_lookups() -> None:
    locality_reads = 0

    class CountingRow:
        political_entity = "Country"

        def __init__(self, index: int) -> None:
            self.index = index

        @property
        def site_label(self) -> str:
            nonlocal locality_reads
            locality_reads += 1
            return f"Site {self.index}"

    rows = tuple(CountingRow(index) for index in range(200))
    index = assembly._LocalityRowIndex(rows)

    for lookup in range(400):
        expected = rows[lookup % len(rows)]
        assert (
            assembly._matching_indexed_locality_row(
                index,
                f"site-{expected.index}",
                "COUNTRY",
            )
            is expected
        )

    assert locality_reads == len(rows)
