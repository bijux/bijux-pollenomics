"""Conditional observation uncertainty with independently declared pollen effort."""

from __future__ import annotations

import re
from collections.abc import Mapping
from fractions import Fraction
from math import comb, fsum, isfinite
from numbers import Real

import numpy as np
import scipy
from scipy.stats import binom

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.models.observation import (
    PROFILE,
    PollenObservationDraws,
    _probability_closure,
)
from bijux_pollenomics_lra.models.validation import integer
from bijux_pollenomics_lra.provenance.identity import canonical_json, sha256_object
from bijux_pollenomics_lra.version import NUMERICAL_BACKEND, __version__


def _digest(value: str, name: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationError(f"{name} requires a canonical SHA-256")
    return value


def _integer(value: int, name: str, minimum: int, maximum: int) -> int:
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValidationError(f"{name} requires an integer in [{minimum}, {maximum}]")
    return integer(value, name, minimum)


def _probabilities(values: Mapping[str, float]) -> tuple[tuple[str, ...], np.ndarray]:
    if not isinstance(values, Mapping) or not 1 <= len(values) <= 128:
        raise ValidationError("Require 1–128 explicitly named pollen fractions")
    if any(not isinstance(k, str) or not k or k != k.strip() for k in values):
        raise ValidationError("Taxa require exact nonempty string identities")
    taxa = tuple(sorted(values))
    if any(
        isinstance(values[k], (bool, np.bool_)) or not isinstance(values[k], Real)
        for k in taxa
    ):
        raise ValidationError("Fractions require numeric scalars, excluding booleans")
    try:
        probabilities = np.asarray([values[k] for k in taxa], dtype=float)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError(
            "Pollen fractions must be finite bounded numbers"
        ) from exc
    if (
        not np.isfinite(probabilities).all()
        or np.any(probabilities < 0)
        or np.any(probabilities > 1)
    ):
        raise ValidationError("Pollen fractions must lie between zero and one")
    if abs(fsum(probabilities) - 1) > 1e-12:
        raise ValidationError("Pollen fractions must close to one, not percentages")
    return taxa, probabilities


def _exact_cdf(k: int, n: int, p: float) -> Fraction:
    if k < 0:
        return Fraction(0)
    if k >= n:
        return Fraction(1)
    a, b = p.as_integer_ratio()
    numerator = sum(comb(n, j) * a**j * (b - a) ** (n - j) for j in range(k + 1))
    return Fraction(numerator, b**n)


def _quantile(q: float, n: int, p: float) -> int:
    if p == 0:
        return 0
    if p == 1:
        return n
    value = float(binom.ppf(q, n, p))
    if not isfinite(value) or value != int(value) or not 0 <= value <= n:
        raise ValidationError("Binomial quantile provider returned an invalid count")
    k = int(value)
    if n <= 256:
        # Finite binary64 probabilities are exact rationals. Check both discrete
        # boundaries without inheriting provider rounding at a probability tie.
        target = Fraction.from_float(q)
        while k > 0 and _exact_cdf(k - 1, n, p) >= target:
            k -= 1
        while k < n and _exact_cdf(k, n, p) < target:
            k += 1
        return k
    below, above = float(binom.cdf(k - 1, n, p)), float(binom.cdf(k, n, p))
    # Large-support exact integers are deliberately bounded out of this profile.
    # Do not choose a discrete endpoint at an unresolved numerical boundary.
    if (
        not isfinite(below)
        or not isfinite(above)
        or not below <= above
        or q - below <= 1e-12
        or above - q <= 1e-12
    ):
        raise ValidationError(
            "Large-support binomial quantile boundary is numerically unresolved",
            reason_code="observation_interval_boundary_unresolved",
        )
    return k


def sample_pollen_observations(
    pollen_fraction: Mapping[str, float],
    *,
    effort: int,
    repeats: int,
    seed: int,
    coverage: float,
    prediction_sha256: str,
    effort_evidence_sha256: str,
) -> PollenObservationDraws:
    """Draw joint multinomial counts and checked binomial marginal predictive bounds.

    The host must supply prediction identity and sampling-effort evidence frozen
    before target observation access. This numerical function cannot authenticate
    those external declarations. It accepts no observed target counts. Fractions
    and effort are conditioned on as fixed; model/PPE/chronology/geometry error
    is not propagated and these are not intervals for vegetation or parameters.

    Sorted taxa make input order irrelevant. Binary64 closure divides by the
    supplied sum and assigns the final rounding residual to the largest category;
    input and effective probabilities both survive in the result. Discrete
    marginal coverage can exceed the nominal level; joint simultaneous coverage
    is not claimed. Joint count rows preserve multinomial dependence between taxa.
    """
    effort = _integer(effort, "effort", 1, 2**31 - 1)
    repeats = _integer(repeats, "repeats", 2, 10_000)
    seed = _integer(seed, "seed", 0, 2**32 - 1)
    if isinstance(coverage, (bool, np.bool_)) or not isinstance(coverage, Real):
        raise ValidationError("Coverage must be a finite numeric scalar")
    try:
        level = float(coverage)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValidationError("Coverage must be a finite bounded number") from exc
    alpha = (1 - level) / 2
    if not isfinite(level) or not 0 < alpha < 0.5 or not 0 < level < 1:
        raise ValidationError("Coverage must lie strictly between zero and one")
    prediction_sha256 = _digest(prediction_sha256, "prediction_sha256")
    effort_evidence_sha256 = _digest(effort_evidence_sha256, "effort_evidence_sha256")
    taxa, original = _probabilities(pollen_fraction)
    if repeats * len(taxa) > 1_000_000:
        raise ValidationError("Requested joint draw storage exceeds one million cells")
    order, ordered_probabilities = _probability_closure(
        tuple(float(value) for value in original)
    )
    effective = np.asarray(ordered_probabilities, dtype=float)
    restored = np.argsort(order)
    probabilities = effective[restored]
    declaration = {
        "profile": PROFILE,
        "taxa": taxa,
        "input_pollen_fraction": dict(zip(taxa, original.tolist(), strict=True)),
        "effective_pollen_fraction": dict(
            zip(taxa, probabilities.tolist(), strict=True)
        ),
        "closure_profile": "binary64-normalize-largest-residual-v1",
        "effort": effort,
        "effort_evidence_sha256": effort_evidence_sha256,
        "prediction_sha256": prediction_sha256,
        "repeats": repeats,
        "seed": seed,
        "coverage": level,
        "rng": "numpy.random.Generator(PCG64)",
        "numpy_version": np.__version__,
        "scipy_version": scipy.__version__,
        "engine_version": __version__,
        "numerical_backend": NUMERICAL_BACKEND,
    }
    identity = sha256_object(declaration)
    generator = np.random.Generator(np.random.PCG64(seed))
    counts = generator.multinomial(effort, effective, size=repeats)[:, restored]
    lower = np.asarray(
        [_quantile(alpha, effort, float(p)) for p in probabilities], dtype=float
    )
    upper = np.asarray(
        [_quantile(1 - alpha, effort, float(p)) for p in probabilities], dtype=float
    )
    if (
        not np.isfinite(lower).all()
        or not np.isfinite(upper).all()
        or np.any(lower < 0)
        or np.any(upper > effort)
        or np.any(lower > upper)
    ):
        raise ValidationError("Conditional binomial interval computation failed")
    result = {
        "schema_version": "lra-pollen-observation-draws.v1",
        "profile": PROFILE,
        "declaration": declaration,
        "declaration_sha256": identity,
        "draw_ids": [f"{identity}:{i}" for i in range(repeats)],
        "counts": counts.tolist(),
        "count_units": "pollen_grains",
        "draw_scope": "joint_multinomial_taxon_counts",
        "marginal_predictive_intervals": {
            taxon: {
                "lower_count": int(lo),
                "upper_count": int(hi),
                "lower_fraction": float(lo / effort),
                "upper_fraction": float(hi / effort),
            }
            for taxon, lo, hi in zip(taxa, lower, upper, strict=True)
        },
        "interval_profile": "fixed-probability-binomial-equal-tail-v1",
        "interval_kind": "conditional_predictive_observation",
        "interval_numeric_profile": "exact-rational-boundary-v1"
        if effort <= 256
        else "scipy-cdf-separated-boundary-v1",
        "numerical_boundary_separation": 1e-12 if effort > 256 else 0.0,
        "sampling_probability_note": "Declared binary64 inputs are passed to NumPy; internal sequential subtraction may differ by floating-point rounding.",
        "propagated_sources": ["observation_process"],
        "conditioned_on": ["fixed_pollen_probabilities", "predeclared_sampling_effort"],
        "not_propagated": [
            "model_fitting",
            "spatial_model",
            "PPE",
            "chronology",
            "geometry",
            "regional_reconstruction",
            "local_reconstruction",
            "effort_uncertainty",
            "overdispersion",
        ],
        "simultaneous_coverage_claimed": False,
        "empirical_coverage_verified": False,
        "scientific_acceptance": "not_evaluated",
        "r_source_parity_claimed": False,
    }
    return PollenObservationDraws(canonical_json(result), sha256_object(result))
