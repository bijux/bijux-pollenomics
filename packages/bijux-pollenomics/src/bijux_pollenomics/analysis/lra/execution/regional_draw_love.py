"""Host execution for local LOVE fed by a verified multi-site draw product."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from ..engine.discovery import (
    MULTISITE_DRAW_LOVE_CAPABILITY,
    EngineBinding,
    load_engine,
)
from ..engine.errors import LRARefusal
from ..inputs.regional_draw_love import (
    read_request_regional_draw_source,
    validate_regional_draw_love_request,
)
from ..inputs.validation import ValidatedRequest
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.publication import LRAProduct, publish_result


def _reconstruct(
    binding: EngineBinding,
    request: ValidatedRequest,
    *,
    input_root: Path,
) -> Any:
    import pandas as pd

    payload = request.payload()
    source = read_request_regional_draw_source(request, input_root=input_root)
    sample = payload["local"]["samples"][0]
    local = pd.DataFrame(
        [[sample["coordinate"], *sample["counts"]]],
        columns=["coordinate", *payload["taxa"]],
    )
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
    supplied = payload["configuration"]["love"]
    try:
        config = binding.api.RegionalDrawLoveConfig(
            local_basin_diameter_m=payload["local"]["basin"]["diameter_m"],
            max_ring=supplied["max_ring"],
            repeats=supplied["repeats"],
            stochastic=supplied["stochastic"],
            seed=supplied["seed"],
            retain_samples=supplied["retain_samples"],
            ppe_error=supplied["ppe_error"],
        )
        return binding.api.run_love_from_regional_draws(
            local,
            source,
            parameters,
            rings,
            config,
            local_site_id=sample["site_id"],
            local_sample_id=sample["sample_id"],
        )
    except binding.api.LRAError as exc:
        raise LRARefusal(
            getattr(exc, "reason_code", "lra_numerical_refusal"),
            str(exc),
            diagnostics=getattr(exc, "diagnostics", None),
        ) from exc
    except (TypeError, ValueError) as exc:
        raise LRARefusal("invalid_engine_configuration", str(exc)) from exc


def validate_regional_draw_love_inputs(
    payload: Mapping[str, object], *, input_root: Path
) -> ValidatedRequest:
    """Validate request, evidence, source product and installed capability."""
    request = validate_regional_draw_love_request(payload, input_root=input_root)
    load_engine(required_capability=MULTISITE_DRAW_LOVE_CAPABILITY)
    return request


def run_regional_draw_love_request(
    payload: Mapping[str, object], *, input_root: Path, destination: Path
) -> LRAProduct:
    """Publish one exploratory local product without regional pollen placeholders."""
    request = validate_regional_draw_love_request(payload, input_root=input_root)
    binding = load_engine(required_capability=MULTISITE_DRAW_LOVE_CAPABILITY)
    identity = capture_code_identity(binding)
    result = _reconstruct(binding, request, input_root=input_root)
    validate_regional_draw_love_request(request.payload(), input_root=input_root)
    verify_code_identity(binding, identity)
    return publish_result(
        result,
        binding,
        request,
        destination=destination,
        input_root=input_root,
        code_identity=identity,
        verify_inputs=lambda: validate_regional_draw_love_request(
            request.payload(), input_root=input_root
        ),
    )
