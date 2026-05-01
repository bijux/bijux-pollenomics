from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "SourceSupportStatus",
    "build_source_support_matrix",
]


@dataclass(frozen=True)
class SourceSupportStatus:
    source: str
    support_status: str
    country_coverage: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "source": self.source,
            "support_status": self.support_status,
            "country_coverage": self.country_coverage,
        }


def build_source_support_matrix() -> tuple[SourceSupportStatus, ...]:
    """Build support-status and country-coverage rows for tracked sources."""
    nordic = ("Denmark", "Finland", "Norway", "Sweden")
    return (
        SourceSupportStatus("aadr", "implemented", nordic),
        SourceSupportStatus("boundaries", "implemented", nordic),
        SourceSupportStatus("landclim", "implemented", nordic),
        SourceSupportStatus("neotoma", "implemented", nordic),
        SourceSupportStatus("raa", "implemented", ("Sweden",)),
        SourceSupportStatus("sead", "implemented", nordic),
    )
