"""Compose exact metadata additions with their existing historical source laws."""

from __future__ import annotations

from hashlib import sha256

from .resource_publication import RESOURCE_PUBLICATION_SPANS
from .resource_routes import RESOURCE_ROUTE_SPANS


def without_resource_context_additions(name: str, current: bytes) -> bytes | None:
    """Return an exact predecessor; this function alone grants no source admission."""
    contract = RESOURCE_ROUTE_SPANS.get(name) or RESOURCE_PUBLICATION_SPANS.get(name)
    if contract is None:
        return current
    predecessor_sha256, pairs = contract
    if not any(extension in current for _, extension in pairs):
        return current
    restored = current
    for prior, extension in pairs:
        if restored.count(extension) != 1:
            return None
        restored = restored.replace(extension, prior, 1)
    if sha256(restored).hexdigest() != predecessor_sha256:
        return None
    return restored
