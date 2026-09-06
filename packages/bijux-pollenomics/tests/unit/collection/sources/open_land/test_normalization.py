from __future__ import annotations

import hashlib
from decimal import Decimal
from pathlib import Path
from zipfile import ZipFile

import pytest
from bijux_pollenomics.collection.sources.open_land import normalization
from bijux_pollenomics.collection.sources.open_land.authority import (
    SOURCE_CITATION_DOI,
    SOURCE_DATA_LICENSE,
    SOURCE_INTERVAL_BY_SLICE_BP,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal

_HEADER = "Lon,Lat,C_KK10LonLatElev,B_KK10LonLatElev,U_KK10LonLatElev"


def _archive(tmp_path: Path, rows: list[str], *, header: str = _HEADER) -> Path:
    path = tmp_path / "open-land.zip"
    body = "\n".join(rows)
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "LandCover_OpenLand/Data/Land_Cover_50.csv",
            f"{header}\n{body}\n",
        )
    return path


def _grid_digest(coordinates: list[tuple[str, str]]) -> str:
    content = "".join(
        f"{Decimal(longitude).normalize()}\t{Decimal(latitude).normalize()}\n"
        for longitude, latitude in sorted(
            (Decimal(longitude), Decimal(latitude))
            for longitude, latitude in coordinates
        )
    ).encode("ascii")
    return hashlib.sha256(content).hexdigest()


def bind_fixture_archive(
    path: Path,
    monkeypatch: pytest.MonkeyPatch,
    *,
    coordinates: list[tuple[str, str]],
) -> None:
    with ZipFile(path) as archive:
        members = archive.infolist()
        expanded_bytes = sum(member.file_size for member in members)
    archive_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
    monkeypatch.setattr(normalization, "ARCHIVE_SHA256", archive_sha256)
    monkeypatch.setattr(normalization, "ARCHIVE_MEMBER_COUNT", len(members))
    monkeypatch.setattr(normalization, "ARCHIVE_EXPANDED_BYTES", expanded_bytes)
    monkeypatch.setattr(normalization, "MODELED_CELL_COUNT", len(coordinates))
    monkeypatch.setattr(normalization, "SOURCE_TIME_SLICES_BP", (50,))
    monkeypatch.setattr(normalization, "SOURCE_INTERVAL_BY_SLICE_BP", {50: (0, 100)})
    monkeypatch.setattr(
        normalization, "SOURCE_ROW_COUNT_BY_SLICE_BP", {50: len(coordinates)}
    )
    monkeypatch.setattr(
        normalization,
        "SOURCE_GRID_SHA256_BY_SLICE_BP",
        {50: _grid_digest(coordinates)},
    )
    monkeypatch.setattr(
        normalization,
        "ADMITTED_CSV_MEMBERS",
        (normalization.csv_member_path(50),),
    )


def test_source_interval_is_modeled_context_and_preserves_numeric_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0,0.3,0.7"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])

    cell = tuple(normalization.iter_modeled_land_cover(path))[0]

    assert (cell.younger_bp, cell.older_bp) == (0, 100)
    assert cell.time_slice_bp == 50
    assert cell.temporal_extent_kind == "source_published_interval"
    assert cell.age_system == "calibrated_bp"
    assert cell.age_reference_epoch_ce == 1950
    assert cell.chronology_status == "source_published_calibrated_bp_interval"
    assert cell.coniferous_proportion == Decimal(0)
    assert cell.as_dict()["coniferous_proportion"] == "0"
    assert cell.spatial_interpolation_status == "source_model_is_spatially_interpolated"
    assert not cell.added_spatial_interpolation
    assert not cell.added_temporal_interpolation
    assert cell.propagation_eligibility == "context_only"
    assert not cell.public_release_allowed
    assert not cell.propagation_use_allowed
    assert len(cell.source_member_sha256) == 64
    assert cell.source_archive_sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
    assert "independent_release_review_required" in cell.refusal_reasons


@pytest.mark.parametrize(
    ("composition", "reason"),
    (
        (("0.2", "0.3", "0.4"), "invalid_modeled_composition"),
        (("-0.1", "0.6", "0.5"), "invalid_modeled_proportion"),
        (("NaN", "0.5", "0.5"), "invalid_open_land_decimal"),
    ),
)
def test_invalid_scientific_values_are_refused(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    composition: tuple[str, str, str],
    reason: str,
) -> None:
    path = _archive(tmp_path, [f"12.5,55.5,{','.join(composition)}"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])

    with pytest.raises(IntakeRefusal, match=reason):
        tuple(normalization.iter_modeled_land_cover(path))


def test_duplicate_coordinates_are_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(
        tmp_path,
        ["12.5,55.5,0.2,0.3,0.5", "12.50,55.50,0.1,0.4,0.5"],
    )
    bind_fixture_archive(
        path,
        monkeypatch,
        coordinates=[("12.5", "55.5"), ("12.5", "55.5")],
    )

    with pytest.raises(IntakeRefusal, match="duplicate_open_land_coordinate"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_extra_csv_value_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0.2,0.3,0.5,unexpected"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])

    with pytest.raises(IntakeRefusal, match="open_land_row_width_mismatch"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_undeclared_csv_member_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0.2,0.3,0.5"])
    with ZipFile(path, "a") as archive:
        archive.writestr(
            "LandCover_OpenLand/Data/unexpected.csv",
            f"{_HEADER}\n13,56,0.2,0.3,0.5\n",
        )
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])

    with pytest.raises(IntakeRefusal, match="open_land_csv_inventory_mismatch"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_reordered_csv_header_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(
        tmp_path,
        ["55.5,12.5,0.2,0.3,0.5"],
        header="Lat,Lon,C_KK10LonLatElev,B_KK10LonLatElev,U_KK10LonLatElev",
    )
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])

    with pytest.raises(IntakeRefusal, match="open_land_header_mismatch"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_slice_row_count_mismatch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0.2,0.3,0.5"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])
    monkeypatch.setattr(normalization, "SOURCE_ROW_COUNT_BY_SLICE_BP", {50: 2})

    with pytest.raises(IntakeRefusal, match="open_land_slice_row_count_mismatch"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_slice_grid_mismatch_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0.2,0.3,0.5"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])
    monkeypatch.setattr(normalization, "SOURCE_GRID_SHA256_BY_SLICE_BP", {50: "0" * 64})

    with pytest.raises(IntakeRefusal, match="open_land_coordinate_grid_mismatch"):
        tuple(normalization.iter_modeled_land_cover(path))


def test_archive_symlink_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ["12.5,55.5,0.2,0.3,0.5"])
    bind_fixture_archive(path, monkeypatch, coordinates=[("12.5", "55.5")])
    link = tmp_path / "linked.zip"
    link.symlink_to(path)

    with pytest.raises(IntakeRefusal, match="open_land_archive_symlink"):
        tuple(normalization.iter_modeled_land_cover(link))


def test_source_time_windows_are_exact_and_irregular() -> None:
    assert SOURCE_INTERVAL_BY_SLICE_BP[50] == (0, 100)
    assert SOURCE_INTERVAL_BY_SLICE_BP[225] == (100, 350)
    assert SOURCE_INTERVAL_BY_SLICE_BP[550] == (350, 700)
    assert SOURCE_INTERVAL_BY_SLICE_BP[1000] == (700, 1200)
    assert SOURCE_INTERVAL_BY_SLICE_BP[1500] == (1200, 1700)
    assert len(SOURCE_INTERVAL_BY_SLICE_BP) == 25
    assert sum(normalization.SOURCE_ROW_COUNT_BY_SLICE_BP.values()) == 45_212
    assert set(normalization.SOURCE_GRID_SHA256_BY_SLICE_BP) == set(
        SOURCE_INTERVAL_BY_SLICE_BP
    )
    assert SOURCE_CITATION_DOI == "https://doi.org/10.3389/fevo.2022.795794"
    assert SOURCE_DATA_LICENSE == "CC-BY-SA-4.0"
