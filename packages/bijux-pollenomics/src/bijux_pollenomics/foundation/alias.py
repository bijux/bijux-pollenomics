from __future__ import annotations

from dataclasses import dataclass

__all__ = ["CompatibilityAliasContract", "compatibility_alias_contract"]


@dataclass(frozen=True)
class CompatibilityAliasContract:
    """Contract for alias distribution behavior."""

    alias_distribution: str
    runtime_distribution: str
    alias_module: str
    runtime_module: str
    role: str


def compatibility_alias_contract() -> CompatibilityAliasContract:
    """Return the canonical compatibility alias contract."""
    return CompatibilityAliasContract(
        alias_distribution="pollenomics",
        runtime_distribution="bijux-pollenomics",
        alias_module="pollenomics",
        runtime_module="bijux_pollenomics",
        role="compatibility_alias_only",
    )
