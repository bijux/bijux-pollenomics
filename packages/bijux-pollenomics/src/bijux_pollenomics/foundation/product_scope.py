from __future__ import annotations

from dataclasses import dataclass

__all__ = ["ProductScope", "build_product_scope"]


@dataclass(frozen=True)
class ProductScope:
    """Current runtime scope and explicit non-claims."""

    current_product_mode: str
    roadmap_mode: str
    current_capabilities: tuple[str, ...]
    not_yet_supported_claims: tuple[str, ...]

    def as_dict(self) -> dict[str, object]:
        return {
            "current_product_mode": self.current_product_mode,
            "roadmap_mode": self.roadmap_mode,
            "current_capabilities": self.current_capabilities,
            "not_yet_supported_claims": self.not_yet_supported_claims,
        }


def build_product_scope() -> ProductScope:
    """Build the canonical product-scope statement."""
    return ProductScope(
        current_product_mode="atlas_builder",
        roadmap_mode="future_engine",
        current_capabilities=(
            "collect and normalize Nordic context evidence",
            "publish country and atlas report bundles",
            "emit heuristic candidate ranking artifacts",
        ),
        not_yet_supported_claims=(
            "full pollenomics scientific decision engine",
            "integrated aDNA, eDNA, pollen, and archaeology co-analysis runtime",
            "paper-grade inferential statistics workflows",
        ),
    )
