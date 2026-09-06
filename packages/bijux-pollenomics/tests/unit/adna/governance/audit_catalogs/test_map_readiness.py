"""Animal map-readiness accounting tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.adna.governance.audit_catalogs.map_readiness import (
    _build_species_map_readiness_row,
    _map_publication_accounting,
    _map_publication_key,
    build_cross_species_map_readiness,
)
from bijux_pollenomics.adna.governance.audit_catalogs import map_readiness
from bijux_pollenomics.reporting import adna as reporting_adna

pytestmark = pytest.mark.generated_artifacts


class _PublicationRow:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def as_dict(self) -> dict[str, object]:
        return dict(self._payload)


def _publication_payload() -> dict[str, object]:
    return {
        "species_latin_name": "Equus caballus",
        "primary_project_accession": "PRJEB1",
        "coordinate_source_locator": "table 1",
        "coordinate_basis": "archive_coordinates",
        "locality": "Site A",
        "latitude_text": "55.0",
        "longitude_text": "12.0",
        "original_place_text": "Site A",
        "resolved_place_text": "Site A",
    }


def _coordinate_payload(**overrides: object) -> dict[str, object]:
    return {
        "species_latin_name": "Equus caballus",
        "species_common_name": "horse",
        "project_accession": "PRJEB1",
        "source_locator": "table 1",
        "coordinate_basis": "archive_coordinates",
        "site_label": "Site A",
        "latitude_text": "55.0",
        "longitude_text": "12.0",
        "original_place_text": "Site A",
        "resolved_place_text": "Site A",
        "mapping_posture": "mappable_point",
        **overrides,
    }


def _install_accounting_scenario(
    monkeypatch: pytest.MonkeyPatch,
    *,
    publication_rows: tuple[_PublicationRow, ...],
    coordinate_rows: list[dict[str, object]],
) -> None:
    monkeypatch.setattr(
        reporting_adna,
        "build_tracked_animal_atlas_evidence_rows",
        lambda _root: publication_rows,
    )
    monkeypatch.setattr(map_readiness, "TRACKED_ADNA_SPECIES", ("Equus caballus",))
    monkeypatch.setattr(map_readiness, "_species_root", lambda *_args: Path("species"))
    monkeypatch.setattr(
        map_readiness,
        "_load_coordinate_provenance_rows",
        lambda _root: coordinate_rows,
    )


def test_map_publication_identity_separates_sibling_sites() -> None:
    shared = {
        "species_latin_name": "Equus caballus",
        "project_accession": "PRJEB1",
        "source_locator": "table 1",
        "coordinate_basis": "supplementary_table_coordinates",
        "original_place_text": "shared context",
        "resolved_place_text": "shared context",
    }
    site_a = {
        **shared,
        "site_label": "Site A",
        "latitude_text": "55.0",
        "longitude_text": "12.0",
    }
    site_b = {
        **shared,
        "site_label": "Site B",
        "latitude_text": "56.0",
        "longitude_text": "13.0",
    }

    assert _map_publication_key(
        site_a, project_field="project_accession"
    ) != _map_publication_key(site_b, project_field="project_accession")


def test_map_readiness_reconciles_point_ready_and_unpublished_counts(
    catalog_data_root: Path,
) -> None:
    readiness = build_cross_species_map_readiness(catalog_data_root)

    horse_row = next(
        row
        for row in readiness["rows"]
        if row["species_latin_name"] == "Equus caballus"
    )
    sheep_row = next(
        row for row in readiness["rows"] if row["species_latin_name"] == "Ovis aries"
    )
    pig_row = next(
        row
        for row in readiness["rows"]
        if row["species_latin_name"] == "Sus scrofa domesticus"
    )
    assert readiness["totals"]["direct_coordinate_backed"] == 274
    assert readiness["totals"]["indirectly_geocoded"] == 4
    assert readiness["totals"]["coordinate_provenance_mappable_count"] == 278
    assert readiness["totals"]["coordinate_provenance_row_count"] == 284
    assert readiness["totals"]["publication_candidate_count"] == 271
    assert readiness["totals"]["not_materialized_count"] == 7
    assert readiness["totals"]["refused_coordinate_provenance_count"] == 6
    assert readiness["totals"]["region_only_coordinate_refusal_count"] == 4
    assert readiness["totals"]["unresolved_location_coordinate_refusal_count"] == 2
    assert readiness["totals"]["unresolved_sample_count"] == 95
    assert readiness["publication_accounting"]["overall_ok"]
    assert {
        (row["project_accession"], row["site_label"])
        for row in readiness["not_materialized_rows"]
    } == {
        ("PRJEB22390", "Botai archaeological site horse context"),
        ("PRJEB90261", "Lobos"),
        ("SRP073444", "Site 1040 near Wadi Halfa dromedary context"),
        ("PRJEB31613", "Altata"),
        ("PRJEB31613", "Belkaragay"),
        ("PRJEB31613", "Derkul"),
        ("PRJEB31613", "Lebyazhinka IV"),
    }
    assert {
        (row["project_accession"], row["site_label"]): row["reason_code"]
        for row in readiness["not_materialized_rows"]
    } == {
        (
            "PRJEB22390",
            "Botai archaeological site horse context",
        ): "no_admitted_sample_backed_locality_candidate",
        ("PRJEB90261", "Lobos"): "no_admitted_sample_backed_locality_candidate",
        (
            "SRP073444",
            "Site 1040 near Wadi Halfa dromedary context",
        ): "no_admitted_sample_backed_locality_candidate",
        (
            "PRJEB31613",
            "Altata",
        ): "chronology_not_supported_for_atlas_publication",
        (
            "PRJEB31613",
            "Belkaragay",
        ): "chronology_not_supported_for_atlas_publication",
        (
            "PRJEB31613",
            "Derkul",
        ): "chronology_not_supported_for_atlas_publication",
        (
            "PRJEB31613",
            "Lebyazhinka IV",
        ): "chronology_not_supported_for_atlas_publication",
    }
    assert horse_row["direct_coordinate_backed"] == 207
    assert horse_row["indirectly_geocoded"] == 1
    assert pig_row["indirectly_geocoded"] == 2
    assert pig_row["coordinate_provenance_mappable_count"] == 2
    assert pig_row["publication_candidate_count"] == 2
    assert pig_row["not_materialized_count"] == 0
    assert sheep_row["refused_coordinate_provenance_count"] == 2
    assert sheep_row["region_only_coordinate_refusal_count"] == 0
    assert sheep_row["unresolved_location_coordinate_refusal_count"] == 2
    assert sheep_row["coordinate_provenance_mappable_count"] == 0
    assert sheep_row["publication_candidate_count"] == 0


def test_map_accounting_refuses_duplicate_publication_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row = _PublicationRow(_publication_payload())
    _install_accounting_scenario(
        monkeypatch,
        publication_rows=(row, row),
        coordinate_rows=[],
    )

    with pytest.raises(ValueError, match="publication identity is not unique"):
        _map_publication_accounting(Path("data"))


def test_map_accounting_refuses_duplicate_coordinate_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    coordinate = _coordinate_payload()
    _install_accounting_scenario(
        monkeypatch,
        publication_rows=(),
        coordinate_rows=[coordinate, coordinate],
    )

    with pytest.raises(ValueError, match="coordinate provenance is not unique"):
        _map_publication_accounting(Path("data"))


def test_map_accounting_refuses_unsupported_coordinate_basis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_accounting_scenario(
        monkeypatch,
        publication_rows=(),
        coordinate_rows=[_coordinate_payload(coordinate_basis="invented_basis")],
    )

    with pytest.raises(ValueError, match="unsupported basis: invented_basis"):
        _map_publication_accounting(Path("data"))


def test_map_accounting_refuses_publication_without_coordinate_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_accounting_scenario(
        monkeypatch,
        publication_rows=(_PublicationRow(_publication_payload()),),
        coordinate_rows=[],
    )

    with pytest.raises(ValueError, match="do not reconcile"):
        _map_publication_accounting(Path("data"))


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"mapping_posture": ""}, "unsupported mapping postures: <empty>"),
        (
            {"coordinate_basis": "invented_basis"},
            "unsupported mappable coordinate bases: invented_basis",
        ),
    ],
)
def test_map_posture_accounting_refuses_unknown_contract_values(
    monkeypatch: pytest.MonkeyPatch,
    overrides: dict[str, object],
    message: str,
) -> None:
    monkeypatch.setattr(map_readiness, "_species_root", lambda *_args: Path("species"))
    monkeypatch.setattr(
        map_readiness,
        "_load_coordinate_provenance_rows",
        lambda _root: [_coordinate_payload(**overrides)],
    )
    monkeypatch.setattr(map_readiness, "_load_sample_rows", lambda _root: [])

    with pytest.raises(ValueError, match=message):
        _build_species_map_readiness_row(Path("data"), "Equus caballus")
