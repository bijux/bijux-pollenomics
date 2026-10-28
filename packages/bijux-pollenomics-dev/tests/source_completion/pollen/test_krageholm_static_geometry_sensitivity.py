"""Refuse changed custody and invalid point-age semantics before numerical work."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

PRODUCER = (
    Path(__file__).resolve().parents[5]
    / "reports/science/krageholm-static-geometry-sensitivity/qualify.py"
)


def module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("krageholm_static_geometry", PRODUCER)
    assert spec is not None and spec.loader is not None
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


@pytest.mark.parametrize("point,index", [(0, 0), (100, 1), (200, None), (-45, None)])
def test_half_open_native_point_domain(point: float, index: int | None) -> None:
    assert module().point_window(point, [0, 100, 200]) == index


@pytest.mark.parametrize("point", [True, "100", float("nan"), float("inf")])
def test_invalid_point_age_is_refused(point: object) -> None:
    with pytest.raises(ValueError, match="finite native number"):
        module().point_window(point, [0, 100, 200])


def test_missing_source_is_refused_before_geometry(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="regular exact files"):
        module().qualify(tmp_path)


def test_changed_source_is_refused_before_geometry(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    (inputs / "dataset-23013-sample-eligibility.json").write_text("[]")
    with pytest.raises(ValueError, match="custody changed"):
        module().qualify(tmp_path)


def test_source_symlink_is_refused_before_geometry(tmp_path: Path) -> None:
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    outside = tmp_path / "sample.json"
    outside.write_text("[]")
    (inputs / "dataset-23013-sample-eligibility.json").symlink_to(outside)
    with pytest.raises(ValueError, match="regular exact files"):
        module().qualify(tmp_path)
