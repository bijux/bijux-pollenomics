"""Compatibility checks for the animal-atlas evidence row package."""

from __future__ import annotations

import inspect

from bijux_pollenomics.reporting.adna import atlas_evidence_rows

_PUBLIC_API = (
    "AnimalAtlasCoordinateReview",
    "AnimalAtlasEvidenceRow",
    "build_tracked_animal_atlas_coordinate_review",
    "build_tracked_animal_atlas_evidence_rows",
    "load_tracked_animal_mappable_localities",
)
_LEGACY_PRIVATE_API = frozenset(
    {
        "_DIRECT_COORDINATE_BASES",
        "_animal_scope_for",
        "_assert_no_project_level_flattening",
        "_atlas_public_chronology",
        "_inclusion_notes_for",
        "_inclusion_statuses_for",
        "_load_citation_lookup",
        "_load_coordinate_provenance_lookup",
        "_load_locality_rows",
        "_load_review_lookup",
        "_load_sample_rows",
        "_load_site_evidence_lookup",
        "_lookup_project_locality_row",
        "_normalize_locality_text",
        "_optional_float",
        "_optional_int",
        "_optional_str",
        "_paper_url_for",
        "_parse_chronology",
        "_parse_locality_summary",
        "_sample_group_ids_for",
        "_sample_locality_token",
        "_sample_record_ids_for",
        "_supplementary_sources_for",
    }
)
_LEGACY_FUNCTION_SIGNATURES = {
    "_animal_scope_for": "(species_root: 'Path') -> 'str'",
    "_assert_no_project_level_flattening": (
        "(*, primary_project_accession: 'str', site_record_id: 'str', "
        "sample_rows: 'tuple[dict[str, object], ...]') -> 'None'"
    ),
    "_atlas_public_chronology": "(chronology: 'AdnaChronology') -> 'AdnaChronology'",
    "_inclusion_notes_for": (
        "(sample_rows: 'tuple[dict[str, object], ...]') -> 'tuple[str, ...]'"
    ),
    "_inclusion_statuses_for": (
        "(sample_rows: 'tuple[dict[str, object], ...]') -> 'tuple[str, ...]'"
    ),
    "_load_citation_lookup": "(species_root: 'Path') -> 'dict[str, dict[str, str]]'",
    "_load_coordinate_provenance_lookup": (
        "(species_root: 'Path') -> 'dict[tuple[str, str], dict[str, object]]'"
    ),
    "_load_locality_rows": "(species_root: 'Path') -> 'list[dict[str, object]]'",
    "_load_review_lookup": "(species_root: 'Path') -> 'dict[str, dict[str, str]]'",
    "_load_sample_rows": "(species_root: 'Path') -> 'list[dict[str, object]]'",
    "_load_site_evidence_lookup": (
        "(species_root: 'Path') -> 'dict[tuple[str, str], dict[str, object]]'"
    ),
    "_lookup_project_locality_row": (
        "(lookup: 'dict[tuple[str, str], dict[str, object]]', *, "
        "project_accession: 'str', locality_text: 'str') -> "
        "'dict[str, object] | None'"
    ),
    "_normalize_locality_text": "(value: 'str') -> 'str'",
    "_optional_float": "(value: 'object') -> 'float | None'",
    "_optional_int": "(value: 'object') -> 'int | None'",
    "_optional_str": "(value: 'object') -> 'str | None'",
    "_paper_url_for": "(doi: 'str') -> 'str'",
    "_parse_chronology": "(payload: 'object') -> 'AdnaChronology'",
    "_parse_locality_summary": (
        "(payload: 'dict[str, object]') -> 'AdnaLocalitySummary'"
    ),
    "_sample_group_ids_for": (
        "(sample_rows: 'tuple[dict[str, object], ...]') -> 'tuple[str, ...]'"
    ),
    "_sample_locality_token": "(row: 'dict[str, object]') -> 'str'",
    "_sample_record_ids_for": (
        "(sample_rows: 'tuple[dict[str, object], ...]') -> 'tuple[str, ...]'"
    ),
    "_supplementary_sources_for": (
        "(sample_rows: 'tuple[dict[str, object], ...]', provenance: "
        "'dict[str, object]', site_evidence: 'dict[str, object]') -> "
        "'tuple[str, ...]'"
    ),
}


def test_facade_preserves_public_and_private_imports() -> None:
    assert tuple(atlas_evidence_rows.__all__) == _PUBLIC_API
    assert _LEGACY_PRIVATE_API <= frozenset(vars(atlas_evidence_rows))


def test_public_callable_signatures_remain_stable() -> None:
    evidence_signature = inspect.signature(
        atlas_evidence_rows.build_tracked_animal_atlas_evidence_rows
    )
    locality_signature = inspect.signature(
        atlas_evidence_rows.load_tracked_animal_mappable_localities
    )
    review_signature = inspect.signature(
        atlas_evidence_rows.build_tracked_animal_atlas_coordinate_review
    )

    assert tuple(evidence_signature.parameters) == ("data_root",)
    assert tuple(locality_signature.parameters) == ("data_root",)
    assert tuple(review_signature.parameters) == ("evidence_rows",)


def test_legacy_function_signatures_remain_stable() -> None:
    assert {
        name: str(inspect.signature(getattr(atlas_evidence_rows, name)))
        for name in _LEGACY_FUNCTION_SIGNATURES
    } == _LEGACY_FUNCTION_SIGNATURES
