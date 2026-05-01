from __future__ import annotations

from dataclasses import dataclass

__all__ = ["OwnershipMapEntry", "build_ownership_map"]


@dataclass(frozen=True)
class OwnershipMapEntry:
    """One ownership-map entry for contributor orientation."""

    concern: str
    owner_module: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {
            "concern": self.concern,
            "owner_module": self.owner_module,
            "reason": self.reason,
        }


def build_ownership_map() -> tuple[OwnershipMapEntry, ...]:
    """Build the canonical ownership map for core runtime concerns."""
    return (
        OwnershipMapEntry(
            concern="source_data_logic",
            owner_module="bijux_pollenomics.data_downloader",
            reason="collects and normalizes tracked evidence sources",
        ),
        OwnershipMapEntry(
            concern="candidate_ranking_logic",
            owner_module="bijux_pollenomics.analysis",
            reason="scores and ranks candidates with explicit heuristics",
        ),
        OwnershipMapEntry(
            concern="publication_logic",
            owner_module="bijux_pollenomics.reporting",
            reason="builds atlas and country publication bundles",
        ),
    )
