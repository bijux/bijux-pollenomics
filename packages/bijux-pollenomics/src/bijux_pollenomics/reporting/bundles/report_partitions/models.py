"""Immutable report-partition planning and execution values."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from ...geography import PublishedGeographyPlan

ReportPartitionKind = Literal["world", "regions", "countries", "foundation"]


@dataclass(frozen=True)
class ReportPartition:
    """One independently executable portion of the published report tree."""

    identity: str
    kind: ReportPartitionKind
    scope_keys: tuple[str, ...]
    required_partition_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class PublishedReportPartitionPlan:
    """Deterministic partition inventory for one geography plan."""

    geography: PublishedGeographyPlan
    partitions: tuple[ReportPartition, ...]

    @property
    def partition_ids(self) -> tuple[str, ...]:
        """Return executable partition identities in canonical order."""
        return tuple(partition.identity for partition in self.partitions)


@dataclass(frozen=True)
class ReportPartitionResult:
    """Materialized partition identity and its complete relative-file inventory."""

    partition: ReportPartition
    output_root: Path
    relative_paths: tuple[str, ...]
