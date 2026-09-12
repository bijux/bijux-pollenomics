"""Provenance identity for the LRA engine."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, is_dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def _canonical(value: Any) -> Any:
    """Convert supported scientific objects into stable JSON data."""
    if is_dataclass(value) and not isinstance(value, type):
        return _canonical(asdict(value))
    if isinstance(value, pd.DataFrame):
        return {
            "__type__": "dataframe",
            "columns": [str(column) for column in value.columns],
            "index": [str(index) for index in value.index],
            "data": [
                [_canonical(item) for item in row]
                for row in value.to_numpy(dtype=object).tolist()
            ],
            "dtypes": [str(dtype) for dtype in value.dtypes],
        }
    if isinstance(value, pd.Series):
        return {
            "__type__": "series",
            "name": None if value.name is None else str(value.name),
            "index": [str(index) for index in value.index],
            "data": [_canonical(item) for item in value.tolist()],
            "dtype": str(value.dtype),
        }
    if isinstance(value, np.ndarray):
        return {
            "__type__": "ndarray",
            "shape": list(value.shape),
            "dtype": str(value.dtype),
            "data": [_canonical(item) for item in value.ravel(order="C").tolist()],
        }
    if isinstance(value, np.generic):
        return _canonical(value.item())
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): _canonical(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canonical(item) for item in value]
    if isinstance(value, float):
        if np.isnan(value):
            return "NaN"
        if np.isposinf(value):
            return "Infinity"
        if np.isneginf(value):
            return "-Infinity"
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    return repr(value)


def canonical_json(value: Any) -> str:
    """Serialise to deterministic compact JSON."""
    return json.dumps(
        _canonical(value),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )


def sha256_object(value: Any) -> str:
    """Hash a supported object using canonical JSON representation."""
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    """Hash a file without loading it all into memory."""
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()
