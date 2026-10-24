"""Fresh same-seed host/engine calls, retaining one exploratory reference product."""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields, is_dataclass
import math
from pathlib import Path
from time import perf_counter
from typing import Any

from ..engine.discovery import load_engine, required_capability_for_profile
from ..engine.errors import LRARefusal
from ..inputs.validation import validate_request
from ..outputs.identity import capture_code_identity, verify_code_identity
from ..outputs.publication import publish_result
from .adapter import reconstruct, validate_engine_configuration


def _same_result(reference: Any, actual: Any, path: str = "result") -> None:
    """Compare public values and existing scientific manifests, never timestamps."""
    import numpy as np
    import pandas as pd

    if type(reference) is not type(actual):
        raise AssertionError(f"{path}: result type differs")
    if path.endswith(".manifest") and callable(
        getattr(reference, "scientific_identity", None)
    ):
        if (
            not callable(getattr(actual, "scientific_identity", None))
            or reference.scientific_identity() != actual.scientific_identity()
        ):
            raise AssertionError(f"{path}: scientific identity differs")
    elif isinstance(reference, pd.DataFrame):
        pd.testing.assert_frame_equal(reference, actual, check_exact=True)
    elif isinstance(reference, pd.Series):
        pd.testing.assert_series_equal(reference, actual, check_exact=True)
    elif isinstance(reference, np.ndarray):
        if reference.shape != actual.shape or reference.dtype != actual.dtype:
            raise AssertionError(f"{path}: array axes or dtype differ")
        np.testing.assert_array_equal(reference, actual)
    elif is_dataclass(reference) and not isinstance(reference, type):
        for field in fields(reference):
            _same_result(
                getattr(reference, field.name),
                getattr(actual, field.name),
                f"{path}.{field.name}",
            )
    elif isinstance(reference, Mapping):
        if reference.keys() != actual.keys():
            raise AssertionError(f"{path}: keys differ")
        for key in reference:
            _same_result(reference[key], actual[key], f"{path}.{key}")
    elif isinstance(reference, (list, tuple)):
        if len(reference) != len(actual):
            raise AssertionError(f"{path}: lengths differ")
        for index, (left, right) in enumerate(zip(reference, actual, strict=True)):
            _same_result(left, right, f"{path}[{index}]")
    elif (
        isinstance(reference, (str, int, float, bool, np.generic)) or reference is None
    ):
        if (
            isinstance(reference, (float, np.floating))
            and math.isnan(reference)
            and math.isnan(actual)
        ):
            return
        if reference != actual:
            raise AssertionError(f"{path}: values differ")
    else:
        raise LRARefusal(
            "lra_benchmark_result_unsupported",
            f"Unsupported public result field: {path}",
        )


def benchmark_lra_request(
    payload: Mapping[str, object],
    *,
    input_root: Path,
    destination: Path,
    repeats: int = 3,
) -> dict[str, Any]:
    """Time 2..10 fresh adapter/numerical calls; publish only the first reference.

    Every call constructs independent inputs from the same immutable validated
    request and explicit seed. Stochastic calls repeat the same seeded experiment,
    not independent Monte Carlo draws. Input/code checks, comparisons and final
    serialization are outside individual call timings. The process and installed
    engine stay loaded: these are neither cold-start nor optimizer warm-start
    measurements. No speedup, incremental RSS or scientific acceptance follows.
    """
    started = perf_counter()
    if type(repeats) is not int or not 2 <= repeats <= 10:
        raise LRARefusal(
            "invalid_lra_benchmark_repeats",
            "Benchmark repeats must be an integer from 2 to 10",
        )
    if destination.exists() or destination.is_symlink():
        raise LRARefusal("lra_output_exists", str(destination))
    request = validate_request(payload, input_root=input_root)
    settings = request.payload()
    binding = load_engine(
        required_capability=required_capability_for_profile(settings["method_profile"])
    )
    validate_engine_configuration(binding, request)
    identity = capture_code_identity(binding)
    setup_seconds = perf_counter() - started
    calls: list[float] = []
    completed = 0
    reference = None
    try:
        for _ in range(repeats):
            began = perf_counter()
            try:
                result = reconstruct(binding, request)
            finally:
                calls.append(perf_counter() - began)
            completed += 1
            validate_request(request.payload(), input_root=input_root)
            verify_code_identity(binding, identity)
            if reference is None:
                # Engines may reuse mutable arrays/results. Detach the reference
                # before another call can mutate that engine-owned object.
                reference = deepcopy(result)
            else:
                try:
                    _same_result(reference, result)
                except AssertionError as exc:
                    raise LRARefusal(
                        "lra_benchmark_nonrepeatable",
                        f"Same-seed scientific result differs on call {completed}: {exc}",
                    ) from exc
            del result
        began = perf_counter()
        product = publish_result(
            reference,
            binding,
            request,
            destination=destination,
            input_root=input_root,
            code_identity=identity,
        )
        publication_seconds = perf_counter() - began
    except (Exception, KeyboardInterrupt) as exc:
        reason = (
            exc.reason_code
            if isinstance(exc, LRARefusal)
            else "lra_benchmark_interrupted"
            if isinstance(exc, KeyboardInterrupt)
            else "lra_benchmark_failed"
        )
        raise LRARefusal(
            reason,
            str(exc) or "Benchmark interrupted",
            diagnostics={
                "engine": binding.as_dict(),
                "request_sha256": request.sha256,
                "attempted_calls": len(calls),
                "completed_calls": completed,
                "call_seconds": calls,
                "cause": exc.diagnostics
                if isinstance(exc, LRARefusal)
                else {"exception_type": type(exc).__name__},
            },
        ) from exc
    return {
        "status": "benchmarked_exploratory",
        "scientific_acceptance": "not_evaluated",
        "operation": settings["operation"],
        "method_profile": settings["method_profile"],
        "request_sha256": request.sha256,
        "engine": binding.as_dict(),
        "seed": settings["configuration"]["seed"],
        "repeats": repeats,
        "timing_scope": "Fresh adapter conversion and numerical call in one loaded process; same seed, no host result cache or optimizer warm start",
        "repeatability": "exact public result content and existing scientific manifests",
        "setup_seconds": setup_seconds,
        "first_call_seconds": calls[0],
        "repeated_call_seconds": calls[1:],
        "publication_seconds": publication_seconds,
        "total_elapsed_seconds": perf_counter() - started,
        "directory": str(product.directory),
        "manifest_sha256": product.manifest_sha256,
        "scientific_content_sha256": product.scientific_content_sha256,
    }
