"""Verify deterministic, refusal-bounded Rootsi input candidate closure."""

from __future__ import annotations

import csv
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyMetadataInventory,
    StudyMetadataRecord,
    StudyMetadataValue,
)
from bijux_pollenomics.collection.sources.rootsi import RootsiSiteMetadataClaim
from bijux_pollenomics_dev.essd_reproduction import rootsi_input_closure
from bijux_pollenomics_dev.essd_reproduction.rootsi_input_closure import (
    RootsiInputClosureError,
    build_rootsi_input_closure,
    main,
    publish_rootsi_input_closure,
    validate_rootsi_input_closure,
)

REPOSITORY = Path(__file__).resolve().parents[4]
LANDCLIM_RAW = REPOSITORY / "data/landclim/raw"
ROOTSI_METADATA = (
    REPOSITORY
    / "artifacts/v2/sources/remaining-frontier/rootsi-lineage/intake-001/metadata.xlsx"
)
TYPED_CELL_REVIEW = (
    REPOSITORY / "artifacts/v2/sources/rootsi-cell-preparation/actual-002/all-79"
)
REAL_PAIR_IDENTITY_SHA256 = (
    "ca94f04342f5c54212dc3ef9acfa0cbeea6e92419878f951ec23b2a0acf5cfd6"
)
OUTPUT_NAMES = {
    "manifest.json",
    "publication-candidates.jsonl",
    "rootsi-crosswalk.csv",
    "requirement-status.csv",
    "report.json",
}

JsonObject = dict[str, object]


def _object(content: bytes) -> JsonObject:
    value = json.loads(content)
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _objects(content: bytes) -> list[JsonObject]:
    result: list[JsonObject] = []
    for line in content.splitlines():
        value = json.loads(line)
        assert isinstance(value, dict)
        result.append(cast(JsonObject, value))
    return result


def _csv(content: bytes) -> list[dict[str, str]]:
    return cast(
        list[dict[str, str]],
        list(csv.DictReader(io.StringIO(content.decode("utf-8")))),
    )


def _publication_value(column: str, raw: str) -> StudyMetadataValue:
    return StudyMetadataValue(column=column, kind="text", raw=raw, number=None)


def _publication(
    worksheet_row: int,
    *,
    sequence: str,
    site: str,
    country: str = "Sweden",
    samples: int = 100,
) -> StudyMetadataRecord:
    values = (
        _publication_value("SiteName", site),
        _publication_value("csvfilename", f"{sequence}.csv"),
        _publication_value("Country", country),
        _publication_value("nPollenSamples", str(samples)),
        _publication_value("DataRestricted/NotRestriced", "NR"),
        _publication_value("Database/Authorname and/or data collector", "EPD"),
        _publication_value("chronologySource", "Authors chronology"),
    )
    return StudyMetadataRecord(
        worksheet_row=worksheet_row,
        source_locator=f"synthetic-landclim.xlsx#metadata!{worksheet_row}",
        values=values,
    )


def _rootsi(
    source_row: int,
    *,
    sequence: str,
    site: str,
    samples: int,
    workbook: str | None,
) -> RootsiSiteMetadataClaim:
    source_values = (
        ("Country", "SWE"),
        ("nr_samples", f"{samples}.0"),
        ("LatDD", f"{56 + source_row / 100:.2f}"),
        ("LongDD", f"{15 + source_row / 100:.2f}"),
        ("Site area (ha)", "1.5"),
        ("Site radius (m)", "50"),
        ("No. of dates1", "4"),
        ("Basin type", "small lake"),
    )
    return RootsiSiteMetadataClaim(
        source_row_number=source_row,
        country_native="SWE",
        site_name=site,
        site_id_native=f"site-{source_row}",
        record_id_native=f"record-{source_row}",
        sample_count_claim=samples,
        site_label=sequence,
        observation_workbook_claim=workbook,
        latitude_dms_claim=None,
        latitude_decimal_claim=None,
        longitude_dms_claim=None,
        longitude_decimal_claim=None,
        elevation_m_claim=None,
        site_area_ha_claim=None,
        site_radius_m_claim=None,
        date_count_claim="4",
        basin_type_claim="small lake",
        source_values=source_values,
        unsupported_values=(),
    )


def _synthetic_inputs() -> rootsi_input_closure._Inputs:
    rootsi: list[RootsiSiteMetadataClaim] = []
    publications: list[StudyMetadataRecord] = []

    for index in range(79):
        source_row = index + 2
        worksheet_row = index + 2
        sequence = "STE" if index == 0 else f"ROOT{index:03d}"
        site = f"Rootsi Site {index:03d}"
        samples = 1000 + index
        workbook = f"root-{index:03d}.xls"
        rootsi.append(
            _rootsi(
                source_row,
                sequence=sequence,
                site=site,
                samples=samples,
                workbook=workbook,
            )
        )
        if index < 60:
            publication_sequence = sequence
            publication_site = site
            publication_samples = samples
        elif index < 62:
            publication_sequence = sequence
            publication_site = f"Publication-only Site {index:03d}"
            publication_samples = samples if index == 61 else samples + 1
        else:
            publication_sequence = f"PUBLICATION{index:03d}"
            publication_site = site
            publication_samples = samples
        publications.append(
            _publication(
                worksheet_row,
                sequence=publication_sequence,
                site=publication_site,
                samples=publication_samples,
            )
        )

    rootsi.extend(
        (
            _rootsi(
                81,
                sequence="ABO",
                site="Unmatched ABO",
                samples=1081,
                workbook=None,
            ),
            _rootsi(
                82,
                sequence="LIND",
                site="Unmatched LIND",
                samples=1082,
                workbook=None,
            ),
        )
    )

    # This row matches STE by label, but exact country policy rejects the pair.
    publications.append(
        _publication(
            81,
            sequence="STE",
            site="Country-disagreeing site",
            country="Germany",
            samples=9999,
        )
    )
    for worksheet_row in range(82, 1130):
        publications.append(
            _publication(
                worksheet_row,
                sequence=f"UNMATCHED{worksheet_row:04d}",
                site=f"Publication-only {worksheet_row:04d}",
                samples=20000 + worksheet_row,
            )
        )

    typed_rows = [
        {
            "archive_member": f"rootsi/root-{index:03d}.xls",
            "sha256": hashlib.sha256(f"workbook-{index}".encode()).hexdigest(),
            "bytes": 1000 + index,
        }
        for index in range(79)
    ]
    typed_manifest: JsonObject = {
        "schema": "quarantined-rootsi-cell-review.v1",
        "scientific_admission": "refused",
        "capture": {
            "scope": "complete_retained_capture",
            "archive_sha256": rootsi_input_closure.ARCHIVE_SHA256,
            "archive_membership_verification": ("retained_receipt_bound_not_replayed"),
            "selected_workbooks": typed_rows,
        },
    }
    typed_manifest_bytes = rootsi_input_closure._json_bytes(typed_manifest)
    publication_inventory = cast(
        LandClimStudyMetadataInventory,
        SimpleNamespace(
            records=tuple(publications),
            schema_version="landclim-study-metadata-inventory.v1",
            sha256="a" * 64,
            workbook_sha256="b" * 64,
            receipt_sha256="c" * 64,
        ),
    )
    return rootsi_input_closure._Inputs(
        publication=publication_inventory,
        rootsi=tuple(rootsi),
        typed_manifest=typed_manifest,
        typed_manifest_bytes=typed_manifest_bytes,
        typed_accounting={
            "workbooks": 79,
            "sheets": 107,
            "rectangle_positions": 547330,
            "scientifically_admitted_observations": 0,
        },
        typed_workbooks={
            cast(str, row["archive_member"]).casefold(): row for row in typed_rows
        },
    )


@pytest.fixture
def synthetic_inputs() -> rootsi_input_closure._Inputs:
    return _synthetic_inputs()


@pytest.fixture
def synthetic_pair_sha256(
    synthetic_inputs: rootsi_input_closure._Inputs,
) -> str:
    matches = rootsi_input_closure._publication_matches(synthetic_inputs)
    return rootsi_input_closure._pair_identity_sha256(matches)


@pytest.fixture
def configured_inputs(
    monkeypatch: pytest.MonkeyPatch,
    synthetic_inputs: rootsi_input_closure._Inputs,
    synthetic_pair_sha256: str,
) -> rootsi_input_closure._Inputs:
    monkeypatch.setattr(
        rootsi_input_closure,
        "_read_inputs",
        lambda *_args: synthetic_inputs,
    )
    monkeypatch.setattr(
        rootsi_input_closure,
        "_EXPECTED_PAIR_IDENTITY_SHA256",
        synthetic_pair_sha256,
    )
    return synthetic_inputs


@pytest.fixture
def products(
    configured_inputs: rootsi_input_closure._Inputs,
) -> dict[str, bytes]:
    return build_rootsi_input_closure(Path("landclim"), Path("rootsi"), Path("cells"))


def test_manifest_binds_all_three_sources_and_exact_outputs(
    products: dict[str, bytes], synthetic_pair_sha256: str
) -> None:
    assert set(products) == OUTPUT_NAMES
    manifest = _object(products["manifest.json"])
    assert manifest["schema_version"] == "essd-rootsi-input-closure-manifest.v1"
    sources = cast(JsonObject, manifest["sources"])
    publication = cast(JsonObject, sources["publication_inventory"])
    rootsi = cast(JsonObject, sources["rootsi_metadata"])
    cells = cast(JsonObject, sources["typed_cell_review"])
    assert publication["workbook_sha256"] == "b" * 64
    assert publication["records"] == 1128
    assert rootsi["archive_membership_verification"] == (
        "retained_receipt_bound_not_replayed"
    )
    assert rootsi["archive_replayed_by_closure"] is False
    assert rootsi["records"] == 81
    assert cells["archive_membership_verification"] == (
        "retained_receipt_bound_not_replayed"
    )
    assert cells["archive_replayed_by_closure"] is False
    assert cells["consumption"] == "validated_reference_without_copy"
    assert cells["scientific_admission"] == "refused"
    assert cells["workbooks"] == 79
    contract = cast(JsonObject, manifest["output_contract"])
    assert contract == {
        "csv_null_encoding": "empty_field_with_explicit_status_columns",
        "output_file_count": 5,
        "publication_candidate_records": 1128,
        "requirement_status_records": 6768,
        "rootsi_crosswalk_records": 81,
        "matching_profile": (
            "normalized-sequence-label-or-normalized-site-name-plus-exact-"
            "sample-count-with-exact-SWE-to-Sweden-country-filter.v1"
        ),
        "candidate_pair_identity_sha256": synthetic_pair_sha256,
    }
    artifacts = cast(list[JsonObject], manifest["artifacts"])
    assert [row["path"] for row in artifacts] == [
        "publication-candidates.jsonl",
        "rootsi-crosswalk.csv",
        "requirement-status.csv",
        "report.json",
    ]
    for row in artifacts:
        name = cast(str, row["path"])
        assert row["byte_count"] == len(products[name])
        assert row["sha256"] == hashlib.sha256(products[name]).hexdigest()


def test_publication_candidates_preserve_full_denominator_and_candidate_boundary(
    products: dict[str, bytes],
) -> None:
    rows = _objects(products["publication-candidates.jsonl"])
    assert len(rows) == 1128
    assert [row["publication_worksheet_row"] for row in rows] == list(range(2, 1130))
    statuses = [row["candidate_status"] for row in rows]
    assert statuses.count("unique_rootsi_metadata_candidate") == 79
    assert statuses.count("no_rootsi_metadata_candidate") == 1049
    assert statuses.count("ambiguous_rootsi_metadata_candidates") == 0
    assert all(row["authenticated_historical_primary_input"] is None for row in rows)
    assert all(row["reproduction_ready"] is False for row in rows)

    ste = next(row for row in rows if row["publication_worksheet_row"] == 2)
    candidates = cast(list[JsonObject], ste["metadata_candidates"])
    assert ste["publication_access_marker_raw"] == "NR"
    assert ste["publication_source_credit_raw"] == "EPD"
    assert ste["publication_chronology_source_raw"] == "Authors chronology"
    assert candidates[0]["rootsi_site_name_raw"] == "Rootsi Site 000"
    assert candidates[0]["rootsi_sample_count_raw"] == "1000.0"
    assert candidates[0]["rootsi_sample_count_claim"] == 1000
    assert candidates[0]["match_reasons"] == [
        "normalized_sequence_label",
        "normalized_site_name_and_exact_sample_count",
    ]
    assert candidates[0]["sample_count_agrees"] is True
    assert candidates[0]["historical_primary_input_identity_verified"] is False


def test_crosswalk_keeps_independent_match_signals_and_disagreements(
    products: dict[str, bytes],
) -> None:
    rows = _csv(products["rootsi-crosswalk.csv"])
    assert len(rows) == 81
    assert [int(row["rootsi_source_row"]) for row in rows] == list(range(2, 83))
    assert sum(bool(row["typed_workbook_member"]) for row in rows) == 79
    assert (
        sum(
            row["publication_candidate_status"] == "unique_rootsi_metadata_candidate"
            for row in rows
        )
        == 79
    )
    assert (
        sum(
            row["publication_candidate_status"] == "no_rootsi_metadata_candidate"
            for row in rows
        )
        == 2
    )
    assert all(
        row["historical_primary_input_identity_status"] == "not_authenticated"
        for row in rows
    )
    assert all(row["reproduction_ready"] == "false" for row in rows)

    sequence_only_mismatch = next(
        row for row in rows if row["rootsi_sequence_label_raw"] == "ROOT060"
    )
    assert json.loads(sequence_only_mismatch["match_reasons_json"]) == [
        ["normalized_sequence_label"]
    ]
    assert json.loads(sequence_only_mismatch["sample_count_agrees_json"]) == [False]

    sequence_only_agreement = next(
        row for row in rows if row["rootsi_sequence_label_raw"] == "ROOT061"
    )
    assert json.loads(sequence_only_agreement["match_reasons_json"]) == [
        ["normalized_sequence_label"]
    ]
    assert json.loads(sequence_only_agreement["sample_count_agrees_json"]) == [True]

    sten = next(row for row in rows if row["rootsi_sequence_label_raw"] == "STE")
    assert sten["rootsi_sample_count_raw"] == "1000.0"
    assert sten["rootsi_sample_count_claim"] == "1000"
    assert json.loads(sten["publication_candidate_rows_json"]) == [2]
    assert json.loads(sten["country_disagreeing_publication_rows_json"]) == [81]
    unmatched = {
        row["rootsi_sequence_label_raw"]
        for row in rows
        if row["publication_candidate_status"] == "no_rootsi_metadata_candidate"
    }
    assert unmatched == {"ABO", "LIND"}


def test_requirement_ledger_distinguishes_absent_candidates_from_refusals(
    products: dict[str, bytes],
) -> None:
    rows = _csv(products["requirement-status.csv"])
    assert len(rows) == 6768
    assert {row["requirement"] for row in rows} == {
        "historical_primary_pollen_counts",
        "historical_selected_chronology",
        "historical_current_revision_identity",
        "per_sequence_rights",
        "taxonomy_and_count_denominator",
        "basin_and_profile_semantics",
    }
    assert {row["state"] for row in rows} == {
        "not_applicable",
        "not_authenticated",
        "unresolved",
    }
    assert sum(row["state"] == "not_applicable" for row in rows) == 6294
    assert sum(row["state"] == "not_authenticated" for row in rows) == 237
    assert sum(row["state"] == "unresolved" for row in rows) == 237
    no_candidate = [
        row
        for row in rows
        if row["metadata_candidate_status"] == "no_rootsi_metadata_candidate"
    ]
    assert len(no_candidate) == 6294
    assert {row["reason_code"] for row in no_candidate} == {
        "no_rootsi_metadata_candidate"
    }
    assert all(row["namespace"] == "essd-rootsi-input-requirement.v1" for row in rows)


def test_report_records_exact_pair_identity_without_promoting_inputs(
    products: dict[str, bytes], synthetic_pair_sha256: str
) -> None:
    report = _object(products["report.json"])
    denominators = cast(JsonObject, report["denominators"])
    assert denominators["publication_rows_with_unique_metadata_candidate"] == 79
    assert denominators["publication_rows_without_rootsi_metadata_candidate"] == 1049
    assert denominators["rootsi_rows_with_unique_publication_candidate"] == 79
    assert denominators["rootsi_rows_without_publication_candidate"] == 2
    assert denominators["country_disagreeing_candidate_pairs_rejected"] == 1
    assert denominators["unique_candidate_sample_count_disagreements"] == 1
    assert denominators["applicable_requirement_status_records"] == 474
    assert denominators["not_applicable_requirement_status_records"] == 6294
    assert denominators["authenticated_historical_primary_input_records"] == 0
    assert denominators["reproduction_ready_records"] == 0
    assert report["candidate_evidence_pattern_counts"] == {
        "normalized_sequence_label": 2,
        "normalized_sequence_label+normalized_site_name_and_exact_sample_count": 60,
        "normalized_site_name_and_exact_sample_count": 17,
    }
    pair_identity = cast(JsonObject, report["pair_identity"])
    assert pair_identity["sha256"] == synthetic_pair_sha256
    assert pair_identity["accepted_pairs"] == 79
    assert pair_identity["country_rejected_pairs"] == 1
    scope = cast(JsonObject, report["scope"])
    assert scope["archive_membership_replayed"] is False
    assert scope["emitted_string_matching_fields_preserve_source_native_text"] is True
    assert scope["rootsi_sample_count_emission"] == (
        "raw_source_text_and_normalized_integer_claim_separate"
    )
    claims = cast(JsonObject, report["claims"])
    assert claims.pop("scientific_acceptance") == "not_evaluated"
    assert claims and all(value is False for value in claims.values())


def test_builder_is_byte_deterministic(products: dict[str, bytes]) -> None:
    assert products == build_rootsi_input_closure(
        Path("landclim"), Path("rootsi"), Path("cells")
    )


def test_pair_identity_change_refuses_even_when_aggregates_stay_constant(
    configured_inputs: rootsi_input_closure._Inputs,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second, *remaining = configured_inputs.rootsi
    swapped_first = replace(
        first,
        site_label=second.site_label,
        site_name=second.site_name,
        sample_count_claim=second.sample_count_claim,
    )
    swapped_second = replace(
        second,
        site_label=first.site_label,
        site_name=first.site_name,
        sample_count_claim=first.sample_count_claim,
    )
    changed = replace(
        configured_inputs,
        rootsi=(swapped_first, swapped_second, *remaining),
    )
    changed_report = rootsi_input_closure._report(
        changed, rootsi_input_closure._publication_matches(changed)
    )
    denominators = cast(JsonObject, changed_report["denominators"])
    assert denominators["publication_rows_with_unique_metadata_candidate"] == 79
    assert changed_report["candidate_evidence_pattern_counts"] == {
        "normalized_sequence_label": 2,
        "normalized_sequence_label+normalized_site_name_and_exact_sample_count": 60,
        "normalized_site_name_and_exact_sample_count": 17,
    }
    monkeypatch.setattr(rootsi_input_closure, "_read_inputs", lambda *_args: changed)
    with pytest.raises(RootsiInputClosureError, match="pair identity changed"):
        build_rootsi_input_closure(Path("landclim"), Path("rootsi"), Path("cells"))


def test_atomic_publication_and_exact_rebuild_validation(
    configured_inputs: rootsi_input_closure._Inputs, tmp_path: Path
) -> None:
    output = tmp_path / "closure"
    manifest = publish_rootsi_input_closure(
        Path("landclim"), Path("rootsi"), Path("cells"), output
    )
    assert manifest["schema_version"] == "essd-rootsi-input-closure-manifest.v1"
    assert {path.name for path in output.iterdir()} == OUTPUT_NAMES
    assert (
        set(
            validate_rootsi_input_closure(
                Path("landclim"), Path("rootsi"), Path("cells"), output
            )
        )
        == OUTPUT_NAMES
    )
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_rootsi_input_closure(
            Path("landclim"), Path("rootsi"), Path("cells"), output
        )


def test_atomic_publication_refuses_dangling_output_and_symlinked_parent(
    configured_inputs: rootsi_input_closure._Inputs, tmp_path: Path
) -> None:
    dangling = tmp_path / "dangling-output"
    dangling.symlink_to(tmp_path / "absent", target_is_directory=True)
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_rootsi_input_closure(
            Path("landclim"), Path("rootsi"), Path("cells"), dangling
        )

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(
        RootsiInputClosureError, match="symlinked closure output ancestor"
    ):
        publish_rootsi_input_closure(
            Path("landclim"), Path("rootsi"), Path("cells"), linked_parent / "bundle"
        )


def test_atomic_publication_rechecks_target_after_stage_validation(
    configured_inputs: rootsi_input_closure._Inputs,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    output = tmp_path / "raced-output"
    original = rootsi_input_closure._require_new_output
    calls = 0

    def inject_target(target: Path) -> None:
        nonlocal calls
        original(target)
        calls += 1
        if calls == 2:
            output.mkdir()

    monkeypatch.setattr(rootsi_input_closure, "_require_new_output", inject_target)
    with pytest.raises(FileExistsError):
        publish_rootsi_input_closure(
            Path("landclim"), Path("rootsi"), Path("cells"), output
        )
    assert calls == 2
    assert output.is_dir()
    assert list(tmp_path.glob(".raced-output-*")) == []


def test_validator_refuses_coherent_claim_rehash(
    configured_inputs: rootsi_input_closure._Inputs,
    products: dict[str, bytes],
    tmp_path: Path,
) -> None:
    output = tmp_path / "rehash"
    output.mkdir()
    for name, content in products.items():
        (output / name).write_bytes(content)
    report = _object((output / "report.json").read_bytes())
    claims = cast(JsonObject, report["claims"])
    claims["whole_paper_reproduction_certified"] = True
    changed = rootsi_input_closure._json_bytes(report)
    (output / "report.json").write_bytes(changed)
    manifest = _object((output / "manifest.json").read_bytes())
    artifacts = cast(list[JsonObject], manifest["artifacts"])
    report_entry = next(row for row in artifacts if row["path"] == "report.json")
    report_entry["byte_count"] = len(changed)
    report_entry["sha256"] = hashlib.sha256(changed).hexdigest()
    (output / "manifest.json").write_bytes(rootsi_input_closure._json_bytes(manifest))
    with pytest.raises(RootsiInputClosureError, match="authenticated parents"):
        validate_rootsi_input_closure(
            Path("landclim"), Path("rootsi"), Path("cells"), output
        )


def test_direct_module_cli_publishes_the_same_boundary(
    configured_inputs: rootsi_input_closure._Inputs,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "cli-output"
    assert (
        main(
            [
                "--landclim-raw-dir",
                "landclim",
                "--rootsi-metadata",
                "rootsi",
                "--typed-cell-review",
                "cells",
                "--output",
                str(output),
            ]
        )
        == 0
    )
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {
        "output": str(output),
        "publication_candidate_records": 1128,
        "rootsi_crosswalk_records": 81,
        "reproduction_ready_records": 0,
        "whole_paper_reproduction_certified": False,
    }


@pytest.mark.skipif(
    not (
        LANDCLIM_RAW.is_dir()
        and ROOTSI_METADATA.is_file()
        and TYPED_CELL_REVIEW.is_dir()
    ),
    reason="private Rootsi closure inputs are absent",
)
def test_private_inputs_retain_pinned_real_pair_identity() -> None:
    products = build_rootsi_input_closure(
        LANDCLIM_RAW, ROOTSI_METADATA, TYPED_CELL_REVIEW
    )
    report = _object(products["report.json"])
    pair_identity = cast(JsonObject, report["pair_identity"])
    assert pair_identity["sha256"] == REAL_PAIR_IDENTITY_SHA256
