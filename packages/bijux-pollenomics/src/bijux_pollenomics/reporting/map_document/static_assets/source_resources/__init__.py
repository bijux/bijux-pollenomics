"""Bounded logical resource metadata for the common static Atlas transport."""

from .publication import SourceResourcePayloads, build_source_resource_payloads
from .validation import validate_source_resource_payloads

__all__ = [
    "SourceResourcePayloads",
    "build_source_resource_payloads",
    "validate_source_resource_payloads",
]
