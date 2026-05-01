from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "SurfaceMap",
    "build_surface_map",
]


@dataclass(frozen=True)
class SurfaceMap:
    """Short map of runtime surfaces and planned engine surfaces."""

    runtime_surfaces: tuple[str, ...]
    planned_engine_surfaces: tuple[str, ...]

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            "runtime_surfaces": self.runtime_surfaces,
            "planned_engine_surfaces": self.planned_engine_surfaces,
        }


def build_surface_map() -> SurfaceMap:
    """Build the canonical runtime-vs-roadmap surface map."""
    return SurfaceMap(
        runtime_surfaces=(
            "source collection and normalization",
            "atlas bundle publication",
            "country report publication",
            "candidate ranking artifacts (heuristic)",
        ),
        planned_engine_surfaces=(
            "multi-evidence harmonization runtime",
            "evidence-aware scoring and interpretation engine",
            "workflow stage replay and diff execution",
        ),
    )
