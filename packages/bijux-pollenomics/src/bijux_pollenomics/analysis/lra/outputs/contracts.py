"""Request-owned metadata and schemas for saved numerical tables."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


def request_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    """Project descriptive product fields from their single request authority."""
    return {
        **{
            key: payload[key]
            for key in (
                "purpose",
                "data_kind",
                "method_profile",
                "operation",
                "evidence",
                "versions",
                "temporal_matching",
                "exclusions",
                "uncertainty_omissions",
            )
        },
        "retained_taxa": payload["taxa"],
        "included_sample_count": sum(
            len(payload[role]["samples"])
            for role in ("regional", "local")
            if role in payload
        ),
        "excluded_record_count": len(payload["exclusions"]),
        "units": {
            "regional_cover": "percent",
            "local_cover": "fraction",
            "distance": "metre",
            "age_support": "typed BP intervals; present=1950 CE",
        },
    }


def _table(path: Path) -> tuple[list[str], list[list[str]]]:
    try:
        with path.open(newline="", encoding="utf-8") as stream:
            rows = list(csv.reader(stream, strict=True))
    except csv.Error as exc:
        raise ValueError(f"Malformed numerical CSV: {path.name}") from exc
    if (
        len(rows) < 2
        or not rows[0]
        or len(set(rows[0])) != len(rows[0])
        or any(not column for column in rows[0])
        or any(len(row) != len(rows[0]) for row in rows[1:])
    ):
        raise ValueError(f"Malformed numerical table: {path.name}")
    return rows[0], rows[1:]


def _number(value: str, *, nullable: bool = False) -> float | None:
    if nullable and value == "":
        return None
    number = float(value)
    if not math.isfinite(number):
        raise ValueError("Nonfinite numerical table value")
    return number


def _json(path: Path) -> Any:
    def object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate numerical JSON key: {key}")
            result[key] = value
        return result

    value = json.loads(path.read_bytes(), object_pairs_hook=object_pairs)
    json.dumps(value, allow_nan=False)
    return value


def _regional(root: Path, payload: dict[str, Any], coordinates: list[float]) -> None:
    taxa = payload["taxa"]
    header, rows = _table(root / "reconstruction.csv")
    expected = ["Distance.weighting", "Basin.type", "coordinate"] + [
        f"{taxon}.{stat}"
        for stat in ("mean", "median", "q90", "q10", "sd")
        for taxon in taxa
    ]
    if header != expected or [_number(row[2]) for row in rows] != coordinates:
        raise ValueError(
            "Regional table taxa/statistics/coordinates differ from request"
        )
    for row in rows:
        if row[1] != payload["regional"]["basin"]["site_type"]:
            raise ValueError("Regional table basin differs from request")
        for column, value in zip(header[3:], row[3:], strict=True):
            # One draw has an undefined sample SD in the source method.
            _number(value, nullable=column.endswith(".sd"))
    header, rows = _table(root / "deposition_factors.csv")
    if header != ["index", "K"] or [row[0] for row in rows] != taxa:
        raise ValueError("Deposition table differs from retained taxa")
    if any(float(row[1]) <= 0 or _number(row[1]) is None for row in rows):
        raise ValueError("Invalid deposition factor")


def _local(root: Path, payload: dict[str, Any]) -> None:
    header, rows = _table(root / "cover_mean.csv")
    if header != ["index", *payload["taxa"]]:
        raise ValueError("Local cover table differs from retained taxa")
    coordinates = [_number(row[0]) for row in rows]
    expected = [
        ring["mean_m"]
        for ring in payload["rings"][: payload["configuration"]["love"]["max_ring"]]
    ]
    if coordinates != expected:
        raise ValueError("Local cover table differs from declared ring support")
    for path in sorted(root.glob("*.csv")):
        header, rows = _table(path)
        if path.name.startswith(("cover_", "pollen_percentages_")):
            if (
                header != ["index", *payload["taxa"]]
                or [_number(row[0]) for row in rows] != expected
            ):
                raise ValueError("Local statistic axes differ from request")
            for row in rows:
                for value in row[1:]:
                    # Analytical source behavior can leave unsupported estimates
                    # missing. Preserve empty fields; never coerce them to zero.
                    _number(value, nullable=True)


def validate_numerical_tables(directory: Path, payload: dict[str, Any]) -> None:
    """Check primary table axes/types while preserving source-declared missingness.

    This verifies saved CSV shape, not ecological accuracy or a recomputation of
    estimates. Binary Monte Carlo arrays retain byte-inventory verification.
    """
    numerical = directory / "numerical"
    operation = payload["operation"]
    coordinates = [sample["coordinate"] for sample in payload["regional"]["samples"]]
    if operation == "reveals":
        stages = [(numerical, "reveals", coordinates)]
    elif operation == "love":
        stages = [(numerical, "love", coordinates)]
    elif operation == "lra":
        stages = [
            (numerical / "regional_reveals", "reveals", coordinates),
            (numerical / "local_love", "love", coordinates),
        ]
    elif operation == "series":
        index = _json(numerical / "series_index.json")
        coordinates = [sample["coordinate"] for sample in payload["local"]["samples"]]
        if (
            not isinstance(index, list)
            or [_number(str(row["coordinate"])) for row in index] != coordinates
        ):
            raise ValueError("Series index differs from requested coordinates")
        stages = []
        seen: set[str] = set()
        for row in index:
            relative = Path(row["path"])
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or relative.as_posix() in seen
            ):
                raise ValueError("Invalid or duplicate series stage path")
            seen.add(relative.as_posix())
            coordinate = float(row["coordinate"])
            stages.extend(
                [
                    (
                        numerical / relative / "regional_reveals",
                        "reveals",
                        [coordinate],
                    ),
                    (numerical / relative / "local_love", "love", [coordinate]),
                ]
            )
    else:
        raise ValueError("Unsupported saved numerical operation")
    for root, kind, stage_coordinates in stages:
        contract = _json(root / "result_contract.json")
        primary = "reconstruction.csv" if kind == "reveals" else "cover_mean.csv"
        units = {
            "cover": "percent" if kind == "reveals" else "fraction",
            "distance": "metre",
        }
        if kind == "love":
            units["pollen_percentages"] = "percent"
        if (
            not isinstance(contract, dict)
            or contract.get("schema_version") != "1.0.0"
            or contract.get("result_type") != kind
            or contract.get("primary_artifact") != primary
            or contract.get("units") != units
        ):
            raise ValueError("Unsupported saved numerical result contract")
        if kind == "reveals":
            _regional(root, payload, stage_coordinates)
        else:
            if contract.get("method") != payload["configuration"]["love"].get(
                "method", "analytical"
            ):
                raise ValueError("Saved LOVE method differs from request")
            _local(root, payload)
