"""Descriptor-bound writes and closed ordinary file namespaces."""

from .namespaces import validate_regular_namespace
from .owned_writes import OwnedTreeWriter

__all__ = ["OwnedTreeWriter", "validate_regular_namespace"]
