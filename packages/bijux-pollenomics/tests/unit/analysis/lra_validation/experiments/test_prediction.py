"""Target support has explicit chronology and no implicit pairing casts."""

from pathlib import Path

import pytest

from bijux_pollenomics.analysis.lra_validation import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    ExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import read_geometry
from bijux_pollenomics.analysis.lra_validation.experiments.prediction import _support

from .test_inputs import fixture_inputs


@pytest.mark.parametrize(
    "field,value",
    [
        ("coordinate", 9007199254740993),
        ("coordinate", True),
        ("age_type", "unknown"),
        ("age_support_bp", [[5300, 5600]]),
        ("bin_id", "another"),
    ],
)
def test_unsupported_target_chronology(
    tmp_path: Path, field: str, value: object
) -> None:
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    geometry = read_geometry(tmp_path, spec.sites[0], spec)
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        object_mapping,
    )

    metadata = object_mapping(geometry["sample_metadata"], "metadata")
    metadata[field] = value
    geometry["sample_metadata"] = metadata
    with pytest.raises(ValidationRefusal):
        _support(spec, geometry, geometry)


def test_same_explicit_bin_is_admitted(tmp_path: Path) -> None:
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    left = read_geometry(tmp_path, spec.sites[0], spec)
    right = read_geometry(tmp_path, spec.sites[1], spec)
    assert _support(spec, left, right) == "test-bin"
