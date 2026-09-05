from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics.reporting.map_document.static_assets import (
    ATLAS_CHUNK_MAX_BYTES,
    validate_static_atlas_assets,
    write_static_atlas_assets,
)

from .fixtures.layers import build_point_layers
from .fixtures.scientific_evidence import (
    build_scientific_point_layers,
    build_scientific_signals,
)

def test_scientific_fixture_refuses_unaccepted_or_unknown_signals(
    tmp_path: Path,
) -> None:
    signals = build_scientific_signals()
    signals[0]["status"] = "review"
    with pytest.raises(ValueError, match="not accepted"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=build_scientific_point_layers(),
            polygon_layers=[],
            scientific_signals=signals,
        )

    point_layers = build_scientific_point_layers()
    features = point_layers[0]["features"]
    assert isinstance(features, list)
    assert isinstance(features[0], dict)
    features[0]["scientific_signal_ids"] = ["pollen:unreviewed"]
    with pytest.raises(ValueError, match="unaccepted scientific signals"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=point_layers,
            polygon_layers=[],
            scientific_signals=build_scientific_signals(),
        )


def test_static_asset_validation_detects_tampering(tmp_path: Path) -> None:
    assets = write_static_atlas_assets(
        tmp_path,
        slug="nordic",
        version="v66",
        point_layers=build_point_layers(),
        polygon_layers=[],
    )
    assets.asset_paths[0].write_text("changed", encoding="utf-8")

    with pytest.raises(ValueError, match="byte count changed|digest changed"):
        validate_static_atlas_assets(assets)


def test_single_unbounded_feature_is_refused(tmp_path: Path) -> None:
    layers = build_point_layers()
    features = layers[0]["features"]
    assert isinstance(features, list)
    assert isinstance(features[0], dict)
    features[0]["description"] = "x" * (ATLAS_CHUNK_MAX_BYTES + 1)

    with pytest.raises(ValueError, match="one static atlas feature"):
        write_static_atlas_assets(
            tmp_path,
            slug="nordic",
            version="v66",
            point_layers=layers,
            polygon_layers=[],
        )
