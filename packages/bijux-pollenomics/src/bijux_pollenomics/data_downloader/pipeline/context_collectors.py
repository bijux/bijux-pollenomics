from __future__ import annotations

from collections.abc import Callable

from ..landclim import collect_landclim_data
from ..neotoma import collect_neotoma_data
from ..raa import collect_raa_data
from ..sead import collect_sead_data

ContextCollectFunction = Callable[..., object]

CONTEXT_COLLECT_FUNCTIONS: dict[str, ContextCollectFunction] = {
    "landclim": collect_landclim_data,
    "neotoma": collect_neotoma_data,
    "raa": collect_raa_data,
    "sead": collect_sead_data,
}


def resolve_context_collect_function(name: str) -> ContextCollectFunction:
    """Resolve a context-source collector function by tracked source name."""
    try:
        return CONTEXT_COLLECT_FUNCTIONS[name]
    except KeyError as exc:
        raise ValueError(f"Unsupported context source: {name}") from exc


__all__ = [
    "CONTEXT_COLLECT_FUNCTIONS",
    "ContextCollectFunction",
    "resolve_context_collect_function",
]
