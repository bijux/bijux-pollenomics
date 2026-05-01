from __future__ import annotations

from dataclasses import dataclass

__all__ = ["RuntimeSurfaceContract", "runtime_surface_contract"]


@dataclass(frozen=True)
class RuntimeSurfaceContract:
    """Canonical responsibility contract for the runtime distribution."""

    package_name: str
    runtime_module: str
    engine_status: str
    description: str


def runtime_surface_contract() -> RuntimeSurfaceContract:
    """Return the canonical runtime surface contract for this repository."""
    return RuntimeSurfaceContract(
        package_name="bijux-pollenomics",
        runtime_module="bijux_pollenomics",
        engine_status="atlas_builder_with_engine_roadmap",
        description=(
            "Canonical runtime surface that collects, normalizes, and publishes "
            "evidence artifacts while the full pollenomics engine remains planned."
        ),
    )
