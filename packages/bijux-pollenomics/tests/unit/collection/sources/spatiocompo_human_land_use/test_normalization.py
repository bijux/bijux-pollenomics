from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use import (
    intake,
)
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.authority import (
    FILE_AUTHORITIES,
    KNOWN_REFUSED_RELATIVE_PATH,
    SOURCE_DIRECTORY,
)
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.intake import (
    normalize_spatiocompo_human_land_use,
)
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.models import (
    ExportFileAuthority,
)
from bijux_pollenomics.collection.sources.spatiocompo_human_land_use.normalization import (
    normalize_export_file,
)

from .support import fixture_authority, fixture_payload


def _available_authority():  # type: ignore[no-untyped-def]
    return next(
        authority
        for authority in FILE_AUTHORITIES
        if authority.upstream_status == "available"
    )


def _write_fixture(
    path: Path,
    *,
    first_values: tuple[str, ...] = (
        "0.18",
        "0.27",
        "0.55",
        "0.2",
        "0.3",
        "0.5",
        "0.1",
    ),
    malformed_first_row: bool = False,
    duplicate_second_coordinate: bool = False,
):  # type: ignore[no-untyped-def]
    authority = _available_authority()
    payload = fixture_payload(
        authority,
        first_values=first_values,
        malformed_first_row=malformed_first_row,
        duplicate_second_coordinate=duplicate_second_coordinate,
    )
    path.write_bytes(payload)
    return fixture_authority(authority, payload)


def _write_collection_fixture(source_root: Path) -> list[ExportFileAuthority]:
    fixture_authorities = []
    for authority in FILE_AUTHORITIES:
        payload = fixture_payload(authority)
        source_path = source_root / authority.relative_path
        source_path.parent.mkdir(parents=True, exist_ok=True)
        source_path.write_bytes(payload)
        fixture_authorities.append(
            fixture_authority(
                authority,
                payload,
                upstream_status=authority.upstream_status,
            )
        )
    return fixture_authorities


def test_valid_export_retains_model_semantics_and_context_only_posture(
    tmp_path: Path,
) -> None:
    path = tmp_path / "source.csv"
    authority = _write_fixture(path)

    source_slice = normalize_export_file(path, authority)

    assert source_slice.row_count == 679
    assert len(source_slice.coordinate_grid_sha256) == 64
    cell = source_slice.cells[0]
    assert cell.model_variant == "all"
    assert cell.period_label == "4000 BCE"
    assert cell.lcc_coniferous_proportion == Decimal("0.18")
    assert cell.human_land_use_proportion == Decimal("0.1")
    assert cell.uncertainty_status == "not_supplied_in_export"
    assert cell.evidence_role == "context_only"
    assert cell.time_start_bp is None and cell.time_end_bp is None
    assert not cell.observed_pollen_use_allowed
    assert not cell.propagation_use_allowed
    assert not cell.interpolation_allowed
    assert not cell.public_release_allowed


def test_export_identity_and_exact_header_are_required(tmp_path: Path) -> None:
    path = tmp_path / "source.csv"
    authority = _write_fixture(path)
    payload = path.read_bytes()

    replacement = b"0" if payload[-2:-1] != b"0" else b"1"
    path.write_bytes(payload[:-2] + replacement + b"\n")
    with pytest.raises(IntakeRefusal, match="spatiocompo_digest_mismatch"):
        normalize_export_file(path, authority)

    invalid_header_payload = payload.replace(b"Lon,Lat,", b"longitude,Lat,", 1)
    path.write_bytes(invalid_header_payload)
    invalid_header_authority = fixture_authority(authority, invalid_header_payload)
    with pytest.raises(IntakeRefusal, match="spatiocompo_header_mismatch"):
        normalize_export_file(path, invalid_header_authority)


@pytest.mark.parametrize(
    ("first_values", "reason"),
    (
        (
            ("NaN", "0.27", "0.55", "0.2", "0.3", "0.5", "0.1"),
            "invalid_spatiocompo_decimal",
        ),
        (
            ("1.2", "0.0", "-0.2", "0.2", "0.3", "0.5", "0.1"),
            "invalid_spatiocompo_proportion",
        ),
        (
            ("0.19", "0.27", "0.55", "0.2", "0.3", "0.5", "0.1"),
            "invalid_spatiocompo_lcc_composition",
        ),
        (
            ("0.19", "0.26", "0.55", "0.2", "0.3", "0.5", "0.1"),
            "invalid_spatiocompo_land_use_equation",
        ),
    ),
)
def test_invalid_scientific_values_are_refused(
    tmp_path: Path, first_values: tuple[str, ...], reason: str
) -> None:
    path = tmp_path / "source.csv"
    authority = _write_fixture(path, first_values=first_values)

    with pytest.raises(IntakeRefusal, match=reason):
        normalize_export_file(path, authority)


def test_malformed_rows_duplicate_coordinates_and_grid_drift_are_refused(
    tmp_path: Path,
) -> None:
    malformed_path = tmp_path / "malformed.csv"
    malformed = _write_fixture(malformed_path, malformed_first_row=True)
    with pytest.raises(IntakeRefusal, match="spatiocompo_column_count_mismatch"):
        normalize_export_file(malformed_path, malformed)

    duplicate_path = tmp_path / "duplicate.csv"
    duplicate = _write_fixture(duplicate_path, duplicate_second_coordinate=True)
    with pytest.raises(IntakeRefusal, match="duplicate_spatiocompo_coordinate"):
        normalize_export_file(duplicate_path, duplicate)

    valid_path = tmp_path / "valid.csv"
    valid = _write_fixture(valid_path)
    with pytest.raises(IntakeRefusal, match="spatiocompo_coordinate_grid_mismatch"):
        normalize_export_file(
            valid_path,
            valid,
            expected_grid=frozenset({(Decimal(0), Decimal(0))}),
        )


def test_known_corrupt_slice_is_refused_without_variant_substitution(
    tmp_path: Path,
) -> None:
    authority = next(
        source
        for source in FILE_AUTHORITIES
        if source.relative_path == KNOWN_REFUSED_RELATIVE_PATH
    )
    payload = fixture_payload(authority)
    authority = fixture_authority(
        authority, payload, upstream_status="known_corrupt_refused"
    )
    path = tmp_path / "source.csv"
    path.write_bytes(payload)

    with pytest.raises(IntakeRefusal, match="437 valid rows, 1 malformed row"):
        normalize_export_file(path, authority)


def test_full_collection_keeps_variants_separate_and_records_one_refusal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixture_authorities = _write_collection_fixture(tmp_path)
    monkeypatch.setattr(intake, "FILE_AUTHORITIES", tuple(fixture_authorities))

    collection = normalize_spatiocompo_human_land_use(tmp_path)

    assert collection.periods_oldest_to_present == (
        "4000 BCE",
        "1000 BCE",
        "1425 CE",
        "1725 CE",
        "1900 CE",
    )
    assert len(collection.slices) == 9
    assert collection.admitted_row_count == 9 * 679
    assert len(collection.refusals) == 1
    refusal = collection.refusals[0]
    assert refusal.model_variant == "all"
    assert refusal.period_key == "1000_bce"
    assert refusal.reason_code == "upstream_spatiocompo_slice_known_corrupt"
    assert not refusal.substitute_variant_allowed
    assert {
        (source_slice.authority.variant.key, source_slice.authority.period.key)
        for source_slice in collection.slices
    } >= {("elevation", "1000_bce"), ("all", "4000_bce")}
    assert not collection.propagation_use_allowed
    assert not collection.interpolation_allowed
    assert not collection.public_release_allowed


@pytest.mark.parametrize(
    ("failure", "reason"),
    (
        ("digest", "spatiocompo_digest_mismatch"),
        ("size", "spatiocompo_size_mismatch"),
        ("symlink", "missing_or_unsafe_spatiocompo_export"),
        ("header", "spatiocompo_header_mismatch"),
    ),
)
def test_corrupt_slice_path_does_not_mask_identity_or_structure_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
    reason: str,
) -> None:
    fixture_authorities = _write_collection_fixture(tmp_path)
    corrupt_index = next(
        index
        for index, authority in enumerate(fixture_authorities)
        if authority.relative_path == KNOWN_REFUSED_RELATIVE_PATH
    )
    corrupt_authority = fixture_authorities[corrupt_index]
    corrupt_path = tmp_path / corrupt_authority.relative_path
    payload = corrupt_path.read_bytes()
    if failure == "digest":
        corrupt_path.write_bytes(b"X" + payload[1:])
    elif failure == "size":
        corrupt_path.write_bytes(payload + b"\n")
    elif failure == "symlink":
        replacement = tmp_path / "corrupt-slice-replacement.csv"
        replacement.write_bytes(payload)
        corrupt_path.unlink()
        corrupt_path.symlink_to(replacement)
    else:
        invalid_header_payload = payload.replace(b"Lon,Lat,", b"Xon,Lat,", 1)
        corrupt_path.write_bytes(invalid_header_payload)
        fixture_authorities[corrupt_index] = fixture_authority(
            corrupt_authority,
            invalid_header_payload,
            upstream_status="known_corrupt_refused",
        )
    monkeypatch.setattr(intake, "FILE_AUTHORITIES", tuple(fixture_authorities))

    with pytest.raises(IntakeRefusal, match=reason):
        normalize_spatiocompo_human_land_use(tmp_path)


def test_full_collection_requires_exact_ten_file_inventory(tmp_path: Path) -> None:
    (tmp_path / SOURCE_DIRECTORY).mkdir()

    with pytest.raises(IntakeRefusal, match="spatiocompo_export_inventory_mismatch"):
        normalize_spatiocompo_human_land_use(tmp_path)


def test_full_collection_refuses_unlisted_non_csv_entries(tmp_path: Path) -> None:
    data_root = tmp_path / SOURCE_DIRECTORY
    data_root.mkdir()
    (data_root / "README.txt").write_text("not part of the pinned export set")

    with pytest.raises(IntakeRefusal, match="README.txt"):
        normalize_spatiocompo_human_land_use(tmp_path)
