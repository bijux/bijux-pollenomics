"""Index only candidate discovery; retain the original matching predicate."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyMetadataInventory,
    StudyMetadataRecord,
)
from bijux_pollenomics.collection.sources.rootsi import RootsiSiteMetadataClaim
from bijux_pollenomics_dev.essd_reproduction import rootsi_input_closure as closure

from ..test_rootsi_input_closure import _publication, _rootsi, _synthetic_inputs


def _inputs(
    publications: list[StudyMetadataRecord], rootsi: list[RootsiSiteMetadataClaim]
) -> closure._Inputs:
    return closure._Inputs(
        publication=cast(
            LandClimStudyMetadataInventory,
            SimpleNamespace(records=tuple(publications)),
        ),
        rootsi=tuple(rootsi),
        typed_manifest={},
        typed_manifest_bytes=b"",
        typed_accounting={},
        typed_workbooks={},
    )


def _full_scan(
    inputs: closure._Inputs,
) -> dict[int, tuple[tuple[closure._Candidate, ...], tuple[closure._Candidate, ...]]]:
    result: dict[
        int, tuple[tuple[closure._Candidate, ...], tuple[closure._Candidate, ...]]
    ] = {}
    for publication in inputs.publication.records:
        observed = tuple(
            candidate
            for rootsi in inputs.rootsi
            if (candidate := closure._match(rootsi, publication)) is not None
        )
        accepted_country = tuple(row for row in observed if row.country_agrees)
        rejected_country = tuple(row for row in observed if not row.country_agrees)
        result[publication.worksheet_row] = (accepted_country, rejected_country)
    return result


def test_candidate_union_preserves_reasons_country_and_original_order() -> None:
    rows = [
        _rootsi(99, sequence="SEQ", site="Áland", samples=7, workbook=None),
        _rootsi(2, sequence="other", site="Åland", samples=7, workbook=None),
        replace(
            _rootsi(1, sequence="SEQ", site="other", samples=7, workbook=None),
            sample_count_claim=None,
        ),
        replace(
            _rootsi(9, sequence="SEQ", site="other", samples=7, workbook=None),
            country_native="FIN",
        ),
    ]
    inputs = _inputs(
        [_publication(1, sequence="dir/seq", site="ALAND", samples=7)], rows
    )
    observed = closure._publication_matches(inputs)
    assert observed == _full_scan(inputs)
    accepted, rejected = observed[1]
    assert [row.rootsi.source_row_number for row in accepted] == [99, 2, 1]
    assert [row.rootsi.source_row_number for row in rejected] == [9]
    assert accepted[0].reasons == (
        "normalized_sequence_label",
        "normalized_site_name_and_exact_sample_count",
    )
    assert accepted[1].reasons == ("normalized_site_name_and_exact_sample_count",)
    assert accepted[2].sample_count_agrees is False


@pytest.mark.parametrize(
    ("raw", "matched"),
    [("7", True), ("07", False), ("7.0", False), (None, False), ("", False)],
)
def test_site_matching_keeps_exact_sample_text(raw: str | None, matched: bool) -> None:
    publication = _publication(1, sequence="unmatched", site="Same", samples=7)
    publication = replace(
        publication,
        values=tuple(
            replace(value, raw=raw) if value.column == "nPollenSamples" else value
            for value in publication.values
        ),
    )
    inputs = _inputs(
        [publication],
        [_rootsi(2, sequence="different", site="Same", samples=7, workbook=None)],
    )
    actual = closure._publication_matches(inputs)
    assert actual == _full_scan(inputs)
    assert bool(actual[1][0]) is matched


@pytest.mark.parametrize("sample", [0, -1])
def test_empty_normalized_keys_and_duplicate_source_rows_remain_distinct(
    sample: int,
) -> None:
    root = _rootsi(2, sequence="--", site="", samples=sample, workbook=None)
    publication = _publication(1, sequence="", site="--", samples=sample)
    publication = replace(
        publication,
        values=tuple(
            replace(value, raw="") if value.column == "csvfilename" else value
            for value in publication.values
        ),
    )
    inputs = _inputs([publication], [root, root])
    actual = closure._publication_matches(inputs)
    assert actual == _full_scan(inputs)
    assert len(actual[1][0]) == 2
    assert actual[1][0][0].reasons == (
        "normalized_sequence_label",
        "normalized_site_name_and_exact_sample_count",
    )


@pytest.mark.parametrize("column", ["csvfilename", "SiteName", "nPollenSamples"])
@pytest.mark.parametrize("change", ["missing", "duplicate"])
def test_unmatched_publication_still_validates_required_columns(
    column: str, change: str
) -> None:
    row = _publication(1, sequence="none", site="none", samples=7)
    values = tuple(value for value in row.values if value.column != column)
    if change == "duplicate":
        original = next(value for value in row.values if value.column == column)
        values += (original, original)
    malformed = replace(row, values=values)
    inputs = _inputs(
        [malformed],
        [_rootsi(2, sequence="other", site="other", samples=0, workbook=None)],
    )
    for match in (_full_scan, closure._publication_matches):
        with pytest.raises(closure.RootsiInputClosureError, match="lacks"):
            match(inputs)
    # The original empty-Rootsi route does not inspect malformed publication cells.
    empty = _inputs([malformed], [])
    assert closure._publication_matches(empty) == _full_scan(empty) == {1: ((), ())}


@pytest.mark.parametrize("matched", [False, True])
@pytest.mark.parametrize("country", ["SWE", "FIN"])
def test_country_validation_remains_lazy(matched: bool, country: str) -> None:
    row = _publication(
        1, sequence="same" if matched else "none", site="none", samples=7
    )
    row = replace(
        row, values=tuple(value for value in row.values if value.column != "Country")
    )
    root = replace(
        _rootsi(2, sequence="same", site="other", samples=0, workbook=None),
        country_native=country,
    )
    inputs = _inputs([row], [root])
    if matched and country == "SWE":
        for match in (_full_scan, closure._publication_matches):
            with pytest.raises(closure.RootsiInputClosureError, match="Country"):
                match(inputs)
    else:
        assert closure._publication_matches(inputs) == _full_scan(inputs)


def test_index_preserves_all_five_complete_synthetic_products(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    inputs = _synthetic_inputs()
    monkeypatch.setattr(closure, "_read_inputs", lambda *_args: inputs)
    monkeypatch.setattr(
        closure,
        "_EXPECTED_PAIR_IDENTITY_SHA256",
        closure._pair_identity_sha256(_full_scan(inputs)),
    )
    indexed = closure._publication_matches
    monkeypatch.setattr(closure, "_publication_matches", _full_scan)
    expected = closure.build_rootsi_input_closure(
        *[Path(name) for name in ("landclim", "rootsi", "cells")]
    )
    monkeypatch.setattr(closure, "_publication_matches", indexed)
    actual = closure.build_rootsi_input_closure(
        *[Path(name) for name in ("landclim", "rootsi", "cells")]
    )
    assert len(actual) == 5
    assert actual == expected
