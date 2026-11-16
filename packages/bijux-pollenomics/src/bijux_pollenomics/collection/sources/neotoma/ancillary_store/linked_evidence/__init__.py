"""Portable shared evidence metadata with explicit source and current-role scopes."""

from .sources import full_evidence_inputs, read_scoped_target, resolve_linked_evidence

__all__ = ["full_evidence_inputs", "read_scoped_target", "resolve_linked_evidence"]
