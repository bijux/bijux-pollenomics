"""Host-owned entry points for validated optional-engine execution."""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from ..engine.discovery import load_engine
from ..inputs.validation import ValidatedRequest, validate_request
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.publication import LRAProduct, publish_result
from .adapter import reconstruct, validate_engine_configuration


def validate_lra_inputs(
    payload: Mapping[str, object], *, input_root: Path
) -> ValidatedRequest:
    """Validate source bytes and engine configuration without computing estimates."""
    request = validate_request(payload, input_root=input_root)
    validate_engine_configuration(load_engine(), request)
    return request


def run_lra_request(
    payload: Mapping[str, object], *, input_root: Path, destination: Path
) -> LRAProduct:
    """Compute one exploratory product from a reproducible source-compatible request."""
    request = validate_request(payload, input_root=input_root)
    binding = load_engine()
    identity = capture_code_identity(binding)
    result = reconstruct(binding, request)
    # A source disappearing or changing during the calculation invalidates output.
    validate_request(request.payload(), input_root=input_root)
    verify_code_identity(binding, identity)
    return publish_result(
        result, binding, request, destination=destination, code_identity=identity
    )
