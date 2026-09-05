from __future__ import annotations

import bijux_pollenomics.adna.projects.evidence.localities as localities


_PUBLIC_API = [
    "ADNA_LOCALITY_CLASSES",
    "build_project_locality_completeness_rows",
    "build_project_locality_worksheet_rows",
    "build_project_locality_substitution_ledger",
    "build_project_sample_locality_evidence_rows",
    "build_sample_locality_conflict_ledger",
    "build_sample_locality_manual_curation_workflow_rows",
    "build_site_name_normalization_dictionary_rows",
    "build_species_locality_completeness_rows",
    "materialize_project_sample_locality_evidence_library",
]


def test_package_facade_preserves_public_api_and_locality_vocabulary() -> None:
    assert localities.__all__ == _PUBLIC_API
    assert localities.ADNA_LOCALITY_CLASSES == (
        "excavation_site",
        "broader_locality",
        "municipality",
        "region",
        "country",
        "inferred_place_string",
        "unresolved",
    )


def test_cached_builders_remain_cache_managed_after_decomposition() -> None:
    cached_builders = [
        getattr(localities, name) for name in _PUBLIC_API if name.startswith("build_")
    ]
    assert all(callable(builder) for builder in cached_builders)
    assert all(hasattr(builder, "cache_clear") for builder in cached_builders)
