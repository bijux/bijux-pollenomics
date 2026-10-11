from __future__ import annotations

import hashlib
import inspect

import pytest

from bijux_pollenomics.collection.sources.landclim.study_inventory import (
    LandClimStudyInventoryRefusal,
    LandClimStudyMetadataInventory,
    read_landclim_study_inventory,
    reopen_landclim_study_inventory,
)
from bijux_pollenomics.collection.sources.landclim.study_inventory.reading import (
    _inventory_from_rows,
    _read_landclim_study_inventory,
)

from .support import RAW_ROOT, cell, rows, source_path

RECEIPT_SHA256 = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
WORKBOOK_SHA256 = "2d4a0cf1401e36c2606f7761cecc85c4bbc15272460c2a4926cb1702d4565ebb"


def _from_rows(source_rows: list[list[str]]) -> LandClimStudyMetadataInventory:
    return _inventory_from_rows(
        source_rows,
        receipt_sha256=RECEIPT_SHA256,
        workbook_sha256=WORKBOOK_SHA256,
    )


def test_exact_governed_workbook_builds_refusal_only_inventory() -> None:
    product = read_landclim_study_inventory(RAW_ROOT)
    assert product.metadata_record_count == product.expected_record_count == 1128
    assert product.records[0].worksheet_row == 2
    assert product.records[-1].worksheet_row == 1129
    assert product.records[0].source_locator == (
        "landclim_ii_site_metadata.xlsx#LANDCLIMII metadata file!2"
    )
    assert len(product.header) == 44
    assert product.receipt_sha256 == RECEIPT_SHA256
    assert product.workbook_sha256 == WORKBOOK_SHA256
    assert product.dataset_doi == "https://doi.org/10.1594/PANGAEA.937075"
    assert product.publication_metadata_only is True
    assert product.raw_pollen_counts_authenticated is False
    assert product.historical_chronologies_authenticated is False
    assert product.per_sequence_rights_cleared is False
    assert product.reproduction_input_complete is False
    assert product.publication_allowed is False
    assert product.scientifically_accepted is False
    assert product.scientific_acceptance == "not_evaluated"
    assert len(product.sha256) == 64
    assert product.payload()["denominators"] == {
        "expected_study_records": 1128,
        "publication_metadata_records": 1128,
        "authenticated_primary_pollen_count_records": 0,
        "authenticated_historical_chronology_records": 0,
        "rights_cleared_records": 0,
    }


def test_public_reader_has_no_caller_supplied_identity_or_schema() -> None:
    assert tuple(inspect.signature(read_landclim_study_inventory).parameters) == (
        "raw_dir",
    )
    assert (
        hashlib.sha256(source_path("landclim_sources.json").read_bytes()).hexdigest()
        == RECEIPT_SHA256
    )
    assert (
        hashlib.sha256(
            source_path("landclim_ii_site_metadata.xlsx").read_bytes()
        ).hexdigest()
        == WORKBOOK_SHA256
    )


def test_canonical_reopen_reconstructs_from_the_same_raw_closure() -> None:
    product = read_landclim_study_inventory(RAW_ROOT)
    reopened = reopen_landclim_study_inventory(product.canonical_bytes, RAW_ROOT)
    assert reopened == product
    assert reopened.canonical_bytes == product.canonical_bytes


@pytest.mark.parametrize(
    "payload",
    [b"{}", b"", bytearray(b"{}")],
    ids=["different-bytes", "empty-bytes", "bytes-subclass-or-mutable"],
)
def test_canonical_reopen_refuses_nonidentical_or_nonexact_bytes(
    payload: object,
) -> None:
    with pytest.raises(LandClimStudyInventoryRefusal):
        reopen_landclim_study_inventory(payload, RAW_ROOT)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("receipt_sha256", "workbook_sha256"),
    [("f" * 64, WORKBOOK_SHA256), (RECEIPT_SHA256, "f" * 64)],
    ids=["receipt", "workbook"],
)
def test_changed_source_identity_is_refused_before_parsing(
    receipt_sha256: str, workbook_sha256: str
) -> None:
    with pytest.raises(LandClimStudyInventoryRefusal):
        _read_landclim_study_inventory(
            RAW_ROOT,
            expected_receipt_sha256=receipt_sha256,
            expected_workbook_sha256=workbook_sha256,
        )


def test_null_and_zero_are_distinct_and_raw_spelling_is_retained() -> None:
    product = _from_rows(rows())
    missing = cell(product.records[5], "Elevation")
    zero = cell(product.records[215], "Elevation")
    longitude = cell(product.records[0], "londd")
    assert (missing.kind, missing.raw, missing.number) == ("null", None, None)
    assert (zero.kind, zero.raw, str(zero.number)) == ("number", "0", "0")
    assert (longitude.kind, longitude.raw, str(longitude.number)) == (
        "number",
        "25.77",
        "25.77",
    )


def test_duplicate_source_content_is_retained_without_inferred_sample_ids() -> None:
    source_rows = rows()
    source_rows[2] = list(source_rows[1])
    product = _from_rows(source_rows)
    assert product.records[0].values == product.records[1].values
    assert product.records[0].source_locator != product.records[1].source_locator
    assert product.records[0].primary_pollen_count_identity is None
    assert product.records[0].chronology_input_identity is None


@pytest.mark.parametrize("change", ["header", "missing-row", "extra-row", "short-row"])
def test_shape_and_denominator_mutations_are_refused(change: str) -> None:
    source_rows = rows()
    if change == "header":
        source_rows[0][0] = "site_name"
    elif change == "missing-row":
        source_rows.pop()
    elif change == "extra-row":
        source_rows.append(list(source_rows[-1]))
    else:
        source_rows[1].pop()
    with pytest.raises(LandClimStudyInventoryRefusal):
        _from_rows(source_rows)


@pytest.mark.parametrize(
    ("column", "value"),
    [("londd", "181"), ("latdd", "-91"), ("latdd", "unknown")],
)
def test_rehashed_coordinate_or_type_mutations_are_refused(
    column: str, value: str
) -> None:
    source_rows = rows()
    source_rows[1][source_rows[0].index(column)] = value
    with pytest.raises(LandClimStudyInventoryRefusal):
        _from_rows(source_rows)


def test_direct_product_forgery_is_refused() -> None:
    with pytest.raises(LandClimStudyInventoryRefusal):
        LandClimStudyMetadataInventory(
            receipt_sha256=RECEIPT_SHA256,
            workbook_sha256=WORKBOOK_SHA256,
            dataset_doi="https://doi.org/10.1594/PANGAEA.937075",
            sheet_name="LANDCLIMII metadata file",
            header=(),
            records=(),
        )
