"""Explicit complete source bindings and finite taxon-parent frontier bounds."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from ..models import NeotomaLinkedEvidence

SCHEMA = "neotoma-taxon-source-ancestry.v1"
MAX_FILES = 32768
MAX_SOURCE_BYTES = 768 * 1024 * 1024
MAX_METADATA_BYTES = 16 * 1024 * 1024
MAX_BYTES = 256 * 1024 * 1024
PART_BYTES = 2 * 1024 * 1024
HARD_PART_BYTES = 3 * 1024 * 1024
MAX_PARTS = 256


@dataclass(frozen=True)
class NeotomaTaxonAncestryLimits:
    """New frontier bounds are separate from preservation of known native edges."""

    max_additional_parent_hops: int = 32
    max_new_taxa: int = 10000
    max_source_entities: int = 10000
    max_literal_edges: int = 100000

    def validate(self) -> None:
        bounds = {
            "max_additional_parent_hops": 32,
            "max_new_taxa": 10000,
            "max_source_entities": 10000,
            "max_literal_edges": 100000,
        }
        for field, maximum in bounds.items():
            value = getattr(self, field)
            if (
                type(value) is not int
                or not 0 <= value <= maximum
                or field != "max_additional_parent_hops"
                and value == 0
            ):
                raise ValueError(
                    "Taxon ancestry requires native finite declared bounds"
                )


@dataclass(frozen=True)
class NeotomaTaxonAncestrySources:
    """Logical source identities remain portable through explicit path resolvers."""

    evidence: NeotomaLinkedEvidence
    capture_sources: Mapping[str, Path]
    source_facets: Mapping[str, Path]
    context_directory: Path
    expected_context_sha256: str
    native_archive_directory: Path
    expected_native_archive_sha256: str


DEFAULT_ANCESTRY_LIMITS = NeotomaTaxonAncestryLimits()
