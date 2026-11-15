"""Dataset facets inherit source roles without inventing native schema or versions."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Any

FACETS = ("chronologies", "lithology", "projects", "publications", "taxa")

BODY = b'{"status":"success","data":[{"depth":10,"age":120}]}'


def owner() -> ModuleType:
    return importlib.import_module(
        "bijux_pollenomics.collection.sources.neotoma.capture.facets"
    )


def plan(*resources: Any, facets: tuple[str, ...] = FACETS) -> Any:
    return owner().NeotomaFacetPlan(tuple(resources), "b" * 64, facets=facets)
