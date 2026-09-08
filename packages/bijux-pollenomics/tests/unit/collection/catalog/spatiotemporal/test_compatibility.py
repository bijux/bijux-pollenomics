"""Spatiotemporal posture package compatibility and ownership tests."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.collection.catalog import spatiotemporal
from bijux_pollenomics.collection.catalog.spatiotemporal import service


def test_facade_preserves_the_public_posture_contract() -> None:
    assert spatiotemporal.__all__ == [
        "SourceSpatiotemporalPostureRecord",
        "build_source_spatiotemporal_posture_payload",
    ]
    assert (
        spatiotemporal.build_source_spatiotemporal_posture_payload
        is service.build_source_spatiotemporal_posture_payload
    )


def test_posture_modules_are_owned_by_source_responsibility() -> None:
    package_root = Path(spatiotemporal.__file__).parent
    assert {
        path.stem for path in package_root.glob("*.py") if path.name != "__init__.py"
    } == {
        "archaeology_sources",
        "model",
        "pollen_sources",
        "records",
        "reference_sources",
        "service",
    }
    assert all(
        len(path.read_text(encoding="utf-8").splitlines()) <= 220
        for path in package_root.glob("*.py")
    )
