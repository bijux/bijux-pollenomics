"""Bounded operation-owned REVEALS inputs for callers choosing capture."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_lra.models.configuration import RevealsConfig
from bijux_pollenomics_lra.models.errors import ValidationError


def _immutable_scalar(value: object) -> bool:
    if type(value) in (str, int, float, bool, type(None)):
        return True
    if isinstance(value, np.generic):
        return type(value) is value.dtype.type and value.dtype.kind in "biufSU"
    if type(value) is tuple:
        return all(_immutable_scalar(item) for item in value)
    return False


def _axis(axis: pd.Index) -> pd.Index:
    if type(axis) not in (pd.Index, pd.RangeIndex):
        raise ValidationError("REVEALS snapshot requires a plain or range index")
    if not _immutable_scalar(axis.name) or not all(
        _immutable_scalar(item) for item in axis
    ):
        raise ValidationError("REVEALS snapshot requires immutable axis labels")
    if isinstance(axis, pd.RangeIndex):
        return pd.RangeIndex(axis.start, axis.stop, axis.step, name=axis.name)
    return axis.copy(deep=True)


def _frame(value: pd.DataFrame) -> pd.DataFrame:
    if type(value) is not pd.DataFrame:
        raise ValidationError("REVEALS snapshot requires ordinary DataFrames")
    for dtype in value.dtypes:
        if type(dtype) is pd.StringDtype and dtype.storage == "python":
            continue
        if not isinstance(dtype, np.dtype) or dtype.kind not in "biufO":
            raise ValidationError(
                "REVEALS snapshot requires ordinary numeric or object columns"
            )
    for position, dtype in enumerate(value.dtypes):
        if (dtype.kind == "O" or isinstance(dtype, pd.StringDtype)) and any(
            not _immutable_scalar(item) for item in value.iloc[:, position]
        ):
            raise ValidationError("REVEALS snapshot requires immutable object cells")
    index, columns = _axis(value.index), _axis(value.columns)
    captured = value.copy(deep=True)
    captured.index, captured.columns = index, columns
    return captured


def _copy_value(value: Any, active: set[int] | None = None) -> Any:
    if _immutable_scalar(value):
        return value
    if type(value) is np.ndarray:
        if value.dtype.kind not in "biufSU":
            raise ValidationError(
                "REVEALS snapshot requires ordinary numeric draw arrays"
            )
        return value.copy(order="K")
    if type(value) in (list, tuple):
        active = set() if active is None else active
        if id(value) in active:
            raise ValidationError("REVEALS snapshot refuses cyclic inputs")
        active.add(id(value))
        items = [_copy_value(item, active) for item in value]
        active.remove(id(value))
        return items if type(value) is list else tuple(items)
    raise ValidationError("REVEALS snapshot requires supported input values")


def capture_reveals_inputs(
    pollen: pd.DataFrame,
    params: pd.DataFrame,
    config: RevealsConfig,
    ppe_draws: object | None,
    pollen_draws: object | None,
) -> tuple[pd.DataFrame, pd.DataFrame, RevealsConfig, object | None, object | None]:
    """Copy supported inputs before use; sequential capture is not atomic."""
    if type(config) is not RevealsConfig:
        raise ValidationError("REVEALS snapshot requires an ordinary RevealsConfig")
    if any(
        not _immutable_scalar(getattr(config, field.name))
        for field in fields(config)
        if field.name != "seed"
    ):
        raise ValidationError(
            "REVEALS snapshot requires immutable configuration values"
        )
    captured_seed = _copy_value(config.seed)
    captured_config = deepcopy(config)
    object.__setattr__(captured_config, "seed", captured_seed)
    return (
        _frame(pollen),
        _frame(params),
        captured_config,
        _copy_value(ppe_draws),
        _copy_value(pollen_draws),
    )
