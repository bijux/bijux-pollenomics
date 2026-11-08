"""Keep native record sets distinct from combined authors and biological admission."""

from __future__ import annotations

from dataclasses import fields, replace
from hashlib import sha256
import json
from typing import Any

import pytest

from bijux_pollenomics.adna.governance.atlas_candidates.validation import (
    _project_sample_animal_scope_resolution_for,
)
from bijux_pollenomics.adna.projects.evidence.chronology.resolution import (
    _artifact_kind_from_path as chronology_kind,
)
from bijux_pollenomics.adna.projects.registry.samples import AdnaCuratedSampleRow
from bijux_pollenomics.adna.projects.registry.sites.evidence import (
    _artifact_kind_from_path as locality_kind,
)
from bijux_pollenomics.adna.projects.sample_master.archive import _project_by_accession
from bijux_pollenomics.adna.projects.sample_master.models import (
    AdnaProjectSampleMasterRow,
)
from bijux_pollenomics.adna.projects.sample_master.tables import _read_xlsx_rows
from bijux_pollenomics.adna.projects.sample_master.tables import (
    goat_imputation as source,
)
from bijux_pollenomics.adna.species.definitions import resolve_species_definition
from bijux_pollenomics.adna.workflow.normalization.samples import (
    _sample_record_is_admissible,
)
from bijux_pollenomics.adna.workflow.source_artifacts import read_source_artifact_text
from bijux_pollenomics.reporting.adna.sample_chronology_context.repository import (
    _refusal_reason,
)
from tests.support.repository import REPOSITORY_ROOT


@pytest.fixture
def context() -> bytes:
    return (REPOSITORY_ROOT / source.GOAT_NATIVE_CONTEXT).read_bytes()


def original_table(context: bytes) -> tuple[tuple[str, ...], ...]:
    workbook = json.loads(context)["workbook"]
    return _read_xlsx_rows(
        REPOSITORY_ROOT / workbook["path"], sheet_name=workbook["sheet"]
    )


@pytest.fixture
def rows(context: bytes) -> tuple[AdnaProjectSampleMasterRow, ...]:
    workbook = json.loads(context)["workbook"]
    table = original_table(context)
    projected = source._build_goat_imputation_rows(
        species=resolve_species_definition("Capra hircus"),
        project=_project_by_accession("PRJEB90141"),
        source_path=workbook["path"],
        rows=table,
    )
    archive = (
        "data/adna/governance/source_library/projects/PRJEB90141/archive_metadata.html"
    )
    return source._qualify_goat_imputation_rows(
        rows=projected,
        table_rows=table,
        archive_text=read_source_artifact_text(REPOSITORY_ROOT / archive),
        archive_source_path=archive,
    )


def bind(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> tuple[AdnaProjectSampleMasterRow, ...]:
    workbook = json.loads(context)["workbook"]
    return source._bind_goat_comparator_native_context(
        rows,
        context=context,
        workbook_sha256=sha256(
            (REPOSITORY_ROOT / workbook["path"]).read_bytes()
        ).hexdigest(),
        table_rows=original_table(context),
    )


def qualified_fixture(
    document: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> bytes:
    """Model another reviewed context to challenge record-set semantics, not raw truth."""
    body = json.dumps(document).encode()
    monkeypatch.setattr(source, "_NATIVE_CONTEXT_SHA256", sha256(body).hexdigest())
    return body


def test_native_assertions_preserve_every_selected_field_and_owner(
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
        assert {k: v for k, v in before.as_dict().items() if k not in changed} == {
            k: v for k, v in after.as_dict().items() if k not in changed
        }
        assert source.GOAT_NATIVE_CONTEXT in after.sample_lineage_path
        assert after.sample_identity_resolution == "ambiguous"
        assert after.source_native_identity_kind == "supplementary_sample_label"
        assert chronology_kind(after.sample_lineage_path) == chronology_kind(
            before.sample_lineage_path
        )
        assert locality_kind(after.sample_lineage_path) == locality_kind(
            before.sample_lineage_path
        )
        if after.preferred_sample_label == "Direkli1-2":
            assert after.source_native_tax_id == "9923"
            assert after.source_native_scientific_name == "Capra aegagrus"
            assert after.taxon_alignment_status == "project_species_mismatch"
            assert (
                after.archive_native_sample_id
                == before.archive_native_sample_id
                == "SAMEA4453841"
            )
            for value in [
                "SAMEA4453841 / ERS2404573",
                "SAMEA4453842 / ERS2404574",
                "TCD_Direkli1",
                "TCD_Direkli2",
                "SAMEA4453841; SAMEA4453842",
                "Direkli1-2",
            ]:
                assert value in after.sample_ambiguity_note
        else:
            assert after.source_native_tax_id == "9925"
            assert after.source_native_scientific_name == "Capra hircus"
            assert after.taxon_alignment_status == "project_species_match"


def test_literal_taxon_comparison_does_not_admit_identity_chronology_or_atlas_scope(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    def scope(row: AdnaProjectSampleMasterRow) -> tuple[str | None, str | None]:
        return _project_sample_animal_scope_resolution_for(
            REPOSITORY_ROOT / "data/adna/species/capra_hircus",
            {"PRJEB90141": "domesticated_core"},
            project_accessions=("PRJEB90141",),
            sample_rows=(row.as_dict(),),
        )

    for before, after in zip(rows, bind(rows, context), strict=True):
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
            assert (
                _refusal_reason(master.as_dict(), {}, {}) == "sample_identity_not_final"
            )
        assert scope(before) == scope(after)


def test_conflicting_second_native_assertion_is_not_replaced_by_first(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = json.loads(context)
    second = next(
        record["native"]
        for record in document["native_records"]
        if record["native"]["accession"] == "SAMEA4453842"
    )
    second.update(taxon_id="9925", scientific_name="Capra hircus")
    result = bind(rows, qualified_fixture(document, monkeypatch))
    pooled = next(row for row in result if row.preferred_sample_label == "Direkli1-2")
    assert pooled.taxon_alignment_status == "archive_taxon_conflict"
    assert set(pooled.source_native_tax_id.split(" || ")) == {"9923", "9925"}
    assert set(pooled.source_native_scientific_name.split(" || ")) == {
        "Capra aegagrus",
        "Capra hircus",
    }
    assert pooled.sample_identity_resolution == "ambiguous"
    assert (
        "SAMEA4453841" in pooled.sample_ambiguity_note
        and "SAMEA4453842" in pooled.sample_ambiguity_note
    )


def test_native_record_order_does_not_select_a_different_assertion(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = bind(rows, context)
    document = json.loads(context)
    document["native_records"].reverse()
    document["benchmarks"].reverse()
    assert bind(rows, qualified_fixture(document, monkeypatch)) == original


@pytest.mark.parametrize(
    "change", ["duplicate", "missing_second", "orphan", "swapped_source_accessions"]
)
def test_missing_duplicated_or_swapped_native_binding_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    document = json.loads(context)
    if change == "duplicate":
        document["native_records"].append(document["native_records"][0])
    elif change == "missing_second":
        document["native_records"] = [
            record
            for record in document["native_records"]
            if record["native"]["accession"] != "SAMEA4453842"
        ]
    elif change == "orphan":
        record = json.loads(json.dumps(document["native_records"][0]))
        record["native"].update(
            accession="SAMEA999999",
            primary_id="SAMEA999999",
            biosample_id="SAMEA999999",
        )
        document["native_records"].append(record)
    else:
        left, right = document["benchmarks"][1], document["benchmarks"][2]
        for field in ["native_accessions", "accession_cell"]:
            left[field], right[field] = right[field], left[field]
    with pytest.raises(ValueError):
        bind(rows, qualified_fixture(document, monkeypatch))


def test_changed_native_context_refuses_even_equivalent_json(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    with pytest.raises(ValueError, match="native source context changed"):
        bind(rows, context + b" ")


def test_changed_original_workbook_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    with pytest.raises(ValueError, match="supplementary source changed"):
        source._bind_goat_comparator_native_context(
            rows,
            context=context,
            workbook_sha256="0" * 64,
            table_rows=original_table(context),
        )


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


def test_missing_or_duplicated_author_owner_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    owner = rows[0]
    for altered in [tuple(row for row in rows if row is not owner), (*rows, owner)]:
        with pytest.raises(ValueError, match="one owner per author row"):
            bind(altered, context)


def test_current_run_associations_preserve_all_five_native_records(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    expected = {
        "Direkli1-2": (
            ("SAMEA4453841", "ERS2404573", 12),
            ("SAMEA4453842", "ERS2404574", 38),
        ),
        "Blagotin3": (("SAMEA4588077", "ERS2408800", 35),),
        "Acem2": (("SAMEA4591761", "ERS2412479", 20),),
        "Semnan3": (("SAMEA4591758", "ERS2412476", 38),),
    }
    for row in bind(rows, context):
        for primary, secondary, count in expected[row.preferred_sample_label]:
            assert (
                f"Current read_run capture for SAMPLE {primary} / {secondary} "
                f"reports PRJEB26011: {count} returned technical rows, {count} distinct run IDs "
                f"and {count} distinct experiment IDs"
            ) in row.sample_ambiguity_note
            assert primary in row.sample_lineage_locator
        assert (
            "not complete or historical study membership" in row.sample_ambiguity_note
        )
        assert row.project_accession == "PRJEB90141"
        assert row.sample_identity_resolution == "ambiguous"


def test_current_associations_change_only_saved_provenance_packets(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    saved = json.loads(
        (
            REPOSITORY_ROOT
            / "data/adna/governance/source_library/projects/PRJEB90141/sample_master.json"
        ).read_text()
    )
    original = {row["repo_stable_sample_id"]: row for row in saved["rows"]}
    changed = {
        "sample_lineage_locator",
        "sample_lineage_excerpt",
        "sample_ambiguity_note",
    }
    result = bind(rows, context)
    assert len(original) == len(result) == 4
    for row in result:
        before = original[row.repo_stable_sample_id]
        after = row.as_dict()
        assert {key: value for key, value in before.items() if key not in changed} == {
            key: value for key, value in after.items() if key not in changed
        }
        assert before["sample_ambiguity_note"] in row.sample_ambiguity_note


@pytest.mark.parametrize(
    "field", ["observed_sample_accession", "query_secondary_accession"]
)
def test_wrong_current_run_sample_association_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    document = json.loads(context)
    left, right = document["native_records"][:2]
    left["current_run_associations"][field] = right["current_run_associations"][field]
    with pytest.raises(ValueError, match="run association sample binding differs"):
        bind(rows, qualified_fixture(document, monkeypatch))


def test_current_associations_retain_multiple_studies_and_technical_multiplicity(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = json.loads(context)
    record = next(
        record
        for record in document["native_records"]
        if record["native"]["accession"] == "SAMEA4588077"
    )
    studies = record["current_run_associations"]["study_associations"]
    studies.append(
        {
            "study_accession": "PRJEB12345",
            "returned_row_count": 6,
            "distinct_run_count": 2,
            "distinct_experiment_count": 3,
        }
    )
    result = bind(rows, qualified_fixture(document, monkeypatch))
    blagotin = next(row for row in result if row.preferred_sample_label == "Blagotin3")
    assert "PRJEB26011: 35 returned technical rows" in blagotin.sample_ambiguity_note
    assert (
        "PRJEB12345: 6 returned technical rows, 2 distinct run IDs and 3 distinct experiment IDs"
    ) in blagotin.sample_ambiguity_note
    assert blagotin.sample_identity_resolution == "ambiguous"
    assert blagotin.project_accession == "PRJEB90141"
    studies.reverse()
    document["native_records"].reverse()
    document["benchmarks"].reverse()
    assert bind(rows, qualified_fixture(document, monkeypatch)) == result


def test_native_project_assertion_is_attributed_once_to_the_matched_direkli_pair(
    rows: tuple[AdnaProjectSampleMasterRow, ...], context: bytes
) -> None:
    result = bind(rows, context)
    assertion = "reports Direkli1 and 2 as identified from the same individual"
    for row in result:
        assert row.sample_identity_resolution == "ambiguous"
        assert row.project_accession == "PRJEB90141"
        if row.preferred_sample_label == "Direkli1-2":
            assert row.sample_ambiguity_note.count(assertion) == 1
            for literal in [
                "PRJEB26011 / ERP107983",
                "PubMed 29976826",
                "same PCR reactions",
                "not a selected physical-specimen identity",
            ]:
                assert literal in row.sample_ambiguity_note
            assert all(
                accession in row.sample_ambiguity_note
                for accession in ["SAMEA4453841", "SAMEA4453842"]
            )
        else:
            assert assertion not in row.sample_ambiguity_note
            assert "native PROJECT PRJEB26011" not in row.sample_ambiguity_note


@pytest.mark.parametrize("accession", ["SAMEA4453841", "SAMEA4453842", "both"])
def test_native_study_assertion_requires_both_current_study_matches(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
    accession: str,
) -> None:
    document = json.loads(context)
    for record in document["native_records"]:
        primary = record["native"]["primary_id"]
        if (
            primary == accession
            or accession == "both"
            and primary in {"SAMEA4453841", "SAMEA4453842"}
        ):
            groups = record["current_run_associations"]["study_associations"]
            groups[0]["study_accession"] = "PRJEB12345"
            groups.append({**groups[0], "study_accession": "PRJEB56789"})
    result = bind(rows, qualified_fixture(document, monkeypatch))
    row = next(row for row in result if row.preferred_sample_label == "Direkli1-2")
    assert "native PROJECT PRJEB26011" not in row.sample_ambiguity_note
    assert (
        "PRJEB12345" in row.sample_ambiguity_note
        and "PRJEB56789" in row.sample_ambiguity_note
    )
    assert row.sample_identity_resolution == "ambiguous"


def test_native_study_match_is_not_selected_from_first_group_or_record(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = json.loads(context)
    for record in document["native_records"]:
        if record["native"]["primary_id"] in {"SAMEA4453841", "SAMEA4453842"}:
            groups = record["current_run_associations"]["study_associations"]
            groups.insert(0, {**groups[0], "study_accession": "PRJEB12345"})
    result = bind(rows, qualified_fixture(document, monkeypatch))
    row = next(row for row in result if row.preferred_sample_label == "Direkli1-2")
    assert (
        row.sample_ambiguity_note.count(
            "reports Direkli1 and 2 as identified from the same individual"
        )
        == 1
    )
    document["native_study_context"]["direkli_assertion"]["native_records"].reverse()
    document["native_records"].reverse()
    for record in document["native_records"]:
        record["current_run_associations"]["study_associations"].reverse()
    assert bind(rows, qualified_fixture(document, monkeypatch)) == result


@pytest.mark.parametrize(
    "field,value",
    [
        ("primary_id", "SAMEA4588077"),
        ("secondary_id", "ERS2408800"),
        ("title", "Blagotin3"),
        ("alias", "TCD_Blagotin3"),
    ],
)
def test_malformed_direkli_study_correspondence_refuses(
    rows: tuple[AdnaProjectSampleMasterRow, ...],
    context: bytes,
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: str,
) -> None:
    document = json.loads(context)
    document["native_study_context"]["direkli_assertion"]["native_records"][0][
        field
    ] = value
    with pytest.raises(ValueError, match="native study assertion binding differs"):
        bind(rows, qualified_fixture(document, monkeypatch))
