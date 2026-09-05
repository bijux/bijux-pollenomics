"""Representative source-native Neotoma classification inputs."""

from __future__ import annotations

from typing import Any


def representative_snapshot() -> dict[str, Any]:
    observations: list[dict[str, Any]] = [
        {
            "observation_id": "obs:1",
            "variable_id": "var:1",
            "site_id": "site:se",
            "country_code": "NO",
            "source_taxon_id": 1947,
            "source_reported_name": "Poaceae (Cerealia-type) undiff.",
            "source_taxon_group": "Vascular plants",
            "source_ecological_group": "UPHE",
            "source_element": "pollen",
            "source_element_type": "pollen",
            "source_unit": "NISP",
            "unit_family": "count",
        },
        {
            "observation_id": "obs:2",
            "variable_id": "var:2",
            "site_id": "site:dk",
            "country_code": "DK",
            "source_taxon_id": 63,
            "source_reported_name": "Pollen concentration",
            "source_taxon_group": "Laboratory analyses",
            "source_ecological_group": "LABO",
            "source_element": "concentration",
            "source_element_type": "concentration",
            "source_unit": "grains/cm3",
            "unit_family": "concentration_per_volume",
        },
        {
            "observation_id": "obs:3",
            "variable_id": "var:3",
            "site_id": "site:missing",
            "country_code": None,
            "source_taxon_id": 9000,
            "source_reported_name": "Recorded value",
            "source_taxon_group": "Administrative variables",
            "source_ecological_group": "ADMN",
            "source_element": "administrative",
            "source_element_type": None,
            "source_unit": "text",
            "unit_family": "categorical",
        },
    ]
    observations.append(dict(observations[0]))
    return {
        "schema_version": "neotoma-relational-snapshot.v1",
        "source_family": "neotoma",
        "source_snapshot_id": "sha256:fixture",
        "build_id": "fixture-build",
        "sites": [
            {"site_id": "site:se", "source_geopolitical": ["Sweden", "Skane"]},
            {"site_id": "site:dk", "source_geopolitical": [{"country": "Denmark"}]},
        ],
        "variables": [
            {
                "variable_id": "var:1",
                "source_taxon_id": 1947,
                "source_reported_name": "Poaceae (Cerealia-type) undiff.",
            },
            {
                "variable_id": "var:2",
                "source_taxon_id": 63,
                "source_reported_name": "Pollen concentration",
            },
        ],
        "observations": observations,
    }
