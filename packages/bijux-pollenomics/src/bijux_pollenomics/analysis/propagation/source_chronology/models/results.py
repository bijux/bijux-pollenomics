"""Context, refusal, and derivation-result models."""

from __future__ import annotations

from dataclasses import dataclass
import re

from ..constants import NODE_PRODUCER_VERSION, SOURCE_NODE_CONFIG_DIGEST
from .nodes import SourceChronologyNode
from .reconciliation import SourceNodeReconciliation


def _required_text(value: str, field_name: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError(f"{field_name} must be non-empty")
    return value


_SHA256_ID = re.compile(r"sha256:[0-9a-f]{64}")


@dataclass(frozen=True)
class SourceNodeContext:
    """Stable configuration identity for one source-native derivation."""

    config_digest: str
    source_snapshot_id: str
    build_id: str
    producer_version: str = NODE_PRODUCER_VERSION

    def __post_init__(self) -> None:
        for field_name in (
            "config_digest",
            "source_snapshot_id",
            "build_id",
            "producer_version",
        ):
            object.__setattr__(
                self,
                field_name,
                _required_text(getattr(self, field_name), field_name),
            )
        if self.config_digest != SOURCE_NODE_CONFIG_DIGEST:
            raise ValueError(
                "config_digest does not identify source chronology node configuration"
            )
        for field_name in ("config_digest", "source_snapshot_id", "build_id"):
            if _SHA256_ID.fullmatch(getattr(self, field_name)) is None:
                raise ValueError(f"{field_name} must be a canonical SHA-256 identity")

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SourceNodeAdmissionRefusal:
    """Observation excluded from source chronology-node derivation."""

    observation_id: str
    country_code: str
    reason_code: str
    chronology_reason_code: str | None = None

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SourceNodeFacetRefusal:
    """Admitted observation missing a source-owned node facet."""

    observation_id: str
    country_code: str
    node_level: str
    reason_code: str

    def as_dict(self) -> dict[str, object]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class SourceNodeDerivationResult:
    """Deterministic source-native nodes, refusals, and accounting."""

    context: SourceNodeContext
    nodes: tuple[SourceChronologyNode, ...]
    admission_refusals: tuple[SourceNodeAdmissionRefusal, ...]
    facet_refusals: tuple[SourceNodeFacetRefusal, ...]
    reconciliation: SourceNodeReconciliation
    derivation_status: str
    result_digest: str

    def as_dict(self) -> dict[str, object]:
        return {
            "context": self.context.as_dict(),
            "nodes": [node.as_dict() for node in self.nodes],
            "admission_refusals": [
                refusal.as_dict() for refusal in self.admission_refusals
            ],
            "facet_refusals": [refusal.as_dict() for refusal in self.facet_refusals],
            "reconciliation": self.reconciliation.as_dict(),
            "derivation_status": self.derivation_status,
            "result_digest": self.result_digest,
        }


__all__ = [
    "SourceNodeAdmissionRefusal",
    "SourceNodeContext",
    "SourceNodeDerivationResult",
    "SourceNodeFacetRefusal",
]
