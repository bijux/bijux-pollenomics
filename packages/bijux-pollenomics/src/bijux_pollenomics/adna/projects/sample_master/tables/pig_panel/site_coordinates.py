"""Governed site-level coordinate anchors for archive-proven pig samples."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import cast

PIG_SITE_COORDINATE_EVIDENCE_PATH = (
    "adna/species/sus_scrofa_domesticus/raw/site_coordinate_evidence.json"
)
_EXPECTED_IDENTITIES = {
    "AA015": ("SAMEA5160867", "Bundsø"),
    "AA016": ("SAMEA5160868", "Trelleborg"),
}
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True)
class PigSiteCoordinateEvidence:
    """One sample-to-site join and separately sourced site-level point."""

    sample_label: str
    archive_native_sample_id: str
    locality_text: str
    political_entity: str
    latitude_text: str
    longitude_text: str
    coordinate_basis: str
    coordinate_confidence: str
    spatial_scope: str
    sample_site_source_path: str
    sample_site_source_locator: str
    sample_site_source_url: str
    coordinate_source_url: str
    coordinate_context_url: str
    coordinate_source_locator: str
    coordinate_source_kind: str
    coordinate_source_sha256: str
    confidence_rationale: str


def load_pig_site_coordinate_evidence(
    data_root: Path,
) -> tuple[PigSiteCoordinateEvidence, ...]:
    """Load and validate the two governed pig site anchors."""
    path = Path(data_root) / PIG_SITE_COORDINATE_EVIDENCE_PATH
    payload = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(payload, dict):
        raise ValueError("Pig site-coordinate evidence must be a JSON object")
    if payload.get("schema_version") != "pig-sample-site-coordinate-evidence.v1":
        raise ValueError("Pig site-coordinate evidence schema version is unsupported")
    if payload.get("project_accession") != "PRJEB30282":
        raise ValueError("Pig site-coordinate evidence must belong to PRJEB30282")
    raw_records = payload.get("records")
    if not isinstance(raw_records, list):
        raise ValueError("Pig site-coordinate evidence records must be a list")
    records = tuple(_parse_record(item) for item in raw_records)
    observed = {record.sample_label for record in records}
    if observed != set(_EXPECTED_IDENTITIES) or len(records) != len(observed):
        raise ValueError(
            "Pig site-coordinate evidence must contain AA015 and AA016 exactly once"
        )
    return tuple(sorted(records, key=lambda record: record.sample_label))


def _parse_record(value: object) -> PigSiteCoordinateEvidence:
    if not isinstance(value, dict):
        raise ValueError("Pig site-coordinate evidence record must be an object")
    required = tuple(PigSiteCoordinateEvidence.__dataclass_fields__)
    if set(value) != set(required):
        raise ValueError("Pig site-coordinate evidence record fields do not match")
    strings: dict[str, str] = {}
    for field in required:
        item = value[field]
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"Pig site-coordinate evidence {field} must be non-empty")
        strings[field] = item.strip()
    record = PigSiteCoordinateEvidence(**strings)
    expected = _EXPECTED_IDENTITIES.get(record.sample_label)
    if expected != (record.archive_native_sample_id, record.locality_text):
        raise ValueError(
            f"Pig site-coordinate identity drift for {record.sample_label}"
        )
    _validate_coordinate(record)
    if record.political_entity != "Denmark":
        raise ValueError("Pig site-coordinate evidence must preserve Denmark")
    if record.coordinate_basis != "named_site_geocoding":
        raise ValueError("Pig site coordinates must be classified as site geocoding")
    if record.coordinate_confidence != "approximate":
        raise ValueError("Pig site coordinates must remain approximate")
    if "not_specimen_findspot" not in record.spatial_scope:
        raise ValueError(
            "Pig site coordinates must disclaim specimen-findspot precision"
        )
    if not _SHA256_RE.fullmatch(record.coordinate_source_sha256):
        raise ValueError("Pig coordinate source digest must be lowercase SHA-256")
    for url in (
        record.sample_site_source_url,
        record.coordinate_source_url,
        record.coordinate_context_url,
    ):
        if not url.startswith("https://"):
            raise ValueError("Pig site-coordinate evidence URLs must use HTTPS")
    return record


def _validate_coordinate(record: PigSiteCoordinateEvidence) -> None:
    try:
        latitude = float(record.latitude_text)
        longitude = float(record.longitude_text)
    except ValueError as error:
        raise ValueError("Pig site coordinates must be numeric") from error
    if not math.isfinite(latitude) or not -90 <= latitude <= 90:
        raise ValueError("Pig site latitude must be finite and in range")
    if not math.isfinite(longitude) or not -180 <= longitude <= 180:
        raise ValueError("Pig site longitude must be finite and in range")


__all__ = [
    "PIG_SITE_COORDINATE_EVIDENCE_PATH",
    "PigSiteCoordinateEvidence",
    "load_pig_site_coordinate_evidence",
]
