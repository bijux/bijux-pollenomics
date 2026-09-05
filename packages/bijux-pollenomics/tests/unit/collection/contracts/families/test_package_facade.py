from __future__ import annotations

import bijux_pollenomics.collection.contracts.families as families
from bijux_pollenomics.collection.contracts.families.archaeology_contracts import (
    build_archaeology_source_family_contracts,
)
from bijux_pollenomics.collection.contracts.families.boundary_contracts import (
    build_boundary_source_family_contracts,
)
from bijux_pollenomics.collection.contracts.families.dna_contracts import (
    build_dna_source_family_contracts,
)
from bijux_pollenomics.collection.contracts.families.hydrography_contracts import (
    build_hydrography_source_family_contracts,
)
from bijux_pollenomics.collection.contracts.families.pollen_contracts import (
    build_pollen_source_family_contracts,
)


_PUBLIC_API = [
    "SourceFamilyContract",
    "SourceFamilyLayerContract",
    "SourceFamilyStateRow",
    "build_source_family_contract_payload",
    "build_source_family_contracts",
    "build_source_family_state_matrix_payload",
    "build_source_family_state_rows",
]

_PRIVATE_COMPATIBILITY_API = (
    "_SourceAuthorityState",
    "_animal_adna_authority_state",
    "_animal_adna_metrics",
    "_blocking_reasons",
    "_boundary_authority_state",
    "_coverage_metrics",
    "_feature_list",
    "_geojson_feature_count",
    "_layer_status",
    "_load_json_object",
    "_non_negative_int",
    "_object",
    "_path_has_governed_content",
    "_provenance_depth",
    "_publication_posture",
    "_resolve_repository_path",
    "_source_authority_state",
    "_svar_authority_state",
)


def test_package_facade_preserves_public_and_private_consumer_surface() -> None:
    assert families.__all__ == _PUBLIC_API
    assert all(hasattr(families, name) for name in _PRIVATE_COMPATIBILITY_API)


def test_contract_definitions_are_owned_by_durable_source_domains() -> None:
    grouped_source_keys = (
        tuple(row.source_key for row in build_pollen_source_family_contracts()),
        tuple(row.source_key for row in build_archaeology_source_family_contracts()),
        tuple(row.source_key for row in build_boundary_source_family_contracts()),
        tuple(row.source_key for row in build_hydrography_source_family_contracts()),
        tuple(row.source_key for row in build_dna_source_family_contracts()),
    )
    assert grouped_source_keys == (
        ("landclim", "neotoma"),
        ("sead", "raa"),
        ("boundaries",),
        ("svar",),
        ("aadr", "animal_adna"),
    )
    assert tuple(
        source_key for group in grouped_source_keys for source_key in group
    ) == tuple(row.source_key for row in families.build_source_family_contracts())
