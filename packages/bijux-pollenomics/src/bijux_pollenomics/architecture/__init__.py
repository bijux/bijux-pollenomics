"""Repository structure, ownership, and public compatibility contracts."""

from .compatibility import CompatibilityAliasContract, compatibility_alias_contract
from .ownership import OwnershipMapEntry, build_ownership_map
from .product import ProductScope, build_product_scope
from .repository import (
    ArchitectureStage,
    CrossTreeSurfaceContract,
    PackageOwnershipContract,
    RepositoryArchitectureContract,
    build_repository_architecture_contract,
)
from .runtime import RuntimeSurfaceContract, runtime_surface_contract
from .surfaces import SurfaceMap, build_surface_map

__all__ = [
    "ArchitectureStage",
    "CompatibilityAliasContract",
    "CrossTreeSurfaceContract",
    "OwnershipMapEntry",
    "PackageOwnershipContract",
    "ProductScope",
    "RepositoryArchitectureContract",
    "RuntimeSurfaceContract",
    "SurfaceMap",
    "build_ownership_map",
    "build_product_scope",
    "build_repository_architecture_contract",
    "build_surface_map",
    "compatibility_alias_contract",
    "runtime_surface_contract",
]
