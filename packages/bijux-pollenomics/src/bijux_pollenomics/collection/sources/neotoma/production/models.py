from __future__ import annotations

from dataclasses import asdict, dataclass
import math

from .constants import (
    PRODUCTION_CONFIG_SCHEMA,
    PRODUCTION_DRIVER_ID,
    PRODUCTION_DRIVER_VERSION,
)


@dataclass(frozen=True)
class NeotomaProductionConfig:
    """Content-affecting configuration included in the production build identity."""

    producer_id: str = PRODUCTION_DRIVER_ID
    producer_version: str = PRODUCTION_DRIVER_VERSION
    config_schema: str = PRODUCTION_CONFIG_SCHEMA
    rows_per_part: int = 50_000
    proximity_tolerance: float = 0.15
    raw_country_aliases: tuple[tuple[str, str], ...] = ()

    def validated(self) -> NeotomaProductionConfig:
        """Return this configuration after checking deterministic identity fields."""
        for label, value in (
            ("producer_id", self.producer_id),
            ("producer_version", self.producer_version),
            ("config_schema", self.config_schema),
        ):
            if not value.strip():
                raise ValueError(f"{label} must not be empty")
        if self.rows_per_part < 1:
            raise ValueError("rows_per_part must be at least 1")
        if not math.isfinite(self.proximity_tolerance) or self.proximity_tolerance < 0:
            raise ValueError("proximity_tolerance must be finite and non-negative")
        aliases = dict(self.raw_country_aliases)
        if len(aliases) != len(self.raw_country_aliases):
            raise ValueError("raw_country_aliases must not contain duplicate keys")
        if any(not key.strip() or not value.strip() for key, value in aliases.items()):
            raise ValueError("raw_country_aliases must contain non-empty text")
        return self


@dataclass(frozen=True)
class NeotomaProductionReport:
    """Stable gate report for one successfully published production snapshot."""

    manifest_path: str
    source_snapshot_id: str
    boundary_authority_id: str
    build_id: str
    raw_part_count: int
    raw_row_count: int
    site_count: int
    country_counts: dict[str, int]
    country_decision_counts: dict[str, int]

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable report."""
        return asdict(self)


@dataclass(frozen=True)
class _RawArchive:
    rows: tuple[dict[str, object], ...]
    source_snapshot_id: str
    part_digests: tuple[str, ...]


@dataclass(frozen=True)
class _BoundaryAuthority:
    boundaries: dict[str, dict[str, object]]
    artifact_digest: str
    version: str
    authority_id: str
