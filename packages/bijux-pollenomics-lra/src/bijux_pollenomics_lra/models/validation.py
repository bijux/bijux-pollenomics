"""Models validation for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.errors import ValidationError

DEFAULT_FALL_SPEED_PROFILE = "disqover-0.9.14-wrapper-v1"
LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE = (
    "landclimii-2016-gpm-neutral-analytical-v1"
)


def fall_speed_bounds(profile: str, distance_weighting: str) -> tuple[float, float]:
    """Return method-scoped fall-speed bounds without changing DISQOVER defaults."""
    if profile == DEFAULT_FALL_SPEED_PROFILE:
        return 0.01, 0.15
    if profile == LANDCLIM_II_GPM_ANALYTICAL_FALL_SPEED_PROFILE:
        if distance_weighting != "gpm neutral":
            raise ValidationError(
                "The LandClim II analytical fall-speed profile requires gpm neutral"
            )
        return 0.006, 0.15
    raise ValidationError("Unsupported fall-speed profile")


def validate_fall_speeds(
    values: object, profile: str, distance_weighting: str
) -> np.ndarray:
    """Validate source fall speeds in m/s without rounding or clamping."""
    speeds = vector(values, "fallspeed")
    minimum, maximum = fall_speed_bounds(profile, distance_weighting)
    if np.any((speeds < minimum) | (speeds > maximum)):
        raise ValidationError(f"fallspeed must be between {minimum} and {maximum} m/s")
    return speeds


def scalar(value: Any, name: str = "value") -> Any:
    """Return a scalar, rejecting multi-element containers."""
    if isinstance(value, (list, tuple, np.ndarray, pd.Series)):
        array = np.asarray(value)
        if array.size != 1:
            raise ValidationError(f"{name} must be scalar")
        return array.reshape(-1)[0].item()
    return value


def parameter_value(params: Mapping[str, Any], key: str, default: Any = None) -> Any:
    """Read an R-list-shaped scalar parameter."""
    return scalar(params[key], key) if key in params else default


def integer(value: Any, name: str, minimum: int = 1) -> int:
    """Validate an integer scalar."""
    value = scalar(value, name)
    if isinstance(value, (bool, np.bool_)):
        raise ValidationError(f"{name} must be an integer >= {minimum}")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be an integer >= {minimum}") from exc
    if not np.isfinite(numeric) or numeric != int(numeric) or numeric < minimum:
        raise ValidationError(f"{name} must be an integer >= {minimum}")
    return int(numeric)


def finite_number(
    value: Any,
    name: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    strict_minimum: bool = False,
) -> float:
    """Validate a finite numeric scalar and optional bounds."""
    value = scalar(value, name)
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"{name} must be a finite number") from exc
    if not np.isfinite(numeric):
        raise ValidationError(f"{name} must be a finite number")
    if minimum is not None:
        invalid = numeric <= minimum if strict_minimum else numeric < minimum
        if invalid:
            operator = ">" if strict_minimum else ">="
            raise ValidationError(f"{name} must be {operator} {minimum}")
    if maximum is not None and numeric > maximum:
        raise ValidationError(f"{name} must be <= {maximum}")
    return numeric


def vector(
    value: Any,
    name: str,
    *,
    finite: bool = True,
    nonnegative: bool = False,
    positive: bool = False,
) -> np.ndarray:
    """Return a validated non-empty one-dimensional float vector."""
    array = np.asarray(value, dtype=float)
    if array.ndim != 1 or array.size == 0:
        raise ValidationError(f"{name} must be a non-empty one-dimensional vector")
    if finite and not np.isfinite(array).all():
        raise ValidationError(f"{name} must contain only finite values")
    if nonnegative and np.any(array < 0):
        raise ValidationError(f"{name} cannot contain negative values")
    if positive and np.any(array <= 0):
        raise ValidationError(f"{name} must contain strictly positive values")
    return array


def matrix(
    value: Any,
    name: str,
    *,
    finite: bool = True,
    nonnegative: bool = False,
) -> np.ndarray:
    """Return a validated non-empty two-dimensional float matrix."""
    array = np.asarray(value, dtype=float)
    if array.ndim != 2 or 0 in array.shape:
        raise ValidationError(f"{name} must be a non-empty two-dimensional matrix")
    if finite and not np.isfinite(array).all():
        raise ValidationError(f"{name} must contain only finite values")
    if nonnegative and np.any(array < 0):
        raise ValidationError(f"{name} cannot contain negative values")
    return array


def frame(value: Any, name: str) -> pd.DataFrame:
    """Return a deep copy of a labelled, non-empty data frame."""
    if not isinstance(value, pd.DataFrame):
        raise ValidationError(f"{name} must be a pandas DataFrame")
    if value.empty:
        raise ValidationError(f"{name} cannot be empty")
    if value.columns.has_duplicates:
        raise ValidationError(f"{name} has duplicate column names")
    return value.copy(deep=True)


def normalise_parameters(
    params: pd.DataFrame,
    taxa: Sequence[str] | None = None,
    *,
    fall_speed_profile: str = DEFAULT_FALL_SPEED_PROFILE,
    distance_weighting: str = "lsm unstable",
) -> pd.DataFrame:
    """Normalise a DISQOVER-style taxon parameter table.

    Accepted layouts are either an explicit first taxon-name column (for
    example ``species`` or ``Taxon``) or an already taxon-indexed frame.
    Returned columns are lower-case and rows are aligned to ``taxa`` when
    supplied.
    """
    table = frame(params, "params")
    table.columns = [str(column).strip().lower() for column in table.columns]
    if table.columns.has_duplicates:
        raise ValidationError("params contains duplicate normalized column names")
    required = {"fallspeed", "ppe", "ppe.error"}

    first = table.columns[0]
    non_taxon_columns = required | {"lower", "upper", "weights"}
    if first not in non_taxon_columns:
        table = table.set_index(first)
    table.index = table.index.map(str)
    if table.index.has_duplicates:
        raise ValidationError("params contains duplicate taxon names")

    missing_columns = required - set(table.columns)
    if missing_columns:
        raise ValidationError(
            f"params is missing required columns: {sorted(missing_columns)}"
        )

    if taxa is not None:
        requested = list(map(str, taxa))
        missing_taxa = sorted(set(requested) - set(table.index))
        if missing_taxa:
            raise ValidationError(f"params is missing taxa: {missing_taxa}")
        table = table.loc[requested]

    validate_fall_speeds(
        table["fallspeed"].to_numpy(dtype=float),
        fall_speed_profile,
        distance_weighting,
    )
    vector(table["ppe"], "ppe", positive=True)
    vector(table["ppe.error"], "ppe.error", nonnegative=True)
    return table


def sample_counts(
    frame_or_vector: pd.DataFrame | Sequence[float] | np.ndarray,
    name: str = "pollen",
) -> tuple[np.ndarray, list[str], float]:
    """Extract one age/depth-prefixed pollen sample.

    Returns ``(counts, taxa, sample_coordinate)``.
    """
    if isinstance(frame_or_vector, pd.DataFrame):
        table = frame(frame_or_vector, name)
        if len(table) != 1 or len(table.columns) < 2:
            raise ValidationError(
                f"{name} must contain exactly one row, one coordinate column, "
                "and at least one taxon"
            )
        coordinate = finite_number(table.iloc[0, 0], f"{name} coordinate")
        taxa = list(map(str, table.columns[1:]))
        counts = vector(table.iloc[0, 1:].to_numpy(dtype=float), name, nonnegative=True)
    else:
        values = vector(frame_or_vector, name)
        if len(values) < 2:
            raise ValidationError(
                f"{name} must contain a coordinate and at least one taxon"
            )
        coordinate = finite_number(values[0], f"{name} coordinate")
        counts = vector(values[1:], name, nonnegative=True)
        taxa = [f"taxon_{index + 1}" for index in range(len(counts))]
    if counts.sum() <= 0:
        raise ValidationError(f"{name} has zero total pollen")
    return counts, taxa, coordinate


def rng_from(
    rng: None | int | np.integer | np.random.Generator = None,
) -> np.random.Generator:
    """Return an explicit NumPy random generator."""
    if isinstance(rng, np.random.Generator):
        return rng
    return np.random.default_rng(rng)


def ensure_same_taxa(*tables: pd.DataFrame) -> list[str]:
    """Require identical taxon columns after the first metadata column."""
    if not tables:
        raise ValidationError("At least one pollen table is required")
    taxa = list(map(str, tables[0].columns[1:]))
    for table in tables[1:]:
        other = list(map(str, table.columns[1:]))
        if other != taxa:
            raise ValidationError(
                "Pollen tables must contain the same taxa in the same order"
            )
    return taxa
