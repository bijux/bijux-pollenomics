from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from bijux_pollenomics.evidence.sources.sead import SEAD_GOVERNED_EVIDENCE_RUN_ID


@dataclass(frozen=True)
class SeadDataReport:
    output_dir: Path
    point_count: int
    raw_path: Path
    normalized_csv_path: Path
    normalized_geojson_path: Path


SEAD_ARCHIVE_SCHEMA_VERSION = "sead-site-archive.v2"
SEAD_GOVERNED_ACQUISITION_ID = SEAD_GOVERNED_EVIDENCE_RUN_ID
SEAD_GOVERNED_EVIDENCE_RELATIVE_PATH = (
    Path("sead/normalized/acquisitions") / SEAD_GOVERNED_ACQUISITION_ID
)
SEAD_LEGACY_CHRONOLOGY_SUMMARY_RELATIVE_PATH = Path(
    "sead/normalized/chronology_claims.json"
)
