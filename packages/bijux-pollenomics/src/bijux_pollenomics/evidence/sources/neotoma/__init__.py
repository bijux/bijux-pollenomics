"""Governed Neotoma relational evidence contracts and readers."""

from .contract import DEFAULT_ROWS_PER_PART
from .validation import validate_neotoma_relational_materialization

read_validated_neotoma_relational_manifest = validate_neotoma_relational_materialization

__all__ = [
    "DEFAULT_ROWS_PER_PART",
    "read_validated_neotoma_relational_manifest",
    "validate_neotoma_relational_materialization",
]
