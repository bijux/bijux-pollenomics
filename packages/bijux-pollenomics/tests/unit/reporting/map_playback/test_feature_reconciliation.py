"""Complexity invariants for source-chronology feature reconciliation."""

from __future__ import annotations

from typing import cast

from bijux_pollenomics.reporting.map_playback.feature_reconciliation import (
    reconcile_facet_metadata_to_features,
)
from tests.unit.reporting.map_playback.support import mutable_source_layers


class _FeatureKeyReadCounter(dict[str, object]):
    def __init__(self, row: dict[str, object]) -> None:
        super().__init__(row)
        self.feature_key_reads = 0

    def get(self, key: str, default: object = None) -> object:
        if key == "feature_key":
            self.feature_key_reads += 1
        return super().get(key, default)


def test_taxon_reconciliation_indexes_each_feature_key_once() -> None:
    layer = mutable_source_layers()[2]
    raw_features = layer["features"]
    assert isinstance(raw_features, list)
    features = [
        _FeatureKeyReadCounter(cast(dict[str, object], feature))
        for feature in raw_features
    ]
    layer["features"] = features
    facets = layer["facet_metadata"]
    assert isinstance(facets, dict)

    reconcile_facet_metadata_to_features(layer, facets)

    assert len(features) == 972
    assert all(feature.feature_key_reads == 1 for feature in features)
