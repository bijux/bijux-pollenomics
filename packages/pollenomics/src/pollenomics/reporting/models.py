"""Compatibility facade for canonical reporting models."""

from bijux_pollenomics.reporting.models import *  # noqa: F403

__all__ = [name for name in globals() if not name.startswith("_")]
