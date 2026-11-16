"""Exact input identity for a standalone captured RAÄ database."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re

from bijux_pollenomics.core.filesystem import BoundedInputTree


@dataclass(frozen=True, slots=True)
class RaaDatabaseIdentity:
    """Pinned original file bytes, never a claim of geometry validity."""

    path: Path
    sha256: str
    byte_count: int
    stat_identity: tuple[int, int, int, int, int]

    def verify_unchanged(self) -> None:
        """Refuse a different physical database attachment after inspection."""
        current = inspect_database_identity(
            self.path, expected_sha256=self.sha256, expected_byte_count=self.byte_count
        )
        if current != self:
            raise ValueError("RAÄ source database changed during inspection")


def check_standalone_database(path: Path) -> None:
    """Refuse auxiliary source state before any immutable native read."""
    for suffix in ("-wal", "-shm", "-journal"):
        auxiliary = path.with_name(path.name + suffix)
        if auxiliary.exists() or auxiliary.is_symlink():
            raise ValueError("RAÄ source must be a standalone finalized database")


def inspect_database_identity(
    path: Path, *, expected_sha256: str, expected_byte_count: int
) -> RaaDatabaseIdentity:
    """Refuse unsafe paths, auxiliary journals and a mismatched raw capture."""
    if not isinstance(expected_sha256, str) or not re.fullmatch(
        "[0-9a-f]{64}", expected_sha256
    ):
        raise ValueError("RAÄ source SHA256 must be explicit lowercase hexadecimal")
    if type(expected_byte_count) is not int or expected_byte_count < 1:
        raise ValueError("RAÄ source byte count must be a positive integer")
    for candidate in (path, *path.parents):
        if candidate.is_symlink():
            raise ValueError("RAÄ source database cannot use symlink paths")
    normalized = Path(os.path.abspath(path))
    for candidate in (normalized, *normalized.parents):
        if candidate.is_symlink():
            raise ValueError("RAÄ source database cannot use symlink paths")
    check_standalone_database(normalized)
    with BoundedInputTree(
        normalized.parent,
        max_bytes=expected_byte_count,
        max_files=1,
        selected=normalized.name,
    ) as tree:
        stamp = tree.files[normalized.name]
        if stamp[4] != expected_byte_count:
            raise ValueError("RAÄ source database type or byte count mismatch")
        tree.validate()
        check_standalone_database(normalized)
        if tree.digests[normalized.name] != expected_sha256:
            raise ValueError("RAÄ source database SHA256 or snapshot identity mismatch")
        key = (stamp[0], stamp[1], stamp[4], stamp[5], stamp[6])
        return RaaDatabaseIdentity(
            normalized, expected_sha256, expected_byte_count, key
        )


# Source profile inspected in the national 2026-09-12 GeoPackage.
SCHEMA_VERSION = "raa-geopackage-ownership-v1"
GEOMETRY_TYPES: dict[str, str] = {
    "point": "POINT",
    "linestring": "LINESTRING",
    "polygon": "POLYGON",
    "lämningar_sverige_lägesosäkerhet": "MULTIPOLYGON",
}
SOURCE_COLUMNS: dict[str, tuple[str, ...]] = {
    "lamning": (
        "fid",
        "uuid",
        "lamningsnummer",
        "raa_nummer",
        "lamningstyp",
        "url",
        "beskrivning",
        "publicerad_av",
        "publiceringsdatum",
        "uttagsdatum",
        "antikvariskbedomning",
        "antikvariskbedomning_motivering",
        "aktualitetstatus",
        "skadestatus",
        "undersokningsstatus",
        "placering",
        "terrang",
        "orientering",
        "tradition",
        "lamningsnamn",
        "lan",
        "kommun",
        "socken",
        "inspire_ruin",
    ),
    "ingaendelamning": ("fid", "id", "lamning_uuid", "antal", "lamningstyp"),
    "egenskap": ("fid", "id", "lamning_uuid", "ingaendelamning_id", "typ", "varde"),
    "point": ("fid", "geometri", "lamning_uuid", "geometrinummer"),
    "linestring": ("fid", "geometri", "lamning_uuid", "geometrinummer"),
    "polygon": ("fid", "geometri", "lamning_uuid", "geometrinummer"),
    "lämningar_sverige_lägesosäkerhet": (
        "fid",
        "geometri",
        "lamning_uuid",
        "lamningsnummer",
        "inmatningskvalitet",
        "definition_av_kvalitet",
        "lagesosakerhet_i_meter",
        "url",
    ),
}
BOUNDARY: dict[str, object] = {
    "scientific_admission": False,
    "canonical_source_adoption": False,
    "historical_density_equivalence": False,
    "representative_coordinates_derived": False,
    "geometry_validation": "not_evaluated",
    "chronology_admission": False,
    "country_assertion": "national_provider_scope_not_derived_country_per_row",
}
