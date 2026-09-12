"""Resources examples for the LRA engine."""

from __future__ import annotations

from importlib.resources import files
import json
from typing import Any, Final

import numpy as np
import pandas as pd

DATASETS: Final[tuple[str, ...]] = (
    "Tiefer_See",
    "LOVEexamplePollen",
    "LOVEexampleParams",
    "LOVEexampleRings",
)


def _decode(value: Any) -> Any:
    if isinstance(value, dict):
        if value.get("__type__") == "dataframe":
            return pd.DataFrame(
                value["data"],
                index=value["index"],
                columns=value["columns"],
            )
        if value.get("__type__") == "array":
            return np.asarray(value["data"], dtype=value["dtype"])
        return {key: _decode(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_decode(item) for item in value]
    return value


def load_dataset(name: str) -> dict[str, Any]:
    """Return a fresh decoded copy of a bundled reference dataset."""
    if name not in DATASETS:
        raise ValueError(f"Unknown dataset {name!r}; choose one of {DATASETS}")
    resource = files("bijux_pollenomics_lra").joinpath(
        "resources", "data", f"{name}.json"
    )
    return _decode(json.loads(resource.read_text(encoding="utf-8")))


def load_love_example() -> tuple[
    pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame
]:
    """Return ready-to-run local pollen, regional pollen, parameters, and rings."""
    pollen = load_dataset("LOVEexamplePollen")["LOVEexamplePollen"]
    pollen = pollen.copy(deep=True)
    pollen.insert(0, "age", 1.0)
    params = load_dataset("LOVEexampleParams")["LOVEexampleParams"]
    rings = load_dataset("LOVEexampleRings")["LOVEexampleRings"]
    return pollen.iloc[[0]], pollen.iloc[[1]], params, rings
