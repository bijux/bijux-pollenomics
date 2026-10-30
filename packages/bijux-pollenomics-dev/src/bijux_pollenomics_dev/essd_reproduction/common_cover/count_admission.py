"""Preserve nested mask provenance at the owned sample-count ingress."""

from __future__ import annotations

from collections.abc import Iterator

import numpy as np

from bijux_pollenomics_lra.models.errors import ValidationError
from bijux_pollenomics_lra.reconstruction.likelihood import multisite_likelihood


def require_unmasked(value: object, name: str) -> None:
    """Refuse hidden masks and cycles without recursive Python calls or coercion."""
    frames: list[tuple[Iterator[object], int | None]] = [(iter((value,)), None)]
    active: set[int] = set()
    while frames:
        iterator, parent = frames[-1]
        try:
            item = next(iterator)
        except StopIteration:
            frames.pop()
            if parent is not None:
                active.remove(parent)
            continue
        multisite_likelihood._require_unmasked(item, name)
        if isinstance(item, (list, tuple)):
            children = iter(item)
        elif isinstance(item, np.ndarray) and item.dtype.kind == "O":
            children = iter(item.flat)
        else:
            continue
        identity = id(item)
        if identity in active:
            raise ValidationError(
                f"{name} contains cyclic containers",
                reason_code="common_cover_cyclic_input",
            )
        active.add(identity)
        frames.append((children, identity))


def matrix(value: object, name: str) -> np.ndarray:
    """Reuse common-cover Boolean, complex and typed numeric admission unchanged."""
    require_unmasked(value, name)
    return multisite_likelihood._input_matrix(value, name)
