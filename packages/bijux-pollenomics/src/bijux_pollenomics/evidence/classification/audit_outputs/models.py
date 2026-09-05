"""Classification-audit path, result, and refusal models."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import MANIFEST_NAME


class ClassificationAuditRefusalError(ValueError):
    """Refuse an unsafe or scientifically inconsistent audit publication."""

    def __init__(self, reason_code: str, detail: str) -> None:
        self.reason_code = reason_code
        super().__init__(detail)


@dataclass(frozen=True)
class ClassificationAuditOutputPaths:
    """Every governed output path required for one atomic audit bundle."""

    output_root: Path
    accepted_mapping_queue: Path
    concept_denominators: Path
    country_partitions: Path
    not_applicable_mapping_queue: Path
    observation_memberships: Path
    observation_denominators: Path
    release_metadata: Path
    review_queue: Path
    unmapped_mapping_queue: Path
    manifest: Path

    @classmethod
    def under(cls, output_root: Path) -> ClassificationAuditOutputPaths:
        """Declare the complete fixed path set below one output root."""
        output_root = Path(output_root)
        return cls(
            output_root=output_root,
            accepted_mapping_queue=output_root / "accepted_mapping_queue.json",
            concept_denominators=output_root / "concept_denominators.json",
            country_partitions=output_root / "country_partitions.json",
            not_applicable_mapping_queue=(
                output_root / "not_applicable_mapping_queue.json"
            ),
            observation_memberships=output_root / "observation_memberships.json",
            observation_denominators=output_root / "observation_denominators.json",
            release_metadata=output_root / "release_metadata.json",
            review_queue=output_root / "review_queue.json",
            unmapped_mapping_queue=output_root / "unmapped_mapping_queue.json",
            manifest=output_root / MANIFEST_NAME,
        )

    def payload_paths(self) -> tuple[Path, ...]:
        return (
            self.accepted_mapping_queue,
            self.concept_denominators,
            self.country_partitions,
            self.not_applicable_mapping_queue,
            self.observation_memberships,
            self.observation_denominators,
            self.release_metadata,
            self.review_queue,
            self.unmapped_mapping_queue,
        )


@dataclass(frozen=True)
class ClassificationAuditMaterializationResult:
    """Observable disposition and identity for one audit materialization."""

    output_root: Path
    disposition: str
    manifest_sha256: str
    file_count: int
    concept_count: int
    observation_count: int
    accepted_mapping_count: int
    release_status: str
