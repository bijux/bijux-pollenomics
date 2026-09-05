"""LandClim country evidence derivation."""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping

from ..constants import INPUT_PATHS, CountryCoverageError
from ..decoding import _country_code, _features, _geojson_country_counts, _object
from .partitions import EvidenceMap, _site_partition


def add_landclim_evidence(
    evidence: EvidenceMap, documents: Mapping[str, Mapping[str, object]]
) -> None:
    landclim = documents[INPUT_PATHS[3]]
    reported = Counter[str]()
    for feature in _features(landclim, "LandClim normalized sites"):
        properties = _object(feature.get("properties"), "LandClim properties")
        popup = properties.get("popup_rows")
        if not isinstance(popup, list):
            raise CountryCoverageError("LandClim source country evidence is missing")
        reported_values = [
            row.get("value")
            for row in popup
            if isinstance(row, Mapping) and row.get("label") == "Reported country"
        ]
        if len(reported_values) > 1:
            raise CountryCoverageError(
                "LandClim feature contains duplicate Reported country labels"
            )
        reported[_country_code(reported_values[0] if reported_values else None)] += 1
    _site_partition(evidence, "landclim", "source_reported", reported)
    _site_partition(
        evidence,
        "landclim",
        "publication",
        _geojson_country_counts(documents[INPUT_PATHS[8]]),
        published=True,
    )
