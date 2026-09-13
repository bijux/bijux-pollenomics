from __future__ import annotations

import inspect
import pickle
from typing import Literal, get_args, get_origin

from bijux_pollenomics.collection.spatial import country_classification

EXPECTED_EXPORTS = [
    "BOUNDARY_CONTACT_EPSILON",
    "COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE",
    "CountryAttributionDecision",
    "CountryDecisionMethod",
    "CountryDecisionStatus",
    "RawCountryComparison",
    "classify_country",
    "decide_country_attribution",
    "geometry_boundary_distance",
    "nearest_country_by_boundary_distance",
    "point_in_geometry",
    "point_in_geometry_ignoring_holes",
    "point_on_geometry_boundary",
    "point_in_outer_ring",
    "point_in_polygon",
    "point_in_ring",
    "point_to_segment_distance",
    "polygon_boundary_distance",
    "ring_boundary_distance",
]

EXPECTED_SIGNATURES = {
    "_compare_raw_country": "(*, raw_country: 'str | None', derived_country: 'str', raw_country_aliases: 'Mapping[str, str] | None') -> 'RawCountryComparison'",
    "_coordinate_refusal_reason": "(longitude: 'float', latitude: 'float') -> 'str | None'",
    "classify_country": "(longitude: 'float', latitude: 'float', country_boundaries: 'CountryBoundaryCollection') -> 'str'",
    "decide_country_attribution": "(longitude: 'float', latitude: 'float', country_boundaries: 'CountryBoundaryCollection', *, boundary_artifact_digest: 'str', boundary_version: 'str', raw_country: 'str | None' = None, raw_country_aliases: 'Mapping[str, str] | None' = None, proximity_tolerance: 'float' = 0.15) -> 'CountryAttributionDecision'",
    "point_to_segment_distance": "(px: 'float', py: 'float', ax: 'float', ay: 'float', bx: 'float', by: 'float') -> 'float'",
}


def test_facade_preserves_exports_constants_and_signatures() -> None:
    assert country_classification.__all__ == EXPECTED_EXPORTS
    assert country_classification.BOUNDARY_CONTACT_EPSILON == 1e-12
    assert country_classification.COUNTRY_BOUNDARY_PROXIMITY_TOLERANCE == 0.15
    assert {
        name: str(inspect.signature(getattr(country_classification, name)))
        for name in EXPECTED_SIGNATURES
    } == EXPECTED_SIGNATURES


def test_public_callables_keep_pickle_import_identity() -> None:
    for name in EXPECTED_EXPORTS:
        value = getattr(country_classification, name)
        if callable(value) and get_origin(value) is None:
            assert pickle.loads(pickle.dumps(value, protocol=5)) is value


def test_public_literal_aliases_keep_pickle_semantics_after_cache_eviction() -> None:
    aliases = [
        getattr(country_classification, name)
        for name in (
            "CountryDecisionMethod",
            "CountryDecisionStatus",
            "RawCountryComparison",
        )
    ]
    # CPython type factories cache only a bounded number of constructed aliases.
    # Serializing a type annotation preserves its meaning, not cache object identity.
    for index in range(256):
        Literal["country-pickle-cache-probe", index]
    for value in aliases:
        restored = pickle.loads(pickle.dumps(value, protocol=5))
        assert get_origin(value) is Literal
        assert get_origin(restored) is Literal
        assert restored == value
        assert get_args(restored) == get_args(value)
