"""Compact synthetic declarations; no native HYDE values are represented."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, cast

from bijux_pollenomics.collection.sources.hyde.netcdf.contracts import (
    SCENARIOS,
    VARIABLES,
)

LICENSE = (
    "The Creative Commons License (CC BY 3.0) applies to all of the HYDE data. "
    "(see https://creativecommons.org/licenses/by/3.0/)"
)


def _axis(
    name: str, values: list[float], *, unlimited: bool = False
) -> tuple[dict[str, object], dict[str, object]]:
    attributes: dict[str, object] = {
        "standard_name": {"time": "time", "lat": "latitude", "lon": "longitude"}[name],
        "units": {
            "time": "days since 1-5-1 00:00:00",
            "lat": "degrees_north",
            "lon": "degrees_east",
        }[name],
    }
    if name == "time":
        attributes["calendar"] = "365_day"
    else:
        attributes["long_name"] = f"{name} centers"
    variable = {
        "dtype": "float32",
        "dimensions": [name],
        "shape": [len(values)],
        "attributes": attributes,
        "coordinate_values": values,
    }
    return variable, {"size": len(values), "unlimited": unlimited}


def header(path: str, size: int, mtime_ns: int, variable: str) -> dict[str, object]:
    time, time_dimension = _axis("time", [-365.0, 0.0, 365.0], unlimited=True)
    lat, lat_dimension = _axis("lat", [0.5, -0.5])
    lon, lon_dimension = _axis("lon", [-1.0, 0.0, 1.0])
    return {
        "path": path,
        "bytes": size,
        "mtime_ns": mtime_ns,
        "format": "NETCDF4",
        "attributes": {
            "version": "HYDE3.4",
            "description": "HYDE3.4 test netCDF",
            "license": LICENSE,
            "source": "provider raw source declaration",
        },
        "dimensions": {
            "time": time_dimension,
            "lat": lat_dimension,
            "lon": lon_dimension,
        },
        "variables": {
            "time": time,
            "lat": lat,
            "lon": lon,
            variable: {
                "dtype": "float32",
                "dimensions": ["time", "lat", "lon"],
                "shape": [3, 2, 3],
                "attributes": {
                    "_FillValue": -9999.0,
                    "standard_name": variable,
                    "long_name": variable.replace("_", " "),
                    "units": (
                        "capita_per_km**2"
                        if variable == "population_density"
                        else "capita"
                        if "population" in variable
                        else "km**2"
                    ),
                },
            },
        },
    }


def write_inputs(tmp_path: Path) -> dict[str, object]:
    file_rows: list[dict[str, object]] = []
    headers: list[dict[str, object]] = []
    for scenario in SCENARIOS:
        for index, variable in enumerate(VARIABLES):
            path = f"original/gbc2025_7apr_{scenario}/NetCDF/{variable}.nc"
            size = 1000 + index
            mtime_ns = 1700000000000000000 + index
            source_sha = hashlib.sha256(path.encode()).hexdigest()
            file_rows.append(
                {
                    "path": path,
                    "bytes": size,
                    "mtime_ns": mtime_ns,
                    "sha256": source_sha,
                    "ctime_ns": mtime_ns,
                    "inode": len(file_rows) + 1,
                }
            )
            headers.append(header(path, size, mtime_ns, variable))
    file_rows.append(
        {
            "path": "License.txt",
            "bytes": 10,
            "mtime_ns": 1700000000000000000,
            "sha256": "a" * 64,
            "ctime_ns": 1700000000000000000,
            "inode": 100,
        }
    )
    files_content = b"".join(
        (json.dumps(row, separators=(",", ":")) + "\n").encode() for row in file_rows
    )
    header_content = json.dumps(headers, separators=(",", ":")).encode()
    files_sha = hashlib.sha256(files_content).hexdigest()
    headers_sha = hashlib.sha256(header_content).hexdigest()
    report = {
        "status": "hashed_and_inventoried_not_admitted",
        "file_count": len(file_rows),
        "byte_count": sum(cast(int, row["bytes"]) for row in file_rows),
        "archive_member_count": 7,
        "source_stat_inventory_unchanged": True,
        "files_sha256": files_sha,
        "elapsed_seconds": 1.0,
    }
    conflict = {
        "schema_version": "hyde-native-metadata-review.v1",
        "inputs": [
            {
                "role": "netcdf_headers",
                "bytes": len(header_content),
                "sha256": headers_sha,
            }
        ],
        "custody": {
            "manifest_sha256": "b" * 64,
            "dataset_inventory_sha256": "c" * 64,
            "counts": {
                "ancillary_file_count": 1,
                "archive_file_count": 0,
                "archive_member_count": 7,
                "byte_count": report["byte_count"],
                "dataset_byte_count": report["byte_count"],
                "dataset_file_count": len(file_rows),
                "file_count": len(file_rows),
                "netcdf_named_file_count": 48,
            },
        },
        "claims": [
            {
                "topic": topic,
                "source": "netcdf_headers",
                "value": value,
                "context": "48_of_48",
            }
            for topic, value in {
                "calendar": "365_day",
                "calendar_units": "days since 1-5-1 00:00:00",
                "license": LICENSE,
                "release": "HYDE3.4",
                "release_description": "HYDE3.4 test netCDF",
            }.items()
        ],
        "scenario_semantics": {
            "labels": list(SCENARIOS),
            "netcdf_header_counts": dict.fromkeys(SCENARIOS, 16),
            "role": "provider_estimate_scenarios",
            "confidence_bounds_status": "not_declared",
            "pointwise_ordering_contract": "none",
        },
        "conflicts": [
            "calendar_mapping_unresolved",
            "coverage_end_year_conflict",
            "license_declaration_conflict",
            "release_identity_conflict",
            "scenario_uncertainty_semantics_unresolved",
            "zero_ad_calendar_interpretation_unresolved",
        ],
        "admission": {
            "native_release_status": "refused_pending_review",
            "scientific_acceptance": "not_evaluated",
            "public_release_allowed": False,
            "country_projection_allowed": False,
            "canonical_calendar_conversion_allowed": False,
            "required_reviews": [
                "qualified_release_identity",
                "qualified_release_specific_rights",
                "native_calendar_and_0ad_interpretation",
                "coverage_end_year",
                "scenario_uncertainty_semantics",
            ],
        },
    }
    contents = {
        "file_inventory": files_content,
        "inventory_report": json.dumps(report).encode(),
        "header_inventory": header_content,
        "conflict_report": json.dumps(conflict).encode(),
    }
    result: dict[str, object] = {}
    for role, content in contents.items():
        path = tmp_path / f"{role}.json"
        path.write_bytes(content)
        result[f"{role}_path"] = path
        result[f"expected_{role}_sha256"] = hashlib.sha256(content).hexdigest()
    return result


def rewrite_json(inputs: dict[str, object], role: str, mutate: Any) -> None:
    path = inputs[f"{role}_path"]
    assert isinstance(path, Path)
    value = json.loads(path.read_text())
    mutate(value)
    path.write_text(json.dumps(value))
    inputs[f"expected_{role}_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()


def rewrite_headers(inputs: dict[str, object], mutate: Any) -> None:
    """Rehash a changed header input through its retained conflict identity."""
    rewrite_json(inputs, "header_inventory", mutate)
    header_sha = inputs["expected_header_inventory_sha256"]

    def bind(value: dict[str, Any]) -> None:
        value["inputs"][0]["sha256"] = header_sha

    rewrite_json(inputs, "conflict_report", bind)
