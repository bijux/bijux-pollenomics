from __future__ import annotations

from bijux_pollenomics.collection.contracts.capabilities import (
    CAPABILITY_DIMENSIONS,
    build_source_capability_contract_payload,
)
from bijux_pollenomics.collection.contracts.families import (
    build_source_family_contract_payload,
)


def test_capability_contract_covers_every_source_and_dimension_exactly() -> None:
    payload = build_source_capability_contract_payload()

    assert payload["schema_version"] == "source-capability-contract.v1"
    assert payload["dimension_count"] == 17
    assert payload["dimensions"] == list(CAPABILITY_DIMENSIONS)
    assert payload["source_count"] == 8
    sources = payload["sources"]
    assert isinstance(sources, list)
    assert {source["source_key"] for source in sources} == {
        "aadr",
        "animal_adna",
        "boundaries",
        "landclim",
        "neotoma",
        "raa",
        "sead",
        "svar",
    }
    for source in sources:
        assert set(source["support_by_dimension"]) == set(CAPABILITY_DIMENSIONS)
        assert set(source["evidence_paths_by_dimension"]) == set(CAPABILITY_DIMENSIONS)
        assert set(source["support_by_dimension"].values()) <= {
            "supported",
            "partial",
            "unsupported",
        }


def test_normative_support_map_and_repository_extension_are_explicit() -> None:
    payload = build_source_capability_contract_payload()
    sources = {source["source_key"]: source for source in payload["sources"]}
    partial = {
        "neotoma": {
            "four_country_coverage",
            "chronology_uncertainty",
            "relative_chronology",
            "derived_pollen_group",
            "derived_ecological_role",
        },
        "sead": {
            "four_country_coverage",
            "chronology_uncertainty",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "landclim": {
            "four_country_coverage",
            "within_site_hierarchy",
            "chronology_uncertainty",
            "taxon_identity",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "dataset_provenance",
            "pollen_propagation_event",
        },
        "raa": {
            "within_site_hierarchy",
            "numeric_chronology",
            "chronology_uncertainty",
            "quantitative_observation",
            "observation_unit",
        },
        "svar": {"within_site_hierarchy", "dataset_provenance"},
        "animal_adna": {
            "four_country_coverage",
            "chronology_uncertainty",
            "relative_chronology",
            "native_ecological_class",
            "quantitative_observation",
            "observation_unit",
        },
        "boundaries": set(),
    }
    unsupported = {
        "neotoma": set(),
        "sead": set(),
        "landclim": {"relative_chronology"},
        "raa": {
            "four_country_coverage",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "svar": {
            "four_country_coverage",
            "numeric_chronology",
            "chronology_uncertainty",
            "relative_chronology",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "animal_adna": {
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "pollen_propagation_event",
        },
        "boundaries": {
            "within_site_hierarchy",
            "numeric_chronology",
            "chronology_uncertainty",
            "relative_chronology",
            "taxon_identity",
            "native_ecological_class",
            "derived_pollen_group",
            "derived_ecological_role",
            "crop_cereal_resolution",
            "quantitative_observation",
            "observation_unit",
            "pollen_propagation_event",
        },
    }
    for source_key in partial:
        expected = {
            dimension: (
                "unsupported"
                if dimension in unsupported[source_key]
                else "partial"
                if dimension in partial[source_key]
                else "supported"
            )
            for dimension in CAPABILITY_DIMENSIONS
        }
        assert sources[source_key]["support_by_dimension"] == expected

    assert payload["normative_contract"] == {
        "contract_id": "bijux-pollenomics-source-capability-matrix",
        "schema_version": "1.0.0",
        "source_count": 7,
        "source_keys": sorted(partial),
    }
    assert payload["extension_sources"] == ["aadr"]
    assert sources["neotoma"]["evidence_class"] == "observed_paleoecological"
    assert (
        sources["animal_adna"]["evidence_class"]
        == "observed_genetic_or_zooarchaeological"
    )


def test_contract_registry_keeps_capability_separate_from_materialization() -> None:
    payload = build_source_family_contract_payload()
    capability = payload["capability_contract"]

    assert capability["schema_version"] == "source-capability-contract.v1"
    assert all("materialization" not in source for source in capability["sources"])
    assert payload["schema_version"] == "source-family-contracts.v1"
