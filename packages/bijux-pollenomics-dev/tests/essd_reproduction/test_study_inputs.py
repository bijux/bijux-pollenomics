"""Verify deterministic, metadata-only ESSD study-input products."""

from __future__ import annotations

import csv
import hashlib
import io
import json
from pathlib import Path
from typing import cast

import pytest

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    read_landclim_study_inventory,
)
from bijux_pollenomics_dev.essd_reproduction import study_inputs
from bijux_pollenomics_dev.essd_reproduction.study_inputs import (
    StudyInputProductError,
    build_study_input_products,
    main,
    publish_study_input_products,
    validate_study_input_products,
)

REPOSITORY = Path(__file__).resolve().parents[4]
RAW_DIR = REPOSITORY / "data/landclim/raw"
OUTPUT_NAMES = {
    "manifest.json",
    "records.jsonl",
    "primary-source-crosswalk.csv",
    "refusals.csv",
    "report.json",
}

JsonObject = dict[str, object]


def _object(content: bytes) -> JsonObject:
    value = json.loads(content)
    assert isinstance(value, dict)
    return cast(JsonObject, value)


def _objects(content: bytes) -> list[JsonObject]:
    rows: list[JsonObject] = []
    for line in content.splitlines():
        value = json.loads(line)
        assert isinstance(value, dict)
        rows.append(cast(JsonObject, value))
    return rows


def _csv(content: bytes) -> list[dict[str, str]]:
    return cast(
        list[dict[str, str]],
        list(csv.DictReader(io.StringIO(content.decode("utf-8")))),
    )


def _cell(record: JsonObject, column: str) -> JsonObject:
    values = cast(list[JsonObject], record["values"])
    matches = [value for value in values if value["column"] == column]
    assert len(matches) == 1
    return matches[0]


@pytest.fixture(scope="module")
def products() -> dict[str, bytes]:
    return build_study_input_products(RAW_DIR)


def test_bundle_has_exact_deterministic_inventory(
    products: dict[str, bytes],
) -> None:
    assert set(products) == OUTPUT_NAMES
    manifest = _object(products["manifest.json"])
    assert manifest["schema_version"] == "essd-study-input-metadata-manifest.v1"
    contract = cast(JsonObject, manifest["output_contract"])
    assert contract == {
        "output_file_count": 5,
        "publication_metadata_records": 1128,
        "crosswalk_ledger_records": 1128,
        "refusal_ledger_records": 4512,
        "csv_null_encoding": (
            "empty_field_only_with_an_explicit_status_or_source_raw_field"
        ),
    }
    artifacts = cast(list[JsonObject], manifest["artifacts"])
    assert [row["path"] for row in artifacts] == [
        "records.jsonl",
        "primary-source-crosswalk.csv",
        "refusals.csv",
        "report.json",
    ]
    for row in artifacts:
        name = cast(str, row["path"])
        assert row["byte_count"] == len(products[name])
        assert row["sha256"] == hashlib.sha256(products[name]).hexdigest()
    assert products == build_study_input_products(RAW_DIR)


def test_records_preserve_every_row_and_null_zero_spelling(
    products: dict[str, bytes],
) -> None:
    rows = _objects(products["records.jsonl"])
    assert len(rows) == 1128
    assert [row["worksheet_row"] for row in rows] == list(range(2, 1130))
    locators = [row["source_locator"] for row in rows]
    assert len(set(locators)) == 1128
    assert locators[0] == ("landclim_ii_site_metadata.xlsx#LANDCLIMII metadata file!2")
    missing = _cell(rows[5], "Elevation")
    zero = _cell(rows[215], "Elevation")
    longitude = _cell(rows[0], "londd")
    assert (missing["kind"], missing["raw"], missing["number"]) == (
        "null",
        None,
        None,
    )
    assert (zero["kind"], zero["raw"], zero["number"]) == (
        "number",
        "0",
        "0",
    )
    assert (longitude["raw"], longitude["number"]) == ("25.77", "25.77")
    assert all(row["primary_pollen_count_identity"] is None for row in rows)
    assert all(row["chronology_input_identity"] is None for row in rows)
    assert all(row["rights_status"] == "unresolved" for row in rows)


def test_crosswalk_is_one_to_one_and_never_invents_source_identity(
    products: dict[str, bytes],
) -> None:
    inventory = read_landclim_study_inventory(RAW_DIR)
    crosswalk = _csv(products["primary-source-crosswalk.csv"])
    assert len(crosswalk) == 1128
    assert [int(row["worksheet_row"]) for row in crosswalk] == list(range(2, 1130))
    first_values = {value.column: value.raw for value in inventory.records[0].values}
    first = crosswalk[0]
    assert first["publication_site_name_raw"] == first_values["SiteName"]
    assert first["publication_csvfilename_raw"] == first_values["csvfilename"]
    assert first["publication_country_raw"] == first_values["Country"]
    assert (
        first["publication_source_credit_raw"]
        == first_values["Database/Authorname and/or data collector"]
    )
    assert (
        first["publication_restriction_label_raw"]
        == first_values["DataRestricted/NotRestriced"]
    )
    assert all(row["historical_primary_input_identity"] == "" for row in crosswalk)
    assert all(row["current_revision_identity"] == "" for row in crosswalk)
    assert all(
        row["historical_primary_identity_status"] == "not_authenticated"
        for row in crosswalk
    )
    assert all(
        row["current_revision_identity_status"] == "not_evaluated" for row in crosswalk
    )
    assert all(row["crosswalk_status"] == "unresolved" for row in crosswalk)


def test_refusal_ledger_has_four_explicit_requirements_per_record(
    products: dict[str, bytes],
) -> None:
    rows = _csv(products["refusals.csv"])
    assert len(rows) == 4512
    expected_requirements = {
        "historical_primary_pollen_counts",
        "historical_chronology",
        "historical_current_revision_crosswalk",
        "per_sequence_rights",
    }
    assert {row["requirement"] for row in rows} == expected_requirements
    assert all(row["namespace"] == "essd-study-input-requirement.v1" for row in rows)
    for worksheet_row in range(2, 1130):
        retained = [row for row in rows if int(row["worksheet_row"]) == worksheet_row]
        assert len(retained) == 4
        assert {row["requirement"] for row in retained} == expected_requirements


def test_report_retains_zero_closure_and_all_prohibited_claims(
    products: dict[str, bytes],
) -> None:
    report = _object(products["report.json"])
    denominators = cast(JsonObject, report["denominators"])
    assert denominators == {
        "expected_study_records": 1128,
        "publication_metadata_records": 1128,
        "crosswalk_ledger_records": 1128,
        "refusal_ledger_records": 4512,
        "authenticated_primary_pollen_count_records": 0,
        "authenticated_historical_chronology_records": 0,
        "authenticated_historical_current_revision_matches": 0,
        "rights_cleared_records": 0,
        "reproduction_ready_records": 0,
    }
    claims = cast(JsonObject, report["claims"])
    assert claims.pop("scientific_acceptance") == "not_evaluated"
    assert claims and all(value is False for value in claims.values())
    label_counts = cast(JsonObject, report["source_label_denominators"])
    countries = cast(list[JsonObject], label_counts["publication_country_raw"])
    restrictions = cast(list[JsonObject], label_counts["publication_restriction_raw"])
    assert sum(cast(int, row["record_count"]) for row in countries) == 1128
    assert sum(cast(int, row["record_count"]) for row in restrictions) == 1128


def test_atomic_publication_validates_and_refuses_existing_or_symlink(
    tmp_path: Path,
) -> None:
    output = tmp_path / "study-inputs"
    manifest = publish_study_input_products(RAW_DIR, output)
    assert manifest["schema_version"] == "essd-study-input-metadata-manifest.v1"
    assert {path.name for path in output.iterdir()} == OUTPUT_NAMES
    assert set(validate_study_input_products(RAW_DIR, output)) == OUTPUT_NAMES
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_study_input_products(RAW_DIR, output)

    symlink = tmp_path / "symlink-output"
    symlink.symlink_to(tmp_path / "absent", target_is_directory=True)
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_study_input_products(RAW_DIR, symlink)

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(StudyInputProductError, match="symlinked ESSD output ancestor"):
        publish_study_input_products(RAW_DIR, linked_parent / "bundle")


def test_atomic_publication_rechecks_target_before_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output = tmp_path / "raced-output"
    original = study_inputs._validate_directory

    def inject_target(staged: Path, expected: dict[str, bytes]) -> dict[str, bytes]:
        validated = original(staged, expected)
        output.mkdir()
        return validated

    monkeypatch.setattr(study_inputs, "_validate_directory", inject_target)
    with pytest.raises(FileExistsError, match="Refusing to replace"):
        publish_study_input_products(RAW_DIR, output)
    assert output.is_dir()
    assert list(tmp_path.glob(".raced-output-*")) == []


def test_validator_refuses_coherent_generated_claim_rehash(
    products: dict[str, bytes], tmp_path: Path
) -> None:
    output = tmp_path / "coherently-rehashed"
    output.mkdir()
    for name, content in products.items():
        (output / name).write_bytes(content)
    report = _object((output / "report.json").read_bytes())
    claims = cast(JsonObject, report["claims"])
    claims["whole_paper_reproduction_certified"] = True
    changed_report = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    (output / "report.json").write_bytes(changed_report)
    manifest = _object((output / "manifest.json").read_bytes())
    artifacts = cast(list[JsonObject], manifest["artifacts"])
    report_entry = next(row for row in artifacts if row["path"] == "report.json")
    report_entry["byte_count"] = len(changed_report)
    report_entry["sha256"] = hashlib.sha256(changed_report).hexdigest()
    (output / "manifest.json").write_bytes(
        (
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
    )
    with pytest.raises(StudyInputProductError, match="does not match raw parents"):
        validate_study_input_products(RAW_DIR, output)


def test_direct_module_cli_publishes_the_same_bounded_product(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "cli-output"
    assert main(["--raw-dir", str(RAW_DIR), "--output", str(output)]) == 0
    receipt = json.loads(capsys.readouterr().out)
    assert receipt == {
        "output": str(output),
        "publication_metadata_records": 1128,
        "refusal_ledger_records": 4512,
        "whole_paper_reproduction_certified": False,
    }
    assert {path.name for path in output.iterdir()} == OUTPUT_NAMES
