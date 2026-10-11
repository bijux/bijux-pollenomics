"""Exact input identity for a standalone captured RAÄ database."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import os
from pathlib import Path
import re
import stat


@dataclass(frozen=True, slots=True)
class RaaDatabaseIdentity:
    """Pinned original file bytes, never a claim of geometry validity."""

    path: Path
    sha256: str
    byte_count: int
    stat_identity: tuple[int, int, int, int, int]

    def verify_unchanged(self) -> None:
        current = inspect_database_identity(
            self.path, expected_sha256=self.sha256, expected_byte_count=self.byte_count
        )
        if current != self:
            raise ValueError("RAÄ source database changed during inspection")


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
    for suffix in ("-wal", "-shm", "-journal"):
        auxiliary = normalized.with_name(normalized.name + suffix)
        if auxiliary.exists() or auxiliary.is_symlink():
            raise ValueError("RAÄ source must be a standalone finalized database")
    before = normalized.stat()
    if not stat.S_ISREG(before.st_mode) or before.st_size != expected_byte_count:
        raise ValueError("RAÄ source database type or byte count mismatch")
    digest = sha256()
    with normalized.open("rb") as stream:
        while content := stream.read(1048576):
            digest.update(content)
    after = normalized.stat()
    before_key = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_key = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_key != after_key or digest.hexdigest() != expected_sha256:
        raise ValueError("RAÄ source database SHA256 or snapshot identity mismatch")
    return RaaDatabaseIdentity(
        normalized, expected_sha256, expected_byte_count, after_key
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
