"""Native record assertions must preserve unresolved specimen and selected fields."""

from __future__ import annotations

from dataclasses import fields, replace
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
from bijux_pollenomics.adna.projects.registry.samples import AdnaCuratedSampleRow
from bijux_pollenomics.adna.governance.atlas_candidates.validation import (
    _project_sample_animal_scope_resolution_for,
)
from bijux_pollenomics.adna.projects.sample_master.archive import _project_by_accession
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.species.definitions import resolve_species_definition
from bijux_pollenomics.adna.workflow.normalization.samples import (
    _sample_record_is_admissible,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text
from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    _refusal_reason,
)

from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.tables.goat_imputation import (
    GOAT_NATIVE_CONTEXT,
    _bind_blagotin_native_context,
    _build_goat_imputation_rows,
    _qualify_goat_imputation_rows,
)
from tests.support.repository import REPOSITORY_ROOT


@pytest.fixture
def context() -> bytes:
    return (REPOSITORY_ROOT / GOAT_NATIVE_CONTEXT).read_bytes()


@pytest.fixture
def rows() -> tuple[AdnaProjectSampleMasterRow, ...]:
    context = json.loads((REPOSITORY_ROOT / GOAT_NATIVE_CONTEXT).read_bytes())
    workbook = context["workbook"]
    table = _read_xlsx_rows(
        REPOSITORY_ROOT / workbook["path"], sheet_name=workbook["sheet"]
    )
    projected = _build_goat_imputation_rows(
        species=resolve_species_definition("Capra hircus"),
        project=_project_by_accession("PRJEB90141"),
        source_path=workbook["path"],
        rows=table,
    )
    archive = (
        "data/adna/governance/source_library/projects/PRJEB90141/archive_metadata.html"
    )
    return _qualify_goat_imputation_rows(
        rows=projected,
        table_rows=table,
        archive_text=read_source_artifact_text(REPOSITORY_ROOT / archive),
        archive_source_path=archive,
    )


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
        "source_native_tax_id",
        "source_native_scientific_name",
        "taxon_alignment_status",
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
        assert after.taxon_alignment_status == "project_species_match"
        assert after.source_native_tax_id == "9925"
        assert after.source_native_scientific_name == "Capra hircus"
        assert chronology_kind(after.sample_lineage_path) == chronology_kind(
            before.sample_lineage_path
        )
        assert locality_kind(after.sample_lineage_path) == locality_kind(
            before.sample_lineage_path
        )


def test_name_agreement_does_not_admit_ambiguous_biological_sample_or_chronology(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    before = next(row for row in rows if row.preferred_sample_label == "Blagotin3")
    after = next(
        row for row in bind(rows, context) if row.preferred_sample_label == "Blagotin3"
    )
    for master in (before, after):
        values: dict[str, Any] = {
            field.name: "" for field in fields(AdnaCuratedSampleRow)
        }
        values.update(
            {key: value for key, value in master.as_dict().items() if key in values}
        )
        values.update(
            stable_sample_id=master.repo_stable_sample_id,
            time_start_bp=None,
            time_end_bp=None,
        )
        assert not _sample_record_is_admissible(AdnaCuratedSampleRow(**values))
        assert _refusal_reason(master.as_dict(), {}, {}) == "sample_identity_not_final"

    def scope(row: AdnaProjectSampleMasterRow) -> tuple[str | None, str | None]:
        return _project_sample_animal_scope_resolution_for(
            REPOSITORY_ROOT / "data/adna/species/capra_hircus",
            {"PRJEB90141": "domesticated_core"},
            project_accessions=("PRJEB90141",),
            sample_rows=(row.as_dict(),),
        )

    assert scope(before) == scope(after)


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
