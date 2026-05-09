"""Canonical path helpers for repository-owned aDNA artifacts."""

from __future__ import annotations

from pathlib import Path

from .species import resolve_species_definition

__all__ = [
    "ADNA_FINAL_DIR",
    "ADNA_GOVERNANCE_DIR",
    "ADNA_ROOT_DIR",
    "ADNA_SOURCE_LIBRARY_DIR",
    "ADNA_SPECIES_DIR",
    "adna_final_root",
    "adna_governance_root",
    "adna_root",
    "adna_source_library_root",
    "adna_species_dir",
    "adna_species_root",
]

ADNA_ROOT_DIR = "data/adna"
ADNA_SPECIES_DIR = f"{ADNA_ROOT_DIR}/species"
ADNA_GOVERNANCE_DIR = f"{ADNA_ROOT_DIR}/governance"
ADNA_FINAL_DIR = f"{ADNA_ROOT_DIR}/final"
ADNA_SOURCE_LIBRARY_DIR = f"{ADNA_GOVERNANCE_DIR}/source_library"


def adna_root(data_root: Path) -> Path:
    """Return the repository root directory for tracked aDNA data."""
    return Path(data_root) / "adna"


def adna_species_dir(data_root: Path) -> Path:
    """Return the directory that contains all species-specific aDNA trees."""
    return adna_root(data_root) / "species"


def adna_governance_root(data_root: Path) -> Path:
    """Return the governed ledger directory for cross-species aDNA artifacts."""
    return adna_root(data_root) / "governance"


def adna_final_root(data_root: Path) -> Path:
    """Return the directory for shipped aDNA outputs."""
    return adna_root(data_root) / "final"


def adna_source_library_root(data_root: Path) -> Path:
    """Return the root for captured article and archive source evidence."""
    return adna_governance_root(data_root) / "source_library"


def adna_species_root(data_root: Path, species_name: str) -> Path:
    """Return the normalized output root for one tracked species."""
    species = resolve_species_definition(species_name)
    return adna_species_dir(data_root) / species.slug
