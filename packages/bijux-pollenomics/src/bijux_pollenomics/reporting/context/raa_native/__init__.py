"""Opt-in, country-unassigned native registry UUID cell-count context."""

from .snapshot import (
    NativeRegistryContextSnapshot,
    NativeRegistrySource,
    capture_native_registry_context,
)

__all__ = [
    "NativeRegistryContextSnapshot",
    "NativeRegistrySource",
    "capture_native_registry_context",
]
