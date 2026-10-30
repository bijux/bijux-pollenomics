"""Reuse the authenticated Namibia publisher tables without new source copies."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import math
from pathlib import Path
import re
import runpy
from typing import Any

from ....ci.report_rebuild.source_paths import safe_source_file
from ....ci.report_rebuild.source_qualification import validated_external_report_sources
from ..namibia_source_join import DESCRIPTOR, REPLAY

TAXA = ("Acacia", "Dichrostachys", "Grewia", "Poaceae", "Combretaceae")
SITES = tuple(f"Namibia_T{i}" for i in range(1, 11))
RADII = tuple(range(100, 1501, 100))
GROUPS = (
    tuple((s,) for s in SITES[:3])
    + (("Namibia_T4", "Namibia_T5"),)
    + tuple((s,) for s in SITES[5:])
)
SPHERE_RADIUS_M = 6_371_000


@dataclass(frozen=True)
class NativeSource:
    """Original native counts, area tokens and event-header coordinates."""

    counts: Mapping[str, tuple[int, ...]]
    areas: Mapping[tuple[str, int], tuple[float, ...]]
    area_tokens: Mapping[tuple[str, int], tuple[str, ...]]
    coordinates: Mapping[str, tuple[float, float]]


def distance(first: tuple[float, float], second: tuple[float, float]) -> float:
    """Use the declared spherical distance, not a recovered image-sector mask."""
    lat1, lon1, lat2, lon2 = map(math.radians, (*first, *second))
    h = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * SPHERE_RADIUS_M * math.asin(math.sqrt(min(1.0, max(0.0, h))))


def event_coordinates(text: str) -> dict[str, tuple[str, str]]:
    """Keep the six-decimal metadata coordinates distinct from table displays."""
    pattern = r"^(?:Event\(s\):\t|\t)(Namibia_T[0-9]+) \* LATITUDE: (-?[0-9.]+) \* LONGITUDE: (-?[0-9.]+) \*"
    rows = re.findall(pattern, text.split("*/\n", 1)[0], re.MULTILINE)
    coordinates = {site: (lat, lon) for site, lat, lon in rows}
    if len(rows) != 10 or set(coordinates) != set(SITES):
        raise ValueError("Namibia event metadata coordinate identities differ")
    return coordinates


def assemble(
    pollen: list[dict[str, str]],
    vegetation: list[dict[str, str]],
    coordinate_tokens: Mapping[str, tuple[str, str]],
    taxa: Any,
) -> NativeSource:
    """Require the declared complete positive source panel and every native radius."""
    if (
        len(pollen) != 10
        or len(vegetation) != 150
        or tuple(row[0] for row in taxa) != TAXA
    ):
        raise ValueError("Namibia native table or taxon population differs")
    counts: dict[str, tuple[int, ...]] = {}
    displays: dict[str, tuple[str, str]] = {}
    for row in pollen:
        event = row["Event"]
        tokens = tuple(row[entry[1]] for entry in taxa)
        if (
            event in counts
            or event not in SITES
            or any(not re.fullmatch(r"[0-9]+", token) for token in tokens)
        ):
            raise ValueError("Namibia native count key or integer token differs")
        values = tuple(int(token) for token in tokens)
        if any(value <= 0 for value in values):
            raise ValueError(
                "Namibia study requires positive measured five-taxon counts"
            )
        counts[event] = values
        displays[event] = (row["Latitude"], row["Longitude"])
    if set(counts) != set(SITES) or sum(map(sum, counts.values())) != 6894:
        raise ValueError("Namibia unique grain denominator differs")
    areas, tokens_by_key = {}, {}
    for row in vegetation:
        event, radius_token = row["Event"], row["Ring sect radius [m]"]
        if not re.fullmatch(r"[0-9]+", radius_token):
            raise ValueError("Namibia native radius token differs")
        key = (event, int(radius_token))
        if (
            key in areas
            or event not in counts
            or key[1] not in RADII
            or displays[event] != (row["Latitude"], row["Longitude"])
        ):
            raise ValueError("Namibia native event/radius/coordinate join differs")
        tokens = tuple(row[entry[2]] for entry in taxa)
        if any(
            not re.fullmatch(
                r"[+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?", token
            )
            for token in tokens
        ):
            raise ValueError("Namibia native mapped area token differs")
        try:
            decimals = tuple(Decimal(token) for token in tokens)
            area_values = tuple(float(value) for value in decimals)
        except (InvalidOperation, ValueError, OverflowError) as exc:
            raise ValueError("Namibia native mapped area token differs") from exc
        if any(not value.is_finite() or value <= 0 for value in decimals) or any(
            not math.isfinite(value) or value <= 0 for value in area_values
        ):
            raise ValueError(
                "Namibia study requires positive finite native mapped areas"
            )
        areas[key], tokens_by_key[key] = area_values, tokens
    if set(areas) != {(site, radius) for site in SITES for radius in RADII}:
        raise ValueError("Namibia complete site/radius support differs")
    coordinates = {
        site: (float(coordinate_tokens[site][0]), float(coordinate_tokens[site][1]))
        for site in SITES
    }
    if any(
        not all(math.isfinite(v) for v in point)
        or not -90 <= point[0] <= 90
        or not -180 <= point[1] <= 180
        for point in coordinates.values()
    ):
        raise ValueError("Namibia metadata coordinates are invalid")
    overlaps = [
        (a, b)
        for i, a in enumerate(SITES)
        for b in SITES[i + 1 :]
        if distance(coordinates[a], coordinates[b]) <= 3000
    ]
    if overlaps != [("Namibia_T4", "Namibia_T5")]:
        raise ValueError("Namibia nominal 1.5 km overlap groups differ")
    return NativeSource(counts, areas, tokens_by_key, coordinates)


def load(repository: Path, source_store: Path) -> NativeSource:
    """Read the existing qualified publisher packet through its maintained join reader."""
    qualified = validated_external_report_sources(repository, source_store, DESCRIPTOR)
    reader = runpy.run_path(
        str(safe_source_file(repository, REPLAY, "Namibia publisher join reader")),
        run_name="bijux_namibia_pollen_inputs",
    )
    pollen_path, vegetation_path = (
        qualified.directory / name
        for name in ("PANGAEA.931033.tab", "PANGAEA.931035.tab")
    )
    pollen = reader["_read_source"](pollen_path, reader["POLLEN_COLUMNS"])
    vegetation = reader["_read_source"](vegetation_path, reader["VEGETATION_COLUMNS"])
    first = event_coordinates(pollen_path.read_text())
    if first != event_coordinates(vegetation_path.read_text()):
        raise ValueError("Namibia original metadata coordinate spellings differ")
    return assemble(pollen, vegetation, first, reader["TAXA"])
