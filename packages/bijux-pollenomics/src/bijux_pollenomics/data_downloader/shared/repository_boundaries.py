from __future__ import annotations

import json
from pathlib import Path

from ..sources.boundaries.store import validate_boundary_collection

__all__ = ["load_repository_country_boundaries"]


def load_repository_country_boundaries(
    data_root: Path,
) -> dict[str, dict[str, object]]:
    """Load the checked-in Nordic country boundaries used by repository materializers."""
    raw_root = Path(data_root) / "boundaries" / "raw"
    boundary_specs = {
        "Denmark": "DNK",
        "Finland": "FIN",
        "Norway": "NOR",
        "Sweden": "SWE",
    }
    boundaries: dict[str, dict[str, object]] = {}
    for country, country_code in boundary_specs.items():
        slug = country.casefold()
        path = raw_root / f"{slug}.geojson"
        payload = json.loads(path.read_text(encoding="utf-8"))
        boundaries[country] = validate_boundary_collection(
            payload,
            path=path,
            country=country,
            country_code=country_code,
        )
    return boundaries
