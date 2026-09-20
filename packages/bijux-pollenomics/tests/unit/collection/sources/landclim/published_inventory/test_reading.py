from __future__ import annotations

from decimal import Decimal
import hashlib
import inspect

import pytest

from bijux_pollenomics.collection.sources.landclim.published_inventory import (
    LandClimPublishedEstimateInventory,
    LandClimPublishedInventoryRefusal,
    read_landclim_published_inventory,
    reopen_landclim_published_inventory,
)
from bijux_pollenomics.collection.sources.landclim.published_inventory.reading import (
    _read_landclim_published_inventory,
)

from .support import RAW_ROOT, source_path

RECEIPT_SHA256 = "eb4350724c176d0dbcb7e441f2d21489bdae1cfff7ebe3088eab27093f315677"
ARCHIVE_SHA256 = "c585f0691ad95342b8aba083b90fe91dc398f985b6b7fbc19561299389c4fb86"


@pytest.fixture(scope="module")
def inventory() -> LandClimPublishedEstimateInventory:
    """Read the exact pinned archive once for this focused test module."""
    return read_landclim_published_inventory(RAW_ROOT)


def test_exact_published_archive_has_complete_paired_denominators(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    assert inventory.receipt_sha256 == RECEIPT_SHA256
    assert inventory.archive_sha256 == ARCHIVE_SHA256
    assert inventory.dataset_doi == "https://doi.org/10.1594/PANGAEA.937075"
    assert len(inventory.time_windows) == 25
    assert len(inventory.variables) == inventory.expected_variable_count == 47
    assert inventory.record_count == inventory.expected_record_count == 10500
    assert inventory.value_pair_count == inventory.expected_value_pair_count == 493500
    assert inventory.coordinate_available_record_count == 10350
    assert inventory.coordinate_refused_record_count == 150
    assert inventory.mean_zero_value_count == 251123
    assert inventory.mean_above_one_value_count == 138862
    assert inventory.mean_negative_value_count == 3
    assert inventory.mean_negative_record_count == 2
    assert len(inventory.sha256) == 64


def test_inventory_is_explicitly_published_output_not_reproduction_or_truth(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    assert inventory.evidence_role == "published_reconstruction_comparison_target"
    assert inventory.value_unit == "percentage_cover"
    assert inventory.published_products_only is True
    assert inventory.raw_pollen_inputs_authenticated is False
    assert inventory.historical_chronologies_authenticated is False
    assert inventory.original_r_execution is False
    assert inventory.pft_discrepancy_resolved is False
    assert inventory.published_product_rights == "not_evaluated"
    assert inventory.independent_measured_vegetation is False
    assert inventory.whole_paper_reproduction_certified is False
    assert inventory.publication_allowed is False
    assert inventory.scientifically_accepted is False
    assert inventory.scientific_acceptance == "not_evaluated"
    assert "ISTS" in inventory.variables


def test_every_source_token_survives_decimal_typing_without_clipping(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    negative: list[tuple[str, str, str]] = []
    zero_count = 0
    above_one_count = 0
    for record in inventory.records:
        assert len(record.estimates) == 47
        assert record.evidence_role == inventory.evidence_role
        assert record.value_unit == inventory.value_unit
        for estimate in record.estimates:
            assert Decimal(estimate.mean_token) == estimate.mean
            assert Decimal(estimate.standard_error_token) == estimate.standard_error
            assert estimate.standard_error >= 0
            zero_count += int(estimate.mean == 0)
            above_one_count += int(estimate.mean > 1)
            if estimate.mean < 0:
                negative.append(
                    (record.time_window, record.cell_id, estimate.mean_token)
                )
    assert zero_count == 251123
    assert above_one_count == 138862
    assert len(negative) == 3
    assert len({item[:2] for item in negative}) == 2
    assert all(Decimal(item[2]) < 0 for item in negative)


def test_missing_published_coordinates_are_retained_as_explicit_refusals(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    refused = [
        record for record in inventory.records if record.coordinate_status == "refused"
    ]
    assert len(refused) == 150
    assert len({record.cell_id for record in refused}) == 6
    assert all(record.mean_longitude_token == "#N/A" for record in refused)
    assert all(record.mean_latitude_token == "#N/A" for record in refused)
    assert all(record.standard_error_longitude_token == "#N/A" for record in refused)
    assert all(record.standard_error_latitude_token == "#N/A" for record in refused)
    assert all(
        record.longitude is None and record.latitude is None for record in refused
    )
    assert all(
        record.coordinate_refusal_reason == "published_coordinates_missing"
        for record in refused
    )
    available = next(
        record
        for record in inventory.records
        if record.coordinate_status == "available"
    )
    assert available.longitude is not None and available.latitude is not None
    assert available.coordinate_refusal_reason is None


def test_order_and_source_locators_remain_source_owned(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    first = inventory.records[0]
    last = inventory.records[-1]
    assert first.time_window == "0-100 BP"
    assert last.time_window == "11200-11700 BP"
    assert first.mean_cell_id_token == first.cell_id
    assert first.standard_error_cell_id_token == first.cell_id
    assert first.mean_source_locator.startswith(
        "landclim_ii_reveals_results.zip#LANDCLIMII.RV.means.JUN2021/"
    )
    assert first.standard_error_source_locator.startswith(
        "landclim_ii_reveals_results.zip#LANDCLIMII.RV.standarderrors.JUN2021/"
    )
    assert "!row=" in first.mean_source_locator
    assert "!row=" in last.standard_error_source_locator


def test_public_reader_accepts_no_caller_identity_or_claim_override() -> None:
    assert tuple(inspect.signature(read_landclim_published_inventory).parameters) == (
        "raw_dir",
    )
    assert (
        hashlib.sha256(source_path("landclim_sources.json").read_bytes()).hexdigest()
        == RECEIPT_SHA256
    )
    assert (
        hashlib.sha256(
            source_path("landclim_ii_reveals_results.zip").read_bytes()
        ).hexdigest()
        == ARCHIVE_SHA256
    )


def test_canonical_reopen_reconstructs_from_the_same_raw_closure(
    inventory: LandClimPublishedEstimateInventory,
) -> None:
    reopened = reopen_landclim_published_inventory(inventory.canonical_bytes, RAW_ROOT)
    assert reopened == inventory
    assert reopened.canonical_bytes == inventory.canonical_bytes


@pytest.mark.parametrize(
    "payload",
    [b"{}", b"", bytearray(b"{}")],
    ids=["different-bytes", "empty-bytes", "mutable-not-exact-bytes"],
)
def test_canonical_reopen_refuses_nonidentical_or_nonexact_bytes(
    payload: object,
) -> None:
    with pytest.raises(LandClimPublishedInventoryRefusal):
        reopen_landclim_published_inventory(payload, RAW_ROOT)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("receipt_sha256", "archive_sha256"),
    [("f" * 64, ARCHIVE_SHA256), (RECEIPT_SHA256, "f" * 64)],
    ids=["receipt", "archive"],
)
def test_source_substitution_is_refused_before_inventory_admission(
    receipt_sha256: str, archive_sha256: str
) -> None:
    with pytest.raises(LandClimPublishedInventoryRefusal):
        _read_landclim_published_inventory(
            RAW_ROOT,
            expected_receipt_sha256=receipt_sha256,
            expected_archive_sha256=archive_sha256,
        )


def test_direct_inventory_forgery_is_refused() -> None:
    with pytest.raises(LandClimPublishedInventoryRefusal):
        LandClimPublishedEstimateInventory(
            receipt_sha256=RECEIPT_SHA256,
            archive_sha256=ARCHIVE_SHA256,
            dataset_doi="https://doi.org/10.1594/PANGAEA.937075",
            time_windows=(),
            variables=(),
            records=(),
            coordinate_available_record_count=0,
            coordinate_refused_record_count=0,
            mean_zero_value_count=0,
            mean_above_one_value_count=0,
            mean_negative_value_count=0,
            mean_negative_record_count=0,
        )
