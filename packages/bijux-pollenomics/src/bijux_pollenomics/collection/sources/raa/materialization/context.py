"""Lazy native-source context, independently scoped from historical WFS density."""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path
import sqlite3
from typing import cast

from ..geometry.binary import describe_geometry
from ..geometry.crs import inspect_crs
from ..inventory import decode_source_object
from .contracts import GEOMETRY_TYPES, SOURCE_COLUMNS
from .reading import quote_identifier, read_only_database, source_profile

SOURCE_ID = "raa/lamningar-v1"
SOURCE_PATH = SOURCE_ID + "/lamningar_sverige.gpkg"
SOURCE_URL = (
    "https://pub.raa.se/nedladdning/datauttag/lamningar_v1/l%c3%a4mningar_sverige.gpkg"
)
RIGHTS_URL = "https://catalog.raa.se/store/1/resource/217"
RIGHTS_VERSION = "3.0 (2026-02-02)"
RIGHTS_SCOPE = "RAÄ Kulturhistoriska lämningar product description v3.0 (2026-02-02) declares the dataset Public Domain with no access restriction; cite source and capture date on redistribution. Separately linked media are outside this decision."


def _metadata(descriptor: Mapping[str, object]) -> dict[str, object]:
    if (
        descriptor.get("private_source_root_relative_path") != SOURCE_PATH
        or descriptor.get("download_url") != SOURCE_URL
        or descriptor.get("rights_authority_url") != RIGHTS_URL
        or descriptor.get("rights_authority_version") != RIGHTS_VERSION
        or descriptor.get("rights_status") != RIGHTS_SCOPE
    ):
        raise ValueError("RAÄ native context source/rights authority differs")
    if (
        descriptor.get("scientific_admission") is not False
        or descriptor.get("canonical_adoption") is not False
    ):
        raise ValueError("RAÄ original capture nonadmission history differs")
    identity = {
        key: descriptor.get(key)
        for key in ("sha256", "byte_count", "captured_at_utc", "http_last_modified")
    }
    if (
        not isinstance(identity["sha256"], str)
        or len(identity["sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in identity["sha256"])
        or type(identity["byte_count"]) is not int
        or identity["byte_count"] <= 0
        or any(
            not isinstance(identity[key], str) or not identity[key]
            for key in ("captured_at_utc", "http_last_modified")
        )
    ):
        raise ValueError("RAÄ native context capture identity is incomplete")
    return identity


def _context_profile(
    descriptor: Mapping[str, object], counts: Mapping[str, int]
) -> dict[str, object]:
    identity = _metadata(descriptor)
    if set(counts) != set(SOURCE_COLUMNS) or any(
        type(value) is not int or value < 0 for value in counts.values()
    ):
        raise ValueError("RAÄ native context table denominators differ")
    return {
        "profile_id": SOURCE_ID + "/native-source-context",
        "source_id": SOURCE_ID,
        "status": "admitted_source_context",
        "evidence_role": "source_context_only",
        "source_identity": identity,
        "source_record_count": counts["lamning"],
        "native_table_row_counts": dict(counts),
        "geometry_occurrence_counts_by_role": {
            "native_remains_geometry": sum(
                counts[name] for name in ("point", "linestring", "polygon")
            ),
            "positional_uncertainty": counts["lämningar_sverige_lägesosäkerhet"],
        },
        "coordinate_reference": "declared EPSG:3006; native XY easting/northing",
        "country_scope": "Swedish national provider scope; no per-record country assignment inferred",
        "rights_authority_url": RIGHTS_URL,
        "rights_authority_version": RIGHTS_VERSION,
        "rights_scope": RIGHTS_SCOPE,
        "scientific_admission": False,
        "chronology_admission": False,
        "event_admission": False,
        "legacy_density_admission": False,
        "publication_admission": False,
        "archaeological_interpretation_admission": False,
    }


class RaaNativeSourceContext:
    """Read original table fields without materializing another national copy."""

    def __init__(
        self, connection: sqlite3.Connection, profile: dict[str, object]
    ) -> None:
        self.connection = connection
        self._profile = profile

    @property
    def profile(self) -> dict[str, object]:
        return deepcopy(self._profile)

    def rows(self, table: str) -> Iterator[dict[str, object]]:
        """Preserve every native value, including raw geometry bytes, null and zero."""
        if table not in SOURCE_COLUMNS:
            raise ValueError("RAÄ native context requires an owned base table")
        for row in self.connection.execute(
            f"SELECT * FROM {quote_identifier(table)} ORDER BY fid"
        ):
            yield dict(row)

    def geometry_rows(self, table: str) -> Iterator[dict[str, object]]:
        """Expose native geometry roles and explicit payload refusals, never repair."""
        if table not in GEOMETRY_TYPES:
            raise ValueError("RAÄ native geometry context requires a geometry table")
        for row in self.rows(table):
            geometry = describe_geometry(
                row.pop("geometri"), geometry_type=GEOMETRY_TYPES[table]
            )
            yield {
                "source_fields": row,
                "geometry_role": "positional_uncertainty"
                if table == "lämningar_sverige_lägesosäkerhet"
                else "native_remains_geometry",
                "geometry": geometry,
                "scientific_admission": False,
            }


@contextmanager
def open_raa_source_context(
    source_path: Path, descriptor: Mapping[str, object]
) -> Iterator[RaaNativeSourceContext]:
    """Admit original source facts only; historical WFS matching is unrelated."""
    identity = _metadata(descriptor)
    with read_only_database(
        source_path,
        expected_sha256=cast(str, identity["sha256"]),
        expected_byte_count=cast(int, identity["byte_count"]),
    ) as connection:
        inspected = source_profile(connection)
        if inspect_crs(inspected)["status"] != "declared_crs_verified":
            raise ValueError("RAÄ native context declared CRS refused")
        tables = cast(dict[str, dict[str, object]], inspected["tables"])
        counts = {name: cast(int, tables[name]["row_count"]) for name in SOURCE_COLUMNS}
        yield RaaNativeSourceContext(connection, _context_profile(descriptor, counts))


def _read(path: Path) -> dict[str, object]:
    if (
        any(part.is_symlink() for part in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_size > 512 * 1024
    ):
        raise ValueError("RAÄ compact qualification source path differs")
    return decode_source_object(path.read_text(encoding="utf-8"))


def qualified_raa_context_profile(data_root: Path) -> dict[str, object] | None:
    """Observe the existing reader result without promoting the legacy density row."""
    descriptor_path = data_root / "raa/raw/national_geopackage_source.json"
    if not descriptor_path.exists() and not descriptor_path.is_symlink():
        return None
    refused: dict[str, object] = {
        "profile_id": SOURCE_ID + "/native-source-context",
        "source_id": SOURCE_ID,
        "status": "not_admitted",
        "evidence_role": "source_context_only",
        "source_record_count": None,
        "scientific_admission": False,
        "chronology_admission": False,
        "event_admission": False,
        "legacy_density_admission": False,
        "publication_admission": False,
        "archaeological_interpretation_admission": False,
        "reason_codes": ["missing_or_invalid_native_context_qualification"],
    }
    try:
        descriptor = _read(descriptor_path)
        identity = _metadata(descriptor)
        report_root = (
            data_root.parent / "reports/science/archaeology-native-reconciliation"
        )
        population = _read(report_root / "report.json")
        geometry = _read(report_root / "geometry.json")
        summary = cast(dict[str, object], population["native_ownership_summary"])
        tables = cast(dict[str, dict[str, object]], summary["tables"])
        counts = {
            name: cast(int, tables[name]["source_rows"]) for name in SOURCE_COLUMNS
        }
        profile = _context_profile(descriptor, counts)
        geometry_summary = cast(dict[str, object], geometry["native_geometry_summary"])
        geometry_tables = cast(dict[str, dict[str, object]], geometry_summary["tables"])
        boundary = cast(dict[str, object], geometry_summary["boundary"])
        if (
            population.get("source_identity") != identity
            or geometry.get("source_identity") != identity
            or population.get("source_context_profile") != profile
            or population.get("scientific_admission") is not False
            or population.get("chronology_admission") is not False
            or any(
                boundary.get(key) is not False
                for key in (
                    "scientific_admission",
                    "chronology_admission",
                    "canonical_source_adoption",
                )
            )
            or geometry_summary.get("crs_status") != "declared_crs_verified"
            or any(
                geometry_tables[name]["source_rows"] != counts[name]
                for name in GEOMETRY_TYPES
            )
            or geometry_summary.get("geometry_occurrences")
            != sum(counts[name] for name in GEOMETRY_TYPES)
        ):
            raise ValueError("RAÄ native context qualification identity/scope differs")
        return profile
    except (
        OSError,
        UnicodeDecodeError,
        ValueError,
        KeyError,
        TypeError,
        AttributeError,
    ):
        return refused


__all__ = [
    "RaaNativeSourceContext",
    "open_raa_source_context",
    "qualified_raa_context_profile",
]
