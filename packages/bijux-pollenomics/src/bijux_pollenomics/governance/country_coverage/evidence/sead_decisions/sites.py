"""SEAD admitted-site payload validation."""

from __future__ import annotations

from collections.abc import Mapping

from ...constants import _UUID_PATTERN, CountryCoverageError
from ...decoding import (
    _coordinate,
    _integer,
    _object,
    _positive_integer,
    _required_text,
    _rows,
)


def admitted_sead_sites(
    admission: Mapping[str, object], site_document: Mapping[str, object]
) -> dict[int, tuple[str, float, float]]:
    """Validate and index the admitted SEAD site table."""
    if site_document.get("schema_version") != "sead-table-payload.v1":
        raise CountryCoverageError("SEAD site payload schema is inconsistent")
    if site_document.get("table") != "tbl_sites":
        raise CountryCoverageError("SEAD site payload table identity is inconsistent")
    site_rows = _rows(site_document, "SEAD admitted sites")
    admitted_sites: dict[int, tuple[str, float, float]] = {}
    admitted_site_uuids: set[str] = set()
    for site_row in site_rows:
        site_id = _positive_integer(site_row.get("site_id"), "SEAD admitted site_id")
        site_uuid = _required_text(site_row, "site_uuid")
        if _UUID_PATTERN.fullmatch(site_uuid) is None:
            raise CountryCoverageError("SEAD admitted site_uuid is invalid")
        latitude = _coordinate(
            site_row.get("latitude_dd"), "SEAD admitted latitude", -90, 90
        )
        longitude = _coordinate(
            site_row.get("longitude_dd"), "SEAD admitted longitude", -180, 180
        )
        if site_id in admitted_sites or site_uuid in admitted_site_uuids:
            raise CountryCoverageError("SEAD admitted sites contain duplicate identity")
        admitted_sites[site_id] = (site_uuid, latitude, longitude)
        admitted_site_uuids.add(site_uuid)
    table_counts = _object(admission.get("table_counts"), "SEAD admission table counts")
    if _integer(table_counts.get("tbl_sites"), "SEAD site payload row count") != len(
        site_rows
    ):
        raise CountryCoverageError("SEAD site payload row count does not reconcile")
    return admitted_sites
