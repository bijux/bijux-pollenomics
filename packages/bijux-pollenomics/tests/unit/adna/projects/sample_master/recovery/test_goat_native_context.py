"""Native record assertions must preserve unresolved specimen and selected fields."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _artifact_kind_from_path as chronology_kind,
)
from bijux_pollenomics.adna.projects.registry.sites.evidence import (
    _artifact_kind_from_path as locality_kind,
)

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.tables.goat_imputation import (
    GOAT_NATIVE_CONTEXT,
    _bind_blagotin_native_context,
)
from tests.support.repository import REPOSITORY_ROOT


@pytest.fixture
def context() -> bytes:
    return (REPOSITORY_ROOT / GOAT_NATIVE_CONTEXT).read_bytes()


@pytest.fixture
def rows() -> tuple[AdnaProjectSampleMasterRow, ...]:
    document = json.loads(
        (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects/PRJEB90141/sample_master.json"
        ).read_bytes()
    )
    return tuple(AdnaProjectSampleMasterRow(**row) for row in document["rows"])


def bind(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    workbook = json.loads(context)["workbook"]
    return _bind_blagotin_native_context(
        rows,
        context=context,
        workbook_sha256=sha256(
            (REPOSITORY_ROOT / workbook["path"]).read_bytes()
        ).hexdigest(),
    )


def test_native_correspondence_changes_only_one_owners_lineage(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    result = bind(rows, context)
    assert len(result) == len(rows) == 4
    changed = {
        "sample_lineage_path",
        "sample_lineage_locator",
        "sample_lineage_excerpt",
        "sample_ambiguity_note",
    }
    for before, after in zip(rows, result, strict=True):
        if before.preferred_sample_label != "Blagotin3":
            assert after == before
            continue
        assert {k: v for k, v in before.as_dict().items() if k not in changed} == {
            k: v for k, v in after.as_dict().items() if k not in changed
        }
        assert GOAT_NATIVE_CONTEXT in after.sample_lineage_path
        assert "SAMEA4588077 / ERS2408800" in after.sample_lineage_excerpt
        assert "TCD_Blagotin3" in after.sample_ambiguity_note
        assert "9925 / Capra hircus" in after.sample_ambiguity_note
        assert "Blagotin-Poljna, Serbia" in after.sample_ambiguity_note
        assert after.sample_identity_resolution == "ambiguous"
        assert after.source_native_identity_kind == "supplementary_sample_label"
        assert after.taxon_alignment_status == "not_reported"
        assert after.source_native_tax_id == after.source_native_scientific_name == ""
        assert chronology_kind(after.sample_lineage_path) == chronology_kind(
            before.sample_lineage_path
        )
        assert locality_kind(after.sample_lineage_path) == locality_kind(
            before.sample_lineage_path
        )


def test_changed_native_context_refuses_even_equivalent_json(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    with pytest.raises(ValueError, match="native source context changed"):
        bind(rows, context + b" ")


def test_changed_original_workbook_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    with pytest.raises(ValueError, match="supplementary source changed"):
        _bind_blagotin_native_context(rows, context=context, workbook_sha256="0" * 64)


@pytest.mark.parametrize(
    "change",
    [
        {"project_accession": "PRJEB1"},
        {"archive_native_sample_id": "SAMEA1"},
        {"paper_native_sample_label": "different"},
        {"sample_identity_resolution": "final"},
        {"source_native_identity_kind": "biological_sample_accession"},
        {"taxon_alignment_status": "project_species_match"},
        {"source_native_tax_id": "9925"},
    ],
)
def test_changed_or_promoted_owner_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes, change: dict[str, Any]
) -> None:
    altered = tuple(
        replace(row, **change) if row.preferred_sample_label == "Blagotin3" else row
        for row in rows
    )
    with pytest.raises(ValueError, match="owner or unselected scope changed"):
        bind(altered, context)


def test_missing_or_duplicated_owner_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    owner = next(row for row in rows if row.preferred_sample_label == "Blagotin3")
    for altered in [tuple(row for row in rows if row is not owner), (*rows, owner)]:
        with pytest.raises(ValueError, match="one supplementary owner"):
            bind(altered, context)
