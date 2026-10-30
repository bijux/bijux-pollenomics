"""Independently admit original count/area bytes, axes and source coordinates."""

from __future__ import annotations

from collections.abc import Sequence
import csv
from decimal import Decimal
import hashlib
import io
import math
from pathlib import Path
import re

from .verification_math import Vector, require

D = Decimal
Counts = dict[str, tuple[int, ...]]
Areas = dict[tuple[str, int], Vector]
Coordinates = dict[str, tuple[Decimal, Decimal]]
AreaTokens = dict[tuple[str, int], tuple[str, ...]]

SOURCES = {
    "PANGAEA.931033.tab": "73c62c335a227283c27a224304b52fd21d1c674f95551d58a2e42dffa325a2e1",
    "PANGAEA.931035.tab": "b2460910d5f72e234fef50a24c4ade08e57ab714bf482ba4afb3b4ed8e7b4f2a",
}
TAXA = ("Acacia", "Dichrostachys", "Grewia", "Poaceae", "Combretaceae")
COUNT_COLUMNS = ("Aca [#]", "Dichrostachys [#]", "Grewia [#]", "Poac [#]", "Comeae [#]")
AREA_COLUMNS = (
    "Acacia [m**2]",
    "Dichrostachys [m**2]",
    "Grewia [m**2]",
    "Poaceae [m**2]",
    "Combretaceae [m**2]",
)
EVENTS = tuple(f"Namibia_T{i}" for i in range(1, 11))
RADII = tuple(range(100, 1501, 100))
GROUPS = (
    ("Namibia_T1",),
    ("Namibia_T2",),
    ("Namibia_T3",),
    ("Namibia_T4", "Namibia_T5"),
    ("Namibia_T6",),
    ("Namibia_T7",),
    ("Namibia_T8",),
    ("Namibia_T9",),
    ("Namibia_T10",),
)
METHODS = ("empirical", "area_only", "training_mean", "nearest_site")
METRICS = ("mean_nll", "mae", "hellinger_squared")
CSV_FIELDS = (
    "radius_label_m",
    "heldout_site",
    "heldout_group",
    "fit_id",
    "training_sites",
    "training_grains",
    "fit_status",
    "fit_stop_reason",
    "fit_steps",
    "fit_score_residual",
    "fit_relative_count_residual",
    "fit_minimum_relative_information",
    "fit_information_resolution_floor",
    "fit_hessian_condition_number",
    "empirical_status",
    "empirical_reason",
    "nearest_site",
    "nearest_distance_m",
    *(f"observed_{t}" for t in TAXA),
    *(f"area_m2_{t}" for t in TAXA),
    *(f"response_multiplier_{t}" for t in TAXA),
    *(f"{m}_{t}" for m in METHODS for t in TAXA),
    *(f"{m}_{metric}" for m in METHODS for metric in METRICS),
    *(
        f"empirical_minus_{baseline}_{metric}"
        for baseline in METHODS[1:]
        for metric in METRICS
    ),
)


def read_sources(source_dir: Path) -> tuple[Counts, Areas, Coordinates, AreaTokens]:
    """Authenticate and parse the original publisher tables without source execution."""
    tables: dict[str, list[dict[str, str]]] = {}
    coordinates: Coordinates = {}
    for filename, expected in SOURCES.items():
        path = source_dir / filename
        require(
            path.is_file() and not any(p.is_symlink() for p in (path, *path.parents)),
            "real original source path",
        )
        body = path.read_bytes()
        require(
            hashlib.sha256(body).hexdigest() == expected,
            "original source identity " + filename,
        )
        text = body.decode()
        require(
            "Creative Commons Attribution 4.0 International (CC-BY-4.0)" in text,
            "source attribution",
        )
        header, data = text.split("*/\n", 1)
        native_coordinates = {
            event: (D(lat), D(lon))
            for event, lat, lon in re.findall(
                r"(Namibia_T\d+) \* LATITUDE: ([\d.+-]+) \* LONGITUDE: ([\d.+-]+)",
                header,
            )
        }
        require(
            set(native_coordinates) == set(EVENTS), "source event metadata population"
        )
        if coordinates:
            require(
                native_coordinates == coordinates, "source metadata coordinates differ"
            )
        coordinates = native_coordinates
        reader = csv.DictReader(io.StringIO(data), delimiter="\t")
        expected_columns = (
            ("Event", "Latitude", "Longitude", *COUNT_COLUMNS)
            if filename.endswith("931033.tab")
            else (
                "Event",
                "Latitude",
                "Longitude",
                "Ring sect radius [m]",
                *AREA_COLUMNS,
            )
        )
        require(
            tuple(reader.fieldnames or ()) == expected_columns, "native TSV columns"
        )
        rows = list(reader)
        require(
            all(
                set(r) == set(expected_columns)
                and all(v not in (None, "") for v in r.values())
                for r in rows
            ),
            "missing source cells",
        )
        tables[filename] = rows
    pollen, vegetation = tables.values()
    require(len(pollen) == 10 and len(vegetation) == 150, "native source denominators")
    counts: Counts = {}
    areas: Areas = {}
    display: dict[str, tuple[str, str]] = {}
    area_tokens: AreaTokens = {}
    for row in pollen:
        event = row["Event"]
        require(
            event not in counts and event in EVENTS, "duplicate or foreign native event"
        )
        require(
            all(re.fullmatch(r"[0-9]+", row[k]) for k in COUNT_COLUMNS),
            "native integer count syntax",
        )
        counts[event] = tuple(int(row[k]) for k in COUNT_COLUMNS)
        display[event] = row["Latitude"], row["Longitude"]
    for row in vegetation:
        event, radius = row["Event"], int(row["Ring sect radius [m]"])
        key = event, radius
        require(
            key not in areas and event in counts and radius in RADII,
            "duplicate or foreign area support",
        )
        require(
            (row["Latitude"], row["Longitude"]) == display[event],
            "exact displayed coordinate join",
        )
        areas[key] = tuple(D(row[k]) for k in AREA_COLUMNS)
        area_tokens[key] = tuple(row[k] for k in AREA_COLUMNS)
    require(
        set(areas) == {(e, r) for e in EVENTS for r in RADII},
        "complete radius/event cross product",
    )
    require(
        all(n > 0 for row in counts.values() for n in row), "positive native counts"
    )
    require(
        all(a.is_finite() and a > 0 for row in areas.values() for a in row),
        "positive native areas",
    )
    return counts, areas, coordinates, area_tokens


def geographic_distance(left: Sequence[Decimal], right: Sequence[Decimal]) -> float:
    """Return the declared spherical distance between Decimal coordinates."""
    lat1, lon1 = map(math.radians, map(float, left))
    lat2, lon2 = map(math.radians, map(float, right))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371000 * math.asin(math.sqrt(min(1.0, max(0.0, h))))
