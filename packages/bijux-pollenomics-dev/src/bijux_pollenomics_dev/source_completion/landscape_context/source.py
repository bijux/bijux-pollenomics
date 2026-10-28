"""Read immutable native feature identities and the original two-lake supports."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .geodesic import point

PREPARED = "docs/report/pollen-reconstruction/swedish-direct-pollen/prepared"
FEATURES = "data/sead/derived/sweden_archaeology_site_discovery.geojson"
ORIGINAL = "docs/report/countries/sweden/observed-pollen-trajectory/report.json"
LINEAGE = "docs/report/countries/sweden/pollen-model-lineage/report.json"
ALTERNATE = (55.44559, 13.80172)
BIN_IDS = tuple(range(-1, 12))


@dataclass(frozen=True)
class Record:
    """One source feature; records at the same site never become a site hull."""

    identifier: str
    site_uuid: str
    coordinate: tuple[float, float]
    lower: float | None
    upper: float | None
    status: str
    claim_ids: tuple[str, ...]
    uncertainty_notes: tuple[str, ...]
    properties_sha256: str
    precision: str
    comparability: str


def age(value: object) -> float | None:
    """Preserve nullable finite native ages and refuse other types."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("Native age is neither null nor numeric")
    if not math.isfinite(value):
        raise ValueError("Nonfinite native age")
    return float(value)


def text_list(value: object) -> tuple[str, ...]:
    """Require textual native identities and preserve their order."""
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError("Native textual identity array required")
    return tuple(value)


def overlap(lower: float | None, upper: float | None, start: int, end: int) -> bool:
    """Preserve original half-open bins, including its separate point-age branch."""
    if lower is None or upper is None or lower > upper:
        return False
    if lower == upper:
        return start <= lower < end
    return lower < end and upper > start


def load(
    root: Path,
) -> tuple[list[Record], dict[str, tuple[float, float]], dict[str, Any]]:
    """Load pinned trajectory features, centres and shared-grid lineage."""
    original: dict[str, Any] = json.loads((root / ORIGINAL).read_bytes())
    for item in original["inputs"]:
        path = root / item["path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Original trajectory source epoch differs")
    lineage = json.loads((root / LINEAGE).read_bytes())
    if lineage["targets_sharing_bus_boke_grid"] != 5:
        raise ValueError("Shared modeled-grid779 lineage changed")
    centres = {}
    bin_sets = []
    for label, dataset in [("BUS", 53995), ("BOKE", 54001)]:
        data = json.loads((root / PREPARED / f"dataset-{dataset}.json").read_bytes())
        bin_sets.append(set(map(int, data["bins"])))
        if data["sample_age_bounds_present"]:
            raise ValueError("Original thirteen point-age bin supports changed")
        centres[label] = point(data["latitude"], data["longitude"])
    if set.intersection(*bin_sets) != set(BIN_IDS):
        raise ValueError("Original thirteen shared bins changed")
    centres["BUS_inventory"] = ALTERNATE
    features = json.loads((root / FEATURES).read_bytes())["features"]
    if len(features) != 8799:
        raise ValueError("Original8799feature population changed")
    records = []
    seen = set()
    for feature in features:
        geometry = feature["geometry"]
        if geometry["type"] != "Point" or len(geometry["coordinates"]) != 2:
            raise ValueError("Original native point geometry changed")
        lon, lat = geometry["coordinates"]
        properties = feature["properties"]
        identifier, uuid = properties["record_id"], properties["site_uuid"]
        if (
            not isinstance(identifier, str)
            or not isinstance(uuid, str)
            or not uuid
            or identifier in seen
        ):
            raise ValueError("Missing/duplicate source feature identity")
        seen.add(identifier)
        lower, upper = (
            age(properties.get("time_start_bp")),
            age(properties.get("time_end_bp")),
        )
        if lower is not None and upper is not None and lower > upper:
            raise ValueError("Reversed native feature interval")
        semantics = properties["temporal_semantics"]
        if lower != age(semantics.get("time_start_bp")) or upper != age(
            semantics.get("time_end_bp")
        ):
            raise ValueError("Outer/native temporal semantics disagree")
        status = "numeric" if lower is not None and upper is not None else "unresolved"
        records.append(
            Record(
                identifier,
                uuid,
                point(lat, lon),
                lower,
                upper,
                status,
                text_list(semantics.get("chronology_claim_ids", [])),
                text_list(semantics.get("uncertainty_notes", [])),
                hashlib.sha256(
                    json.dumps(
                        properties,
                        sort_keys=True,
                        ensure_ascii=False,
                        allow_nan=False,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest(),
                str(semantics["precision_posture"]),
                str(semantics["comparability_posture"]),
            )
        )
    return records, centres, original
