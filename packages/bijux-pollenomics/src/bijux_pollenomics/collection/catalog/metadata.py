from __future__ import annotations

from datetime import UTC, date, datetime
import json
from pathlib import Path
from typing import cast

from ..contracts.models import SourceAcquisitionMetadata
from ..sources.boundaries.collection import NATURAL_EARTH_VERSION

__all__ = ["build_repository_source_metadata", "build_source_metadata"]

_UNAVAILABLE = "unavailable"

_SOURCE_LICENSES: dict[str, str] = {
    "aadr": "source-specific terms",
    "boundaries": "Natural Earth public domain",
    "landclim": "source-specific terms",
    "neotoma": "source-specific terms",
    "raa": "open data terms",
    "sead": "source-specific terms",
    "svar": "open data terms",
}

_SOURCE_VERSIONS: dict[str, str] = {
    "boundaries": NATURAL_EARTH_VERSION,
}

_DATED_SOURCE_RECEIPTS: dict[str, tuple[str, dict[str, str]]] = {
    "boundaries": (
        "raw/source_manifest.json",
        {
            "schema_version": "natural-earth-boundary-receipt.v1",
            "source": "Natural Earth",
        },
    ),
    "landclim": (
        "raw/landclim_sources.json",
        {"schema_version": "landclim-raw-receipt.v1", "source": "LandClim"},
    ),
    "neotoma": (
        "raw/neotoma_pollen_dataset_downloads/manifest.json",
        {
            "source": "Neotoma",
            "endpoint_template": (
                "https://api.neotomadb.org/v2.0/data/downloads/{datasetid}"
            ),
        },
    ),
    "svar": (
        "raw/svar_lake_registry_manifest.json",
        {
            "source": "SMHI SVAR",
            "wfs_url": "https://vattenwebb.smhi.se/svarwebb/svar.map",
        },
    ),
}

_SEAD_EVIDENCE_MANIFEST_SCHEMA = "sead-evidence-materialization-manifest.v1"
_SEAD_RECEIPT_SCHEMA = "sead-scoped-acquisition-receipt.v1"


def build_source_metadata(
    *, selected_sources: tuple[str, ...], version: str
) -> dict[str, SourceAcquisitionMetadata]:
    """Build source acquisition metadata for every selected source."""
    retrieved_on = str(date.today())
    metadata: dict[str, SourceAcquisitionMetadata] = {}
    for source in selected_sources:
        metadata[source] = SourceAcquisitionMetadata(
            source=source,
            version=_SOURCE_VERSIONS.get(source, version),
            license=_SOURCE_LICENSES.get(source, "source-specific terms"),
            retrieved_on=retrieved_on,
            acquisition_method="collector_pipeline",
        )
    return metadata


def build_repository_source_metadata(
    *,
    selected_sources: tuple[str, ...],
    version: str,
    source_output_roots: dict[str, str],
) -> dict[str, SourceAcquisitionMetadata]:
    """Recover acquisition metadata from immutable repository source receipts."""
    metadata: dict[str, SourceAcquisitionMetadata] = {}
    for source in selected_sources:
        source_root = Path(source_output_roots[source])
        retrieved_on, acquisition_method = _repository_acquisition(source, source_root)
        metadata[source] = SourceAcquisitionMetadata(
            source=source,
            version=_SOURCE_VERSIONS.get(source, version),
            license=_SOURCE_LICENSES.get(source, "source-specific terms"),
            retrieved_on=retrieved_on,
            acquisition_method=acquisition_method,
        )
    return metadata


def _repository_acquisition(source: str, source_root: Path) -> tuple[str, str]:
    if source == "sead":
        return _sead_acquisition(source_root)
    receipt_spec = _DATED_SOURCE_RECEIPTS.get(source)
    if receipt_spec is None:
        return _UNAVAILABLE, _UNAVAILABLE
    relative_path, expected_values = receipt_spec
    payload = _read_json_object(source_root / relative_path)
    if payload is None or any(
        payload.get(field) != expected for field, expected in expected_values.items()
    ):
        return _UNAVAILABLE, _UNAVAILABLE
    retrieved_on = _date_value(payload.get("generated_on"))
    if retrieved_on is None:
        return _UNAVAILABLE, _UNAVAILABLE
    return retrieved_on, _UNAVAILABLE


def _sead_acquisition(source_root: Path) -> tuple[str, str]:
    manifests = tuple(
        sorted(
            (source_root / "normalized" / "acquisitions").glob(
                "*/evidence_materialization_manifest.json"
            )
        )
    )
    if len(manifests) != 1:
        return _UNAVAILABLE, _UNAVAILABLE
    manifest = _read_json_object(manifests[0])
    if manifest is None or manifest.get("schema_version") != (
        _SEAD_EVIDENCE_MANIFEST_SCHEMA
    ):
        return _UNAVAILABLE, _UNAVAILABLE
    source_run_id = manifest.get("source_run_id")
    if not isinstance(source_run_id, str) or not source_run_id:
        return _UNAVAILABLE, _UNAVAILABLE
    if manifests[0].parent.name != source_run_id:
        return _UNAVAILABLE, _UNAVAILABLE

    receipt_paths = tuple(
        sorted(
            (source_root / "raw" / "acquisitions" / source_run_id / "receipts").glob(
                "*.json"
            )
        )
    )
    if not receipt_paths:
        return _UNAVAILABLE, _UNAVAILABLE
    completed_at: list[datetime] = []
    routes: set[str] = set()
    for receipt_path in receipt_paths:
        receipt = _read_json_object(receipt_path)
        if receipt is None or any(
            (
                receipt.get("schema_version") != _SEAD_RECEIPT_SCHEMA,
                receipt.get("source") != "SEAD",
                receipt.get("status") != "complete",
            )
        ):
            return _UNAVAILABLE, _UNAVAILABLE
        completed = _datetime_value(receipt.get("completed_at"))
        route = receipt.get("route")
        if completed is None or not isinstance(route, str) or not route:
            return _UNAVAILABLE, _UNAVAILABLE
        completed_at.append(completed)
        routes.add(route)
    if len(routes) != 1:
        return _UNAVAILABLE, _UNAVAILABLE
    return max(completed_at).date().isoformat(), routes.pop()


def _read_json_object(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return cast(dict[str, object], payload)


def _date_value(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        return date.fromisoformat(value).isoformat()
    except ValueError:
        return None


def _datetime_value(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(UTC) if parsed.tzinfo is not None else None
