"""One adapter for regional, local and paired source-compatible workflows."""

from __future__ import annotations

from typing import Any

from ..engine.discovery import EngineBinding
from ..engine.errors import LRARefusal
from ..inputs.validation import ValidatedRequest


def _configuration(
    binding: EngineBinding, payload: dict[str, Any]
) -> tuple[Any, Any, Any]:
    supplied = payload["configuration"]
    operation = payload["operation"]
    if "seed" not in supplied:
        raise LRARefusal(
            "missing_random_seed",
            "Every host run requires an explicit reproducible seed",
        )
    if operation == "reveals" and (
        "love" in supplied or "couple_regional_draws" in supplied
    ):
        raise LRARefusal(
            "unused_lra_configuration", "REVEALS does not consume LOVE configuration"
        )
    if operation == "love" and (
        "reveals" in supplied or "couple_regional_draws" in supplied
    ):
        raise LRARefusal(
            "unused_lra_configuration", "Standalone LOVE uses its own regional settings"
        )
    regional = payload["regional"]["basin"]
    reveals_values = {
        "basin_type": regional["site_type"],
        "basin_diameter_m": regional["diameter_m"],
        "seed": supplied["seed"],
    }
    love_values = None
    if "local" in payload:
        local = payload["local"]["basin"]
        if local["site_type"] != "lake":
            raise LRARefusal(
                "unsupported_local_basin_profile",
                "The adopted LOVE facade's local-basin profile is lake only",
            )
        love_values = {
            "regional_basin_type": regional["site_type"],
            "regional_basin_diameter_m": regional["diameter_m"],
            "local_basin_diameter_m": local["diameter_m"],
            "seed": supplied["seed"],
        }
    for name, values in (("reveals", reveals_values), ("love", love_values)):
        if values is None:
            continue
        for key, value in supplied.get(name, {}).items():
            if key in values and values[key] != value:
                raise LRARefusal(
                    "configuration_evidence_conflict",
                    f"{name}.{key} differs from admitted geometry, rings or seed",
                )
            values[key] = value
    if love_values is not None and "max_ring" not in love_values:
        raise LRARefusal(
            "missing_local_ring_limit",
            "LOVE must declare max_ring separately from the full supplied regional ring set",
        )
    try:
        reveals = (
            binding.api.RevealsConfig(**reveals_values) if operation != "love" else None
        )
        love = (
            binding.api.LoveConfig(**love_values) if love_values is not None else None
        )
        if love is not None and (
            love.max_ring > len(payload["rings"])
            or (love.method == "optimized" and love.max_ring >= len(payload["rings"]))
        ):
            raise LRARefusal(
                "invalid_local_ring_limit",
                "Optimized LOVE needs regional rings beyond max_ring; all limits must lie within supplied rings",
            )
        if (
            love is not None
            and love.method == "analytical"
            and any(
                ring["terrestrial_area_m2"] != ring["ring_area_m2"]
                for ring in payload["rings"]
            )
        ):
            raise LRARefusal(
                "unsupported_analytical_land_mask",
                "Analytical LOVE assumes fully terrestrial rings; partial land masks require the optimized profile",
            )
        if (
            love is not None
            and love.method == "analytical"
            and payload["rings"][0]["inner_m"]
            <= payload["local"]["basin"]["diameter_m"] / 2
        ):
            raise LRARefusal(
                "invalid_analytical_ring_support",
                "Analytical LOVE requires ring inner distances strictly beyond the local basin radius",
            )
        paired = None
        if operation in {"lra", "series"}:
            paired = binding.api.LRAConfig(
                reveals,
                love,
                seed=supplied["seed"],
                couple_regional_draws=supplied.get("couple_regional_draws", True),
            )
    except LRARefusal:
        raise
    except (TypeError, ValueError) as exc:
        raise LRARefusal("invalid_engine_configuration", str(exc)) from exc
    return reveals, love, paired


def validate_engine_configuration(
    binding: EngineBinding, request: ValidatedRequest
) -> None:
    """Validate geometry/configuration consistency without running a reconstruction."""
    _configuration(binding, request.payload())


def reconstruct(binding: EngineBinding, request: ValidatedRequest) -> Any:
    """Invoke the selected operation; numerical errors never select another backend."""
    import pandas as pd

    payload = request.payload()
    reveals, love, paired = _configuration(binding, payload)
    tables = {
        role: pd.DataFrame(
            [[row["coordinate"], *row["counts"]] for row in payload[role]["samples"]],
            columns=["coordinate", *payload["taxa"]],
        )
        for role in ("regional", "local")
        if role in payload
    }
    parameters = pd.DataFrame(
        [
            {
                "species": row["taxon"],
                "fallspeed": row["fallspeed_m_s"],
                "ppe": row["ppe"],
                "ppe.error": row["ppe_sd"],
            }
            for row in payload["parameters"]
        ]
    )
    try:
        if payload["operation"] == "reveals":
            return binding.api.run_reveals(tables["regional"], parameters, reveals)
        rings = pd.DataFrame(
            [
                {
                    "inner": row["inner_m"],
                    "outer": row["outer_m"],
                    "mean": row["mean_m"],
                    "ring": row["ring_area_m2"],
                    "terrestrial": row["terrestrial_area_m2"],
                }
                for row in payload["rings"]
            ]
        )
        if payload["operation"] == "love":
            return binding.api.run_love(
                tables["local"], tables["regional"], parameters, rings, love
            )
        operation = (
            binding.api.run_lra_series
            if payload["operation"] == "series"
            else binding.api.run_lra
        )
        return operation(tables["local"], tables["regional"], parameters, rings, paired)
    except binding.api.LRAError as exc:
        raise LRARefusal(
            getattr(exc, "reason_code", "lra_numerical_refusal"),
            str(exc),
            diagnostics=getattr(exc, "diagnostics", None),
        ) from exc
