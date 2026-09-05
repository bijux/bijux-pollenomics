from __future__ import annotations

import json
import hashlib
from pathlib import Path
from zipfile import ZipFile

import pytest

from bijux_pollenomics.collection.sources.open_land import normalization
from bijux_pollenomics.collection.sources.open_land.authority import (
    SOURCE_CITATION_DOI,
    SOURCE_DATA_LICENSE,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal


def _archive(tmp_path: Path, composition: tuple[str, str, str]) -> Path:
    path = tmp_path / "open-land.zip"
    with ZipFile(path, "w") as archive:
        archive.writestr(
            "LandCover_OpenLand/Data/Land_Cover_50.csv",
            "Lon,Lat,C_KK10LonLatElev,B_KK10LonLatElev,U_KK10LonLatElev\n"
            f"12.5,55.5,{','.join(composition)}\n",
        )
    return path


def _bind_fixture_archive(
    path: Path, monkeypatch: pytest.MonkeyPatch, *, time_slice: int = 50
) -> None:
    with ZipFile(path) as archive:
        member = archive.infolist()[0]
        expanded_bytes = member.file_size
    monkeypatch.setattr(
        normalization, "ARCHIVE_SHA256", hashlib.sha256(path.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(normalization, "ARCHIVE_MEMBER_COUNT", 1)
    monkeypatch.setattr(normalization, "ARCHIVE_EXPANDED_BYTES", expanded_bytes)
    monkeypatch.setattr(normalization, "SOURCE_TIME_SLICES_BP", (time_slice,))
    monkeypatch.setattr(
        normalization,
        "ADMITTED_CSV_MEMBERS",
        (normalization.csv_member_path(time_slice),),
    )


def test_source_slice_is_modeled_context_and_not_publication_evidence(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = _archive(tmp_path, ("0.2", "0.3", "0.5"))
    _bind_fixture_archive(path, monkeypatch)

    cells = tuple(normalization.iter_modeled_land_cover(path))

    assert len(cells) == 1
    cell = cells[0]
    assert cell.time_slice_bp == 50
    assert cell.temporal_extent_kind == "source_point_slice"
    assert cell.source_age_label == "BP"
    assert cell.age_system is None
    assert cell.age_reference_epoch_ce is None
    assert cell.chronology_status == "source_native_bp_point_slice_unreviewed"
    assert cell.temporal_comparability == "unresolved"
    assert cell.propagation_eligibility == "context_only"
    assert cell.evidence_kind == "derived_modeled_land_cover"
    assert len(cell.source_member_sha256) == 64
    assert cell.source_repository == (
        "https://github.com/BehnazP/SpatioCompo_entireHolocene_EU"
    )
    assert cell.source_citation_doi == "https://doi.org/10.3389/fevo.2022.795794"
    assert cell.source_data_license == "CC-BY-SA-4.0"
    assert cell.licensing_status == (
        "upstream_license_verified_release_review_required"
    )
    assert cell.attribution_status == "required_not_materialized_for_public_release"
    assert cell.country_code is None
    assert cell.taxon_id is None
    assert cell.taxon_semantics == "not_applicable_land_cover_aggregate"
    assert cell.uncertainty is None
    assert cell.land_cover_uncertainty_status == "not_supplied"
    assert not cell.public_release_allowed
    assert not cell.propagation_use_allowed
    assert "uncertainty_surface_not_supplied" in cell.refusal_reasons
    assert json.dumps(cell.as_dict(), sort_keys=True, separators=(",", ":")) == (
        '{"age_reference_epoch_ce":null,"age_system":null,'
        '"attribution_status":"required_not_materialized_for_public_release",'
        '"broadleaved_proportion":"0.3",'
        '"chronology_status":"source_native_bp_point_slice_unreviewed",'
        '"coniferous_proportion":"0.2","country_code":null,'
        '"evidence_kind":"derived_modeled_land_cover",'
        '"land_cover_uncertainty_status":"not_supplied","latitude_claim":"55.5",'
        '"licensing_status":"upstream_license_verified_release_review_required",'
        '"longitude_claim":"12.5","propagation_eligibility":"context_only",'
        '"propagation_use_allowed":false,'
        '"public_release_allowed":false,"refusal_reasons":['
        '"country_boundary_join_required","chronology_conversion_not_reviewed",'
        '"uncertainty_surface_not_supplied",'
        '"human_licensing_review_required","scientific_model_review_required"],'
        '"source_age_label":"BP","source_archive_sha256":'
        '"7ed602f3b480a995cd2e1ff6dc445e994442100b1f626a953185849305e2434b",'
        '"source_citation_doi":"https://doi.org/10.3389/fevo.2022.795794",'
        '"source_commit":"894d44d58f66bb5c273491d98c3ec23a35e6a796",'
        '"source_data_license":"CC-BY-SA-4.0",'
        '"source_member":"LandCover_OpenLand/Data/Land_Cover_50.csv",'
        '"source_member_sha256":'
        '"1787889ab078c6d832584c0d09c8decc14c87215bc1142ccd551db3986da3a1b",'
        '"source_repository":'
        '"https://github.com/BehnazP/SpatioCompo_entireHolocene_EU",'
        '"source_row_number":2,'
        '"source_values":["12.5","55.5","0.2","0.3","0.5"],'
        '"spatial_reference_status":'
        '"source_script_assigns_wgs84_to_generated_geometry_unreviewed",'
        '"taxon_id":null,"taxon_semantics":"not_applicable_land_cover_aggregate",'
        '"temporal_comparability":"unresolved",'
        '"temporal_extent_kind":"source_point_slice",'
        '"time_slice_bp":50,"uncertainty":null,"unforested_open_proportion":"0.5"}'
    )


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
    path = _archive(tmp_path, composition)
    _bind_fixture_archive(path, monkeypatch)

    with pytest.raises(IntakeRefusal, match=reason):
        tuple(normalization.iter_modeled_land_cover(path))


def test_source_time_slices_are_exact_and_irregular() -> None:
    assert normalization.SOURCE_TIME_SLICES_BP[:4] == (50, 225, 550, 1000)
    assert len(normalization.SOURCE_TIME_SLICES_BP) == 25
    assert 0 not in normalization.SOURCE_TIME_SLICES_BP
    assert SOURCE_CITATION_DOI == "https://doi.org/10.3389/fevo.2022.795794"
    assert SOURCE_DATA_LICENSE == "CC-BY-SA-4.0"
