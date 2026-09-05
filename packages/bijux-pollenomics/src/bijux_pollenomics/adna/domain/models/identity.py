"""Stable sample and locality identities for aDNA records."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdnaSampleIdentity:
    """Canonical identity namespace for one normalized ancient-DNA sample."""

    namespace: str
    stable_token: str
    accession_lineage: tuple[str, ...]


@dataclass(frozen=True)
class AdnaLocalityIdentity:
    """Canonical shared locality anchor for species-aware ancient-DNA records."""

    namespace: str
    stable_token: str
    locality_text: str
    political_entity: str | None
    source_anchor_tokens: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "stable_token": self.stable_token,
            "locality_text": self.locality_text,
            "political_entity": self.political_entity,
            "source_anchor_tokens": list(self.source_anchor_tokens),
        }
