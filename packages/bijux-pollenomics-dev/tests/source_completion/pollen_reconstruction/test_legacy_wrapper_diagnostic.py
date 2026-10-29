"""Legacy wrapper domain and fatal-error boundaries on artificial caller tables."""

from __future__ import annotations

from copy import deepcopy
import math
from pathlib import Path
import runpy
from typing import Any

import pytest

from bijux_pollenomics.analysis.lra.engine.errors import LRARefusal
from bijux_pollenomics_lra.models.errors import ValidationError

ROOT = Path.cwd()
SOURCE = globals().get(
    "SCIENTIFIC_SOURCE_ROOT", ROOT / "reports/science/legacy-wrapper-diagnostics/source"
)
API = runpy.run_path(
    str(SOURCE / "replay.py"), run_name="legacy_wrapper_source_controls"
)
TAXA = ["taxon:" + str(index) for index in range(30)]


def pair(index: int = 1) -> dict[str, Any]:
    return {
        "nominal_request_sha256": format(index, "064x"),
        "legacy_request_sha256": format(index + 100, "064x"),
        "regional_cover": [0.5, 0.49999, *([0.0] * 28)],
        "payload": {
            "operation": "lra",
            "method_profile": "disqover-0.9.14-source-compatible",
            "taxa": TAXA,
            "configuration": {
                "seed": 7,
                "reveals": {
                    "stochastic": False,
                    "iterations": 2,
                    "distance_weighting": "gpm neutral",
                },
                "love": {
                    "method": "optimized",
                    "optimized_profile": "disqover-0.9.14-source",
                    "optimizer_backend": "scipy.differential_evolution",
                    "max_ring": 2,
                    "repeats": 1,
                    "stochastic": False,
                    "distance_weighting": "gpm neutral",
                    "fall_speed_profile": "disqover-0.9.14-wrapper-v1",
                    "optimizer_iterations": 300,
                    "optimizer_max_evaluations": 16000,
                    "optimizer_tolerance": 1e-8,
                },
            },
            "local": {
                "basin": {"site_type": "lake", "diameter_m": 40},
                "samples": [{"coordinate": 1, "counts": [8, 2, *([0] * 28)]}],
            },
            "regional": {
                "basin": {"site_type": "lake", "diameter_m": 1000},
                "samples": [{"coordinate": 1, "counts": [5, 5, *([0] * 28)]}],
            },
            "parameters": [
                {"taxon": t, "fallspeed_m_s": 0.024, "ppe": 1, "ppe_sd": 0}
                for t in TAXA
            ],
            "rings": [
                {
                    "inner_m": lo,
                    "outer_m": hi,
                    "mean_m": (lo + hi) / 2,
                    "ring_area_m2": math.pi * (hi**2 - lo**2),
                    "terrestrial_area_m2": math.pi * (hi**2 - lo**2),
                }
                for lo, hi in ((100, 500), (500, 1000), (1000, 10000))
            ],
        },
    }


def test_real_maintained_wrapper_refuses_before_any_kernel_or_optimizer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from bijux_pollenomics_lra.reconstruction import optimized
    from bijux_pollenomics_lra.workflows.local import run_love

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Source dimension guard must precede kernels and optimization")

    monkeypatch.setattr(optimized, "calK", forbidden)
    result = API["invoke"](pair(), run_love)
    assert result["status"] == "refused"
    assert result["reason_code"] == "unsupported_source_ring_dimensions"
    assert len(result["ring_dispositions"]) == 2
    assert result["raw_regional_cover"] == pair()["regional_cover"]
    assert sum(result["raw_regional_cover"]) == pytest.approx(0.99999)


def test_complete39_population_preserves_every_refusal_and_input() -> None:
    calls = []

    def refuse(
        local: Any, regional: Any, params: Any, rings: Any, config: Any, **kwargs: Any
    ) -> Any:
        calls.append(kwargs["regional_cover_draws"].tolist())
        assert list(local.columns[1:]) == list(regional.columns[1:]) == TAXA
        assert list(params["species"]) == TAXA and rings.shape == (3, 5)
        assert config.optimized_profile == "disqover-0.9.14-source"
        assert config.optimizer_backend == "scipy.differential_evolution"
        raise ValidationError(
            "Original dimension diagnostic", reason_code=API["REFUSAL"]
        )

    original = [pair(i) for i in range(1, 40)]
    before = deepcopy(original)
    records = API["run"](original, refuse)
    assert original == before and len(records) == len(calls) == 39
    assert sum(len(row["ring_dispositions"]) for row in records) == 78
    assert [row["nominal_request_sha256"] for row in records] == [
        row["nominal_request_sha256"] for row in original
    ]
    assert all(
        row["reason_code"] == API["REFUSAL"] and row["API_calls"] == 1
        for row in records
    )
    assert all(vector == [original[0]["regional_cover"]] for vector in calls)


@pytest.mark.parametrize(
    "kind", ["validation", "engine", "runtime", "value", "returned"]
)
def test_unknown_faults_and_unexpected_success_are_fatal(kind: str) -> None:
    def broken(*args: Any, **kwargs: Any) -> Any:
        if kind == "validation":
            raise ValidationError("Unknown validation", reason_code="invalid_input")
        if kind == "engine":
            raise LRARefusal(
                "lra_extension_missing",
                "Engine unavailable",
                diagnostics={"ready": False},
            )
        if kind == "runtime":
            raise RuntimeError("Implementation failure")
        if kind == "value":
            raise ValueError("Unclassified implementation failure")
        return object()

    expected = {
        "validation": ValidationError,
        "engine": LRARefusal,
        "runtime": RuntimeError,
        "value": ValueError,
        "returned": RuntimeError,
    }[kind]
    with pytest.raises(expected) as error:
        API["invoke"](pair(), broken)
    if kind == "engine":
        assert isinstance(error.value, LRARefusal)
        assert error.value.reason_code == "lra_extension_missing"
        assert error.value.diagnostics == {"ready": False}


@pytest.mark.parametrize(
    "kind", ["taxa", "regional-axis", "profile", "terrestrial", "population"]
)
def test_changed_population_or_source_domain_fails_before_api(kind: str) -> None:
    candidate = pair()
    if kind == "taxa":
        candidate["payload"]["taxa"] = TAXA[:-1]
    elif kind == "regional-axis":
        candidate["regional_cover"] = candidate["regional_cover"][:-1]
    elif kind == "profile":
        candidate["payload"]["configuration"]["love"]["optimized_profile"] = (
            "ring-taxon-preserving"
        )
    elif kind == "terrestrial":
        candidate["payload"]["rings"][0]["terrestrial_area_m2"] = 0

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        pytest.fail("Changed declared source domain cannot reach the numerical API")

    with pytest.raises(ValueError):
        if kind == "population":
            API["run"]([candidate] * 39, forbidden)
        else:
            API["invoke"](candidate, forbidden)
