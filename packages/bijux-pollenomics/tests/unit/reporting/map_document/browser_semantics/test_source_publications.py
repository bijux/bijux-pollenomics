"""Real compact source projections expose later citations without approval claims."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest

from ..evidence_projection.test_neotoma_publications import (
    capture as capture,
)
from ..evidence_projection.test_neotoma_publications import (
    projected,
    publication,
    save_capture,
)
from ..evidence_projection.test_neotoma_publications import (
    source as source,
)
from .test_native_source_context import observe, parse_html


def test_native_citation_fields_and_later_capture_are_readable_and_escaped(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
) -> None:
    record = projected(source, capture).detail_records[0]
    tabs = record["tabs"]
    output = observe(tabs)
    html = output["provenance"]
    document = parse_html(html)
    assert "Original &lt;literal&gt; citation" in html
    assert "Native title" in html and "Native" in html and "Author" in html
    assert "1994" in html and "Provider primary flag" in html
    assert "neotoma:dataset:201, publication 501" in html
    assert "2026-09-29T02:41:47.238255+00:00" in html
    assert "captured separately from the original pollen snapshot" in html
    assert "source designation only" in html and "No reviewed citation choice" in html
    assert "full-paper access" in html and "rights decision" in html
    assert not document.findall(".//literal")
    assert all(
        link.attrib["href"].startswith("https://api.neotomadb.org/v2.0/data/downloads/")
        for link in document.findall(".//a")
    )
    assert 'data-detail-table-page="provenance.publications"' in html
    assert 'data-detail-table-page="provenance.publication_datasets"' in html
    assert output["unchanged"]


def test_full_native_tables_are_reused_by_reference_without_source_mutation(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
) -> None:
    tabs = projected(source, capture).detail_records[0]["tabs"]
    before = deepcopy(tabs)
    output = observe(
        tabs,
        "(()=>{const render=renderDetailTable,calls=[];renderDetailTable=(table,path)=>{if(path.startsWith('provenance.publication'))calls.push({path,same:table===(path==='provenance.publications'?tabs.provenance.publication_capture.publications:tabs.provenance.publication_capture.datasets)});return render(table,path);};renderSourceProvenanceContext(tabs);renderDetailTable=render;return calls;})()",
    )
    assert output["extra"] == [
        {"path": "provenance.publication_datasets", "same": True},
        {"path": "provenance.publications", "same": True},
    ]
    assert tabs == before and output["unchanged"]


@pytest.mark.parametrize(
    "state", ["unconfigured", "uncovered", "empty", "null", "multiple"]
)
def test_absent_capture_missing_relation_and_nullable_alternatives_remain_distinct(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    state: str,
) -> None:
    rows = [] if state == "empty" else [publication(201, 20, 501, None)]
    if state == "multiple":
        rows = [publication(201, 20, 501, True), publication(201, 20, 502, True)]
    capture = save_capture(
        tmp_path / "packet", {} if state == "uncovered" else {201: rows}, monkeypatch
    )
    tabs = projected(
        source, None if state == "unconfigured" else capture
    ).detail_records[0]["tabs"]
    html = observe(tabs)["provenance"]
    expected = {
        "unconfigured": "no separate publication capture is configured",
        "uncovered": "not_captured",
        "empty": "no_publication_link",
        "null": "no_source_primary_flag",
        "multiple": "multiple_source_primary_publications",
    }[state]
    assert expected in html
    if state == "null":
        assert "null (source null)" in html
    if state == "multiple":
        assert "publication 501" in html and "publication 502" in html
    assert (
        "accepted_scientific_classification_not_available" in observe(tabs)["accepted"]
    )


def test_malformed_capture_table_does_not_hide_original_dataset_context(
    source: tuple[Path, dict[str, Any], dict[str, Any]],
    capture: Path,
) -> None:
    tabs = projected(source, capture).detail_records[0]["tabs"]
    tabs["provenance"]["publication_capture"]["publications"]["record_count"] += 1
    output = observe(tabs)
    assert "cannot be decoded consistently" in output["provenance"]
    assert "Source dataset metadata" in output["provenance"]
    assert 'data-detail-table-page="provenance.datasets"' in output["provenance"]
    assert output["unchanged"]
