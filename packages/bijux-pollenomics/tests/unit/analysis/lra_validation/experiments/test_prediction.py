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


def test_same_bin_wrapper_refuses_before_mapping(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import prediction
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        object_mapping,
    )

    spec = ExperimentSpec(fixture_inputs(tmp_path))
    target = read_geometry(tmp_path, spec.sites[0], spec)
    anchor = read_geometry(tmp_path, spec.sites[1], spec)
    metadata = object_mapping(target["sample_metadata"], "metadata")
    metadata["bin_id"] = "future-bin"
    target["sample_metadata"] = metadata
    geometry_calls = iter((target, anchor))
    monkeypatch.setattr(
        prediction, "read_geometry", lambda *args, **kwargs: next(geometry_calls)
    )

    def forbidden(*args: object, **kwargs: object) -> None:
        pytest.fail("Chronology mismatch reached mechanical forward mapping")

    monkeypatch.setattr(prediction, "prepare_forward_geometry", forbidden)
    with pytest.raises(ValidationRefusal, match="bin_id"):
        prediction.prepare_target_forward(
            spec, spec.sites[0], spec.sites[1], (0.4, 0.6), input_root=tmp_path
        )


def _mapping_spy(monkeypatch: pytest.MonkeyPatch) -> tuple[object, dict[str, object]]:
    """Record the adapter boundary without requiring the optional numeric extra."""
    import sys
    from types import ModuleType, SimpleNamespace

    from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
    from bijux_pollenomics.analysis.lra_validation.experiments import prediction

    captured: dict[str, object] = {}
    pandas = ModuleType("pandas")
    monkeypatch.setattr(pandas, "DataFrame", lambda value: value, raising=False)
    monkeypatch.setitem(sys.modules, "pandas", pandas)
    api = ModuleType("mapping-test-api")

    def config(**kwargs: object) -> dict[str, object]:
        return kwargs

    def prepare(
        parameters: object, rings: object, regional: object, configured: object
    ) -> object:
        captured.update(
            parameters=parameters, rings=rings, regional=regional, config=configured
        )
        return SimpleNamespace(taxa=("Alnus", "Betula"))

    monkeypatch.setattr(api, "ForwardConfig", config, raising=False)
    monkeypatch.setattr(api, "prepare_forward_inputs", prepare, raising=False)
    monkeypatch.setattr(api, "forward_deposition", lambda: None, raising=False)
    binding = EngineBinding("test-only", "test-only", "test-only", api)
    monkeypatch.setattr(prediction, "load_engine", lambda: binding)
    return binding, captured


def test_mapping_preserves_measured_areas_parameter_errors_and_default_profiles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from bijux_pollenomics.analysis.lra_validation.experiments import prediction

    binding, captured = _mapping_spy(monkeypatch)
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    geometry = read_geometry(tmp_path, spec.sites[0], spec)
    template = spec.template()
    # Nontrivial values expose fraction/area and uncertainty-column substitution.
    template["parameters"] = [
        {"taxon": "Alnus", "fallspeed_m_s": 0.02, "ppe": 4.0, "ppe_sd": 0.4},
        {"taxon": "Betula", "fallspeed_m_s": 0.03, "ppe": 3.0, "ppe_sd": 0.6},
    ]
    geometry["forward_rings"] = [
        {
            "inner_m": 20.0,
            "outer_m": 1000.0,
            "mean_m": 510.0,
            "ring_area_m2": 3140336.0,
            "terrestrial_area_m2": 1570168.0,
        },
    ]
    actual, _ = prediction.prepare_forward_geometry(
        template, geometry, (0.35, 0.65), local_ring_count=1
    )
    assert actual is binding
    assert captured == {
        "parameters": {
            "Taxon": ["Alnus", "Betula"],
            "fallspeed": [0.02, 0.03],
            "ppe": [4.0, 3.0],
            "ppe.error": [0.4, 0.6],
        },
        "rings": {
            "inner": [20.0],
            "outer": [1000.0],
            "mean": [510.0],
            "ring": [3140336.0],
            "terrestrial": [1570168.0],
        },
        "regional": (0.35, 0.65),
        "config": {
            "local_ring_count": 1,
            "local_basin_diameter_m": 40,
            "distance_weighting": "lsm unstable",
            "regional_cover_profile": "disqover-rounded-fractions",
        },
    }


@pytest.mark.parametrize("guard", ["lake", "taxa", "capability"])
def test_mapping_retains_existing_refusals(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, guard: str
) -> None:
    from bijux_pollenomics.analysis.lra.engine.discovery import EngineBinding
    from bijux_pollenomics.analysis.lra_validation.experiments import prediction
    from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
        object_mapping,
    )

    binding, _ = _mapping_spy(monkeypatch)
    assert isinstance(binding, EngineBinding)
    spec = ExperimentSpec(fixture_inputs(tmp_path))
    geometry = read_geometry(tmp_path, spec.sites[0], spec)
    template = spec.template()
    if guard == "lake":
        basin = object_mapping(geometry["basin"], "basin")
        basin["site_type"] = "bog"
        geometry["basin"] = basin
    elif guard == "taxa":
        template["taxa"] = ["Betula", "Alnus"]
    else:
        monkeypatch.delattr(binding.api, "prepare_forward_inputs")
    with pytest.raises(ValidationRefusal) as refused:
        prediction.prepare_forward_geometry(
            template, geometry, (0.4, 0.6), local_ring_count=2
        )
    assert (
        refused.value.reason_code
        == {
            "lake": "unsupported_target_basin",
            "taxa": "taxon_denominator_mismatch",
            "capability": "forward_preparation_unavailable",
        }[guard]
    )


@pytest.mark.parametrize("failure", ["mapping", "support", "missing_anchor"])
def test_consumed_geometry_survives_later_target_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    import json

    from bijux_pollenomics.analysis.lra_validation.experiments import prediction

    from .test_inputs import store

    request = fixture_inputs(tmp_path)
    if failure == "support":
        site = request["sites"][0]
        path = tmp_path / site["geometry"]["path"]
        geometry = json.loads(path.read_text())
        geometry["sample_metadata"]["bin_id"] = "future-bin"
        site["geometry"] = store(tmp_path, path.name, geometry)
    spec = ExperimentSpec(request)
    if failure == "missing_anchor":
        (tmp_path / spec.sites[1].geometry.path).unlink()

    def mapping_failure(*args: object, **kwargs: object) -> None:
        raise ValidationRefusal(
            "controlled_mapping_failure", "After both admitted reads"
        )

    monkeypatch.setattr(prediction, "prepare_forward_geometry", mapping_failure)
    consumed: set[str] = set()
    with pytest.raises(ValidationRefusal):
        prediction.prepare_target_forward(
            spec,
            spec.sites[0],
            spec.sites[1],
            (0.4, 0.6),
            input_root=tmp_path,
            consumed_geometry=consumed,
        )
    assert consumed == {
        site.record.record_id
        for site in spec.sites[: 1 if failure == "missing_anchor" else 2]
    }
