"""Read exact pinned original SEAD table and claim identities."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

RUN = "sead-full-evidence-39bfff6a-ce80714e"
INDEX_SHA256 = "b9accf421059eebf95b75a8c22fd237f4d51991fbc868e79530d20a694e6cd21"
SOURCES = {
    "dating_range": ("tbl_analysis_dating_ranges", "analysis_dating_range_id"),
    "dendrochronology": ("tbl_dendro_dates", "dendro_date_id"),
    "relative_period": ("tbl_relative_dates", "relative_date_id"),
    "geochronology": ("tbl_geochronology", "geochron_id"),
    "analysis_entity_age": ("tbl_analysis_entity_ages", "analysis_entity_age_id"),
}
TABLE_KEYS = {
    **dict(SOURCES.values()),
    "tbl_analysis_values": "analysis_value_id",
    "tbl_analysis_entities": "analysis_entity_id",
    "tbl_physical_samples": "physical_sample_id",
    "tbl_sample_groups": "sample_group_id",
    "tbl_sites": "site_id",
    "tbl_datasets": "dataset_id",
    "tbl_methods": "method_id",
    "tbl_biblio": "biblio_id",
    "tbl_dating_uncertainty": "dating_uncertainty_id",
    "tbl_site_references": "site_reference_id",
    "tbl_sample_group_references": "sample_group_reference_id",
    "tbl_relative_age_refs": "relative_age_ref_id",
}


def index_rows(rows: list[dict[str, Any]], key: str) -> dict[int, dict[str, Any]]:
    """Index native rows by unique nonnegative integer identifiers."""
    result: dict[int, dict[str, Any]] = {}
    for row in rows:
        value = row.get(key)
        if type(value) is not int or value < 0 or value in result:
            raise ValueError("Invalid or duplicated native identifier: " + key)
        result[value] = row
    return result


def _read(
    path: Path, expected: str, inputs: dict[str, str], root: Path
) -> dict[str, Any]:
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected:
        raise ValueError("Native annotation input digest differs: " + str(path))
    inputs[path.relative_to(root).as_posix()] = digest
    value: Any = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Native source document is not an object")
    return value
