"""Publish a private, refusal-bounded HYDE three-scenario source window."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import tempfile
from typing import Literal, cast

from bijux_pollenomics.collection.sources.hyde.ascii import (
    NativeAsciiWindow,
    read_hyde_ascii_window,
)
from bijux_pollenomics.collection.sources.hyde.ascii.geometry import (
    native_axis_geometry,
)
from bijux_pollenomics.collection.sources.hyde.local.contracts import (
    checked_path,
    decode,
    digest,
    encode,
    sha256,
)
from bijux_pollenomics.collection.sources.hyde.netcdf import (
    HydeNetcdfDeclarationInventory,
    read_hyde_netcdf_declaration_inventory,
)
from bijux_pollenomics.collection.sources.quarantine import IntakeRefusal
from bijux_pollenomics.core.owned_tree import publish_new_output_tree

Scenario = Literal["base", "lower", "upper"]

SCHEMA_VERSION = "hyde-nordic-intent-native-window-bundle.v1"
STATUS = "private_source_index_only"
SCENARIOS: tuple[Scenario, ...] = ("base", "lower", "upper")
COUNTRY_CODES = ("SE", "DK", "NO", "FI")
WINDOW_ROWS = (216, 432)
WINDOW_COLUMNS = (2208, 2544)
SELECTED_INDEX_POSITIONS = 72_576
SCENARIO_TOKEN_INSTANCES = 217_728
CUSTODY_MANIFEST_SHA256 = (
    "cd66806f890fbb4c556dfc55ae91b93088a98013112a671cd77814bf9f2b50dd"
)
DATASET_INVENTORY_SHA256 = (
    "bcc6ee45d4af4c1e4516a1ec4fe7b1f0048d21935ce77738f997244484ccff82"
)

_FILE_INVENTORY_SHA256 = (
    "727893bef686146611dcb702e7fab5c497f70c8630b8d2a3fc158b3b5b7d53ef"
)
_INVENTORY_REPORT_SHA256 = (
    "3b951d91b064fa6885ec5e3ffaac82217bb7d9058f11e21d9b58216f4d3d1ac9"
)
_HEADER_INVENTORY_SHA256 = (
    "b1809b9a5f935332c336aa695b9c2614a5c8db4a15ee1b86106fa6a13a622d1f"
)
_CONFLICT_REPORT_SHA256 = (
    "1de8918edcb9e27507effc6ab360a7c23a4e06c9bbb369552ea3e4d88589fcbb"
)
_DECLARATION_HASHES = {
    "file_inventory": _FILE_INVENTORY_SHA256,
    "inventory_report": _INVENTORY_REPORT_SHA256,
    "header_inventory": _HEADER_INVENTORY_SHA256,
    "conflict_report": _CONFLICT_REPORT_SHA256,
}
_CONFLICTS = (
    "calendar_mapping_unresolved",
    "coverage_end_year_conflict",
    "license_declaration_conflict",
    "release_identity_conflict",
    "scenario_uncertainty_semantics_unresolved",
    "zero_ad_calendar_interpretation_unresolved",
)
_HEADER_TOKENS = (
    ("ncols", "4320"),
    ("nrows", "2160"),
    ("xllcorner", "-180"),
    ("yllcorner", "-90"),
    ("cellsize", "0.0833333"),
    ("NODATA_value", "-9999"),
)
_SCENARIO_COUNTS = {
    "base": (29_217, 43_359, 15_307),
    "lower": (29_217, 43_359, 15_158),
    "upper": (29_217, 43_359, 15_332),
}
_SOURCE_AXIS_EDGES = {
    "global_west": "-180",
    "global_south": "-90",
    "global_east": "179.9998560",
    "global_north": "89.9999280",
    "window_west": "3.9999264",
    "window_east": "31.9999152",
    "window_south": "53.9999424",
    "window_north": "71.9999352",
    "step": "0.0833333",
    "row_order": "north_to_south",
}
_REASON_CODES = (
    "hyde_native_country_projection_unverified",
    "candidate_source_axis_window_is_not_country_partition",
)
_NETCDF_LICENSE_DECLARATION = "".join(
    (
        "The Creative Commons License (CC BY 3.0) applies to all of the HYDE ",
        "data. (see https://creativecommons.org/licenses/by/3.0/)",
    )
)
_NETCDF_RAW_DECLARATIONS: dict[str, object] = {
    "time_axis_units": ["days since 1-5-1 00:00:00"],
    "time_axis_calendars": ["365_day"],
    "global_attributes": {
        "license": [_NETCDF_LICENSE_DECLARATION],
        "version": ["HYDE3.4"],
        "description": ["HYDE3.4 test netCDF"],
    },
    "interpretation": "retained_source_declarations_not_ascii_admission",
}


@dataclass(frozen=True)
class _ScenarioSource:
    archive_path: str
    archive_sha256: str
    archive_bytes: int
    member_sha256: str
    member_bytes: int
    member_crc32: int


SCENARIO_SOURCES: dict[Scenario, _ScenarioSource] = {
    "base": _ScenarioSource(
        "original/gbc2025_7apr_base/zip/2000AD_lu.zip",
        "d0a762ccce3256d25c36e1c58894c6a6b05f93075006366854cc7e6176c7d09f",
        56_720_903,
        "31a74f63973886edbd2303737df2684c799caaea83af27561755e1d5da67b0c7",
        66_122_101,
        0xD7AA6327,
    ),
    "lower": _ScenarioSource(
        "original/gbc2025_7apr_lower/zip/2000AD_lu.zip",
        "e763c82b62e7fd6c19d68113bcff23bfebaf5e71732f39824762a951e738480b",
        56_802_955,
        "af2ec9495411a2651a17d7e992213c28ca13e6afde8662eed12ffc267edecf70",
        66_167_280,
        0x3ED75C45,
    ),
    "upper": _ScenarioSource(
        "original/gbc2025_7apr_upper/zip/2000AD_lu.zip",
        "8a3a518655e16e7a49c72c6463ef4a377588c271d0a381f32c60dd8a801f7ea9",
        56_720_413,
        "9e8dbff9b25e24227f4f8fcdf1abb41911f62873e1a23e61b37327105b57aabe",
        66_119_264,
        0xCACA6A12,
    ),
}


@dataclass(frozen=True)
class HydeNativeWindowInput:
    """One authenticated retained native window and its intended raw scenario."""

    scenario: Scenario
    directory: Path
    expected_manifest_sha256: str

    def __post_init__(self) -> None:
        if self.scenario not in SCENARIOS:
            raise IntakeRefusal("hyde_nordic_scenario_invalid", repr(self.scenario))
        digest(self.expected_manifest_sha256)


@dataclass(frozen=True)
class HydeDeclarationParentInput:
    """Four compact, independently pinned declaration parents."""

    file_inventory_path: Path
    expected_file_inventory_sha256: str
    inventory_report_path: Path
    expected_inventory_report_sha256: str
    header_inventory_path: Path
    expected_header_inventory_sha256: str
    conflict_report_path: Path
    expected_conflict_report_sha256: str

    def __post_init__(self) -> None:
        values = {
            "file_inventory": self.expected_file_inventory_sha256,
            "inventory_report": self.expected_inventory_report_sha256,
            "header_inventory": self.expected_header_inventory_sha256,
            "conflict_report": self.expected_conflict_report_sha256,
        }
        for value in values.values():
            digest(value)
        if values != _DECLARATION_HASHES:
            raise IntakeRefusal(
                "hyde_nordic_declaration_parent_identity_invalid",
                "The four governed declaration identities are required",
            )


@dataclass(frozen=True)
class HydeNordicWindowBundle:
    """Authenticated private source-index evidence with no country admission."""

    directory: Path
    manifest_sha256: str
    child_manifest_sha256: tuple[tuple[Scenario, str], ...]
    declaration_inventory_sha256: str
    selected_index_positions: int
    scenario_token_instances: int


@dataclass(frozen=True)
class _CapturedWindow:
    request: HydeNativeWindowInput
    product: NativeAsciiWindow
    manifest_bytes: bytes
    window_bytes: bytes
    custody_manifest_sha256: str
    dataset_inventory_sha256: str
    archive_sha256: str
    archive_bytes: int
    member_bytes: int
    member_crc32: int


_read_ascii_window = read_hyde_ascii_window
_read_declarations = read_hyde_netcdf_declaration_inventory
_native_axis_geometry = native_axis_geometry
_publish_new_output_tree = publish_new_output_tree


def _producer_identity() -> dict[str, str]:
    source = Path(__file__).resolve()
    return {
        "source_completion/hyde_nordic_window.py": sha256(source.read_bytes()),
    }


def _child_bytes(root: Path) -> tuple[bytes, bytes]:
    root = checked_path(root)
    if not root.is_dir() or {path.name for path in root.iterdir()} != {
        "manifest.json",
        "window.json",
    }:
        raise IntakeRefusal("hyde_nordic_child_inventory_invalid", str(root))
    contents: list[bytes] = []
    for name, limit in (("manifest.json", 65_536), ("window.json", 16 * 1024 * 1024)):
        path = checked_path(root / name)
        if not path.is_file():
            raise IntakeRefusal("hyde_nordic_child_inventory_invalid", str(path))
        content = path.read_bytes()
        if len(content) > limit:
            raise IntakeRefusal("hyde_nordic_child_limit", name)
        contents.append(content)
    return contents[0], contents[1]


def _child_source_identity(
    manifest_bytes: bytes,
) -> tuple[str, str, str, int, int, int]:
    value = decode(manifest_bytes)
    if not isinstance(value, dict):
        raise IntakeRefusal("hyde_nordic_child_manifest_invalid", "object required")
    archive = value.get("archive_member")
    payload = value.get("member_payload")
    if not isinstance(archive, dict) or not isinstance(payload, dict):
        raise IntakeRefusal("hyde_nordic_child_manifest_invalid", "source identity")
    try:
        custody_manifest_sha256 = digest(value["custody_manifest_sha256"])
        dataset_inventory_sha256 = digest(value["dataset_inventory_sha256"])
        archive_sha256 = digest(archive["archive_sha256"])
        archive_bytes = archive["archive_bytes"]
        member_bytes = payload["bytes"]
        member_crc32 = payload["crc32"]
    except KeyError as exc:
        raise IntakeRefusal(
            "hyde_nordic_child_manifest_invalid", "source identity"
        ) from exc
    if any(
        type(number) is not int or number < 0
        for number in (archive_bytes, member_bytes, member_crc32)
    ):
        raise IntakeRefusal("hyde_nordic_child_manifest_invalid", "source numbers")
    return (
        custody_manifest_sha256,
        dataset_inventory_sha256,
        archive_sha256,
        archive_bytes,
        member_bytes,
        member_crc32,
    )


def _capture_window_bytes(request: HydeNativeWindowInput) -> _CapturedWindow:
    root = checked_path(request.directory)
    product = _read_ascii_window(
        root, expected_manifest_sha256=request.expected_manifest_sha256
    )
    manifest_bytes, window_bytes = _child_bytes(root)
    if sha256(manifest_bytes) != request.expected_manifest_sha256:
        raise IntakeRefusal(
            "hyde_nordic_child_manifest_digest_mismatch", request.scenario
        )
    (
        custody_manifest_sha,
        dataset_inventory_sha,
        archive_sha,
        archive_bytes,
        member_bytes,
        member_crc32,
    ) = _child_source_identity(manifest_bytes)
    return _CapturedWindow(
        request,
        product,
        manifest_bytes,
        window_bytes,
        custody_manifest_sha,
        dataset_inventory_sha,
        archive_sha,
        archive_bytes,
        member_bytes,
        member_crc32,
    )


def _source_bytes_unchanged(captured: _CapturedWindow) -> None:
    manifest_bytes, window_bytes = _child_bytes(captured.request.directory)
    if (
        manifest_bytes != captured.manifest_bytes
        or window_bytes != captured.window_bytes
    ):
        raise IntakeRefusal("hyde_nordic_input_changed", captured.request.scenario)


def _validate_window(captured: _CapturedWindow) -> dict[str, object]:
    scenario = captured.request.scenario
    expected = SCENARIO_SOURCES[scenario]
    window = captured.product
    selection = window.selection
    labels = (("scenario", scenario), ("time", "2000AD"), ("variable", "cropland"))
    if (
        window.manifest_sha256 != captured.request.expected_manifest_sha256
        or window.custody_manifest_sha256 != CUSTODY_MANIFEST_SHA256
        or window.member_sha256 != expected.member_sha256
        or selection.archive_path != expected.archive_path
        or selection.member_index != 0
        or selection.expected_member_name != "cropland2000AD.asc"
        or (selection.row_start, selection.row_stop) != WINDOW_ROWS
        or (selection.column_start, selection.column_stop) != WINDOW_COLUMNS
        or selection.native_labels != labels
        or window.header.rows != 2160
        or window.header.columns != 4320
        or window.header.tokens != _HEADER_TOKENS
        or len(window.source_tokens) != SELECTED_INDEX_POSITIONS
        or len(window.missing_mask) != SELECTED_INDEX_POSITIONS
        or captured.custody_manifest_sha256 != CUSTODY_MANIFEST_SHA256
        or captured.dataset_inventory_sha256 != DATASET_INVENTORY_SHA256
        or captured.archive_sha256 != expected.archive_sha256
        or captured.archive_bytes != expected.archive_bytes
        or captured.member_bytes != expected.member_bytes
        or captured.member_crc32 != expected.member_crc32
    ):
        raise IntakeRefusal("hyde_nordic_window_profile_invalid", scenario)
    geometry = _native_axis_geometry(window, archive_sha256=expected.archive_sha256)
    required_geometry = {
        "source_header_tokens": dict(_HEADER_TOKENS),
        "selected_source_indices": {
            "row_start": WINDOW_ROWS[0],
            "row_stop": WINDOW_ROWS[1],
            "column_start": WINDOW_COLUMNS[0],
            "column_stop": WINDOW_COLUMNS[1],
        },
        "selected_cells": SELECTED_INDEX_POSITIONS,
        "coordinate_reference_system": None,
        "variable_units": None,
        "calendar_support": None,
        "country_projection": "not_performed",
        "scientific_acceptance": "not_evaluated",
        "public_release_allowed": False,
    }
    if any(geometry.get(key) != value for key, value in required_geometry.items()):
        raise IntakeRefusal("hyde_nordic_geometry_posture_invalid", scenario)
    if geometry.get("source_axis_edges") != _SOURCE_AXIS_EDGES:
        raise IntakeRefusal("hyde_nordic_geometry_profile_invalid", scenario)
    if (
        geometry.get("selected_missing"),
        geometry.get("selected_nonmissing"),
        geometry.get("selected_zero"),
    ) != _SCENARIO_COUNTS[scenario]:
        raise IntakeRefusal("hyde_nordic_scenario_denominator_invalid", scenario)
    return {
        "scenario": scenario,
        "child_directory": f"scenarios/{scenario}",
        "child_manifest_sha256": captured.request.expected_manifest_sha256,
        "custody_manifest_sha256": CUSTODY_MANIFEST_SHA256,
        "dataset_inventory_sha256": DATASET_INVENTORY_SHA256,
        "archive": {
            "path": expected.archive_path,
            "sha256": expected.archive_sha256,
            "bytes": expected.archive_bytes,
        },
        "member": {
            "index": 0,
            "name": "cropland2000AD.asc",
            "sha256": expected.member_sha256,
            "bytes": expected.member_bytes,
            "crc32": expected.member_crc32,
        },
        "native_labels": [list(pair) for pair in labels],
        "source_header_tokens": [list(pair) for pair in _HEADER_TOKENS],
        "selected_source_indices": required_geometry["selected_source_indices"],
        "source_axis_edges": {
            "authority": "undeclared_native_axis_values",
            **_SOURCE_AXIS_EDGES,
        },
        "counts": {
            "selected_cells": geometry["selected_cells"],
            "selected_missing": geometry["selected_missing"],
            "selected_nonmissing": geometry["selected_nonmissing"],
            "selected_zero": geometry["selected_zero"],
        },
    }


def _read_declaration_parents(
    parents: HydeDeclarationParentInput,
) -> HydeNetcdfDeclarationInventory:
    return _read_declarations(
        file_inventory_path=parents.file_inventory_path,
        inventory_report_path=parents.inventory_report_path,
        header_inventory_path=parents.header_inventory_path,
        conflict_report_path=parents.conflict_report_path,
    )


def _declaration_parents_unchanged(parents: HydeDeclarationParentInput) -> None:
    sources = (
        (
            parents.file_inventory_path,
            parents.expected_file_inventory_sha256,
            1024 * 1024,
        ),
        (
            parents.inventory_report_path,
            parents.expected_inventory_report_sha256,
            64 * 1024,
        ),
        (
            parents.header_inventory_path,
            parents.expected_header_inventory_sha256,
            12 * 1024 * 1024,
        ),
        (
            parents.conflict_report_path,
            parents.expected_conflict_report_sha256,
            64 * 1024,
        ),
    )
    for path, expected_sha256, limit in sources:
        source = checked_path(path)
        if not source.is_file():
            raise IntakeRefusal("hyde_nordic_input_changed", str(source))
        with source.open("rb") as stream:
            content = stream.read(limit + 1)
        if len(content) > limit or sha256(content) != expected_sha256:
            raise IntakeRefusal("hyde_nordic_input_changed", str(source))


def _declaration_summary(
    inventory: HydeNetcdfDeclarationInventory,
) -> dict[str, object]:
    if (
        dict(inventory.input_sha256) != _DECLARATION_HASHES
        or inventory.custody_manifest_sha256 != CUSTODY_MANIFEST_SHA256
        or inventory.dataset_inventory_sha256 != DATASET_INVENTORY_SHA256
        or inventory.scenario_counts != (("base", 16), ("lower", 16), ("upper", 16))
        or inventory.conflicts != _CONFLICTS
        or inventory.scenario_role != "provider_estimate_scenarios"
        or inventory.pointwise_ordering_contract != "none"
        or inventory.scenario_confidence_bounds is not False
        or inventory.native_release_admitted is not False
        or inventory.rights_cleared is not False
        or inventory.crs_assigned is not False
        or inventory.canonical_bp_conversion_allowed is not False
        or inventory.publication_allowed is not False
        or inventory.independent_measured_vegetation_truth is not False
        or inventory.scientific_acceptance != "not_evaluated"
    ):
        raise IntakeRefusal(
            "hyde_nordic_declaration_posture_invalid", "governed inventory"
        )
    cropland_units = sorted(
        {row.units for row in inventory.files if row.variable == "cropland"}
    )
    time_axes = [axis for axis in inventory.axes if axis.name == "time"]
    global_attributes = {
        key: sorted(
            {
                dict(row.global_attributes)[key]
                for row in inventory.files
                if key in dict(row.global_attributes)
            }
        )
        for key in ("license", "version", "description")
    }
    raw_declarations = {
        "time_axis_units": sorted({axis.units for axis in time_axes}),
        "time_axis_calendars": sorted(
            {axis.calendar for axis in time_axes if axis.calendar is not None}
        ),
        "global_attributes": global_attributes,
        "interpretation": "retained_source_declarations_not_ascii_admission",
    }
    if (
        cropland_units != ["km**2"]
        or len(time_axes) != 1
        or raw_declarations != _NETCDF_RAW_DECLARATIONS
    ):
        raise IntakeRefusal(
            "hyde_nordic_declaration_posture_invalid",
            "typed NetCDF raw declarations",
        )
    return {
        "schema_version": inventory.schema_version,
        "canonical_sha256": inventory.sha256,
        "input_sha256": dict(inventory.input_sha256),
        "custody_manifest_sha256": inventory.custody_manifest_sha256,
        "dataset_inventory_sha256": inventory.dataset_inventory_sha256,
        "scenario_counts": dict(inventory.scenario_counts),
        "scenario_role": inventory.scenario_role,
        "conflicts": list(inventory.conflicts),
        "netcdf_raw_declarations": raw_declarations,
        "netcdf_cropland_unit_candidates": cropland_units,
        "netcdf_unit_transfer_to_ascii": "not_performed",
    }


def _effective_semantics() -> dict[str, object]:
    return {
        "coordinate_reference_system": None,
        "variable_units": None,
        "calendar_support": None,
        "cell_area": None,
        "country_assignment_method": None,
        "scenario_confidence_bounds": False,
        "pointwise_ordering_contract": "none",
        "rights_cleared": False,
        "scientific_acceptance": "not_evaluated",
        "independent_measured_vegetation_truth": False,
        "public_release_allowed": False,
    }


def _country_intent() -> dict[str, object]:
    return {
        "requested_country_codes": list(COUNTRY_CODES),
        "partition_status": "not_materialized",
        "rows": [
            {
                "country_code": country,
                "assignment_status": "refused",
                "selected_cells": None,
                "nonmissing_cells": None,
                "cell_area": None,
                "value_total": None,
                "reason_codes": list(_REASON_CODES),
            }
            for country in COUNTRY_CODES
        ],
    }


def _file_inventory(captured: tuple[_CapturedWindow, ...]) -> dict[str, object]:
    result: dict[str, object] = {}
    for item in captured:
        prefix = f"scenarios/{item.request.scenario}"
        result[f"{prefix}/manifest.json"] = {
            "bytes": len(item.manifest_bytes),
            "sha256": sha256(item.manifest_bytes),
        }
        result[f"{prefix}/window.json"] = {
            "bytes": len(item.window_bytes),
            "sha256": sha256(item.window_bytes),
        }
    return result


def _manifest(
    captured: tuple[_CapturedWindow, ...],
    declarations: HydeNetcdfDeclarationInventory,
    producer: dict[str, str],
) -> dict[str, object]:
    scenarios = [_validate_window(item) for item in captured]
    return {
        "schema_version": SCHEMA_VERSION,
        "status": STATUS,
        "producer": {
            "files": producer,
            "files_sha256": sha256(encode(producer)),
        },
        "files": _file_inventory(captured),
        "declarations": _declaration_summary(declarations),
        "scenarios": scenarios,
        "counts": {
            "scenario_count": 3,
            "unique_selected_index_positions": SELECTED_INDEX_POSITIONS,
            "scenario_token_instances": SCENARIO_TOKEN_INSTANCES,
        },
        "effective_semantics": _effective_semantics(),
        "country_intent": _country_intent(),
    }


def _raw_bundle(root: Path, expected_manifest_sha256: str) -> dict[str, bytes]:
    root = checked_path(root)
    if not root.is_dir() or {path.name for path in root.iterdir()} != {
        "manifest.json",
        "scenarios",
    }:
        raise IntakeRefusal("hyde_nordic_bundle_inventory_invalid", str(root))
    manifest_path = checked_path(root / "manifest.json")
    if not manifest_path.is_file():
        raise IntakeRefusal("hyde_nordic_bundle_inventory_invalid", "manifest.json")
    manifest_bytes = manifest_path.read_bytes()
    if len(manifest_bytes) > 1024 * 1024:
        raise IntakeRefusal("hyde_nordic_bundle_limit", "manifest.json")
    if sha256(manifest_bytes) != digest(expected_manifest_sha256):
        raise IntakeRefusal("hyde_nordic_manifest_digest_mismatch", str(root))
    scenarios_root = checked_path(root / "scenarios")
    if not scenarios_root.is_dir() or {
        path.name for path in scenarios_root.iterdir()
    } != set(SCENARIOS):
        raise IntakeRefusal("hyde_nordic_bundle_inventory_invalid", "scenarios")
    result = {"manifest.json": manifest_bytes}
    for scenario in SCENARIOS:
        manifest, window = _child_bytes(scenarios_root / scenario)
        result[f"scenarios/{scenario}/manifest.json"] = manifest
        result[f"scenarios/{scenario}/window.json"] = window
    return result


def _manifest_object(content: bytes) -> dict[str, object]:
    value = decode(content)
    if not isinstance(value, dict):
        raise IntakeRefusal("hyde_nordic_manifest_invalid", "object required")
    required = {
        "schema_version",
        "status",
        "producer",
        "files",
        "declarations",
        "scenarios",
        "counts",
        "effective_semantics",
        "country_intent",
    }
    if set(value) != required:
        raise IntakeRefusal("hyde_nordic_manifest_invalid", "top-level fields")
    return cast(dict[str, object], value)


def _read_bundle(root: Path, expected_manifest_sha256: str) -> HydeNordicWindowBundle:
    raw = _raw_bundle(root, expected_manifest_sha256)
    manifest = _manifest_object(raw["manifest.json"])
    if manifest["schema_version"] != SCHEMA_VERSION or manifest["status"] != STATUS:
        raise IntakeRefusal("hyde_nordic_manifest_posture_invalid", str(root))
    producer = manifest["producer"]
    if not isinstance(producer, dict) or set(producer) != {"files", "files_sha256"}:
        raise IntakeRefusal("hyde_nordic_producer_invalid", str(root))
    files = producer["files"]
    if (
        not isinstance(files, dict)
        or set(files) != {"source_completion/hyde_nordic_window.py"}
        or any(not isinstance(value, str) for value in files.values())
        or any(digest(value) != value for value in files.values())
        or producer["files_sha256"] != sha256(encode(files))
    ):
        raise IntakeRefusal("hyde_nordic_producer_invalid", str(root))
    inventory = manifest["files"]
    if not isinstance(inventory, dict) or set(inventory) != set(raw) - {
        "manifest.json"
    }:
        raise IntakeRefusal("hyde_nordic_file_inventory_invalid", str(root))
    for name, content in raw.items():
        if name == "manifest.json":
            continue
        identity = inventory[name]
        if not isinstance(identity, dict) or identity != {
            "bytes": len(content),
            "sha256": sha256(content),
        }:
            raise IntakeRefusal("hyde_nordic_file_inventory_invalid", name)
    windows: list[_CapturedWindow] = []
    scenario_rows = manifest["scenarios"]
    if not isinstance(scenario_rows, list) or len(scenario_rows) != 3:
        raise IntakeRefusal("hyde_nordic_scenario_inventory_invalid", str(root))
    for scenario, row in zip(SCENARIOS, scenario_rows, strict=True):
        if not isinstance(row, dict):
            raise IntakeRefusal("hyde_nordic_scenario_inventory_invalid", scenario)
        expected_child = cast(str, row.get("child_manifest_sha256"))
        child = root / "scenarios" / scenario
        product = _read_ascii_window(
            child, expected_manifest_sha256=digest(expected_child)
        )
        manifest_bytes = raw[f"scenarios/{scenario}/manifest.json"]
        window_bytes = raw[f"scenarios/{scenario}/window.json"]
        (
            custody_manifest_sha,
            dataset_inventory_sha,
            archive_sha,
            archive_bytes,
            member_bytes,
            member_crc32,
        ) = _child_source_identity(manifest_bytes)
        captured = _CapturedWindow(
            HydeNativeWindowInput(scenario, child, expected_child),
            product,
            manifest_bytes,
            window_bytes,
            custody_manifest_sha,
            dataset_inventory_sha,
            archive_sha,
            archive_bytes,
            member_bytes,
            member_crc32,
        )
        expected_row = _validate_window(captured)
        if row != expected_row:
            raise IntakeRefusal("hyde_nordic_scenario_manifest_invalid", scenario)
        windows.append(captured)
    counts = manifest["counts"]
    if counts != {
        "scenario_count": 3,
        "unique_selected_index_positions": SELECTED_INDEX_POSITIONS,
        "scenario_token_instances": SCENARIO_TOKEN_INSTANCES,
    }:
        raise IntakeRefusal("hyde_nordic_denominator_invalid", str(root))
    if manifest["effective_semantics"] != _effective_semantics():
        raise IntakeRefusal("hyde_nordic_semantics_promoted", str(root))
    if manifest["country_intent"] != _country_intent():
        raise IntakeRefusal("hyde_nordic_country_claim_invalid", str(root))
    declarations = manifest["declarations"]
    if not isinstance(declarations, dict):
        raise IntakeRefusal("hyde_nordic_declaration_manifest_invalid", str(root))
    required_declarations = {
        "schema_version",
        "canonical_sha256",
        "input_sha256",
        "custody_manifest_sha256",
        "dataset_inventory_sha256",
        "scenario_counts",
        "scenario_role",
        "conflicts",
        "netcdf_raw_declarations",
        "netcdf_cropland_unit_candidates",
        "netcdf_unit_transfer_to_ascii",
    }
    if (
        set(declarations) != required_declarations
        or declarations["schema_version"] != "hyde-netcdf-declaration-inventory.v1"
        or not isinstance(declarations["canonical_sha256"], str)
        or digest(declarations["canonical_sha256"]) != declarations["canonical_sha256"]
        or declarations["input_sha256"] != _DECLARATION_HASHES
        or declarations["custody_manifest_sha256"] != CUSTODY_MANIFEST_SHA256
        or declarations["dataset_inventory_sha256"] != DATASET_INVENTORY_SHA256
        or declarations["scenario_counts"] != dict.fromkeys(SCENARIOS, 16)
        or declarations["scenario_role"] != "provider_estimate_scenarios"
        or declarations["conflicts"] != list(_CONFLICTS)
        or declarations["netcdf_raw_declarations"] != _NETCDF_RAW_DECLARATIONS
        or declarations["netcdf_cropland_unit_candidates"] != ["km**2"]
        or declarations["netcdf_unit_transfer_to_ascii"] != "not_performed"
    ):
        raise IntakeRefusal("hyde_nordic_declaration_manifest_invalid", str(root))
    if _raw_bundle(root, expected_manifest_sha256) != raw:
        raise IntakeRefusal("hyde_nordic_bundle_changed", str(root))
    return HydeNordicWindowBundle(
        root,
        expected_manifest_sha256,
        tuple(
            (item.request.scenario, item.request.expected_manifest_sha256)
            for item in windows
        ),
        declarations["canonical_sha256"],
        SELECTED_INDEX_POSITIONS,
        SCENARIO_TOKEN_INSTANCES,
    )


def read_hyde_nordic_window_bundle(
    destination: Path, *, expected_manifest_sha256: str
) -> HydeNordicWindowBundle:
    """Authenticate an exact private bundle without promoting source semantics."""
    try:
        return _read_bundle(checked_path(destination), expected_manifest_sha256)
    except (
        OSError,
        TypeError,
        KeyError,
        ValueError,
        OverflowError,
        RecursionError,
    ) as exc:
        if isinstance(exc, IntakeRefusal):
            raise
        raise IntakeRefusal("hyde_nordic_read_failed", str(exc)) from exc


def publish_hyde_nordic_window_bundle(
    *,
    windows: tuple[HydeNativeWindowInput, ...],
    declarations: HydeDeclarationParentInput,
    destination: Path,
) -> HydeNordicWindowBundle:
    """Copy authenticated children and atomically publish one refusal-only bundle."""
    if not isinstance(windows, tuple) or not isinstance(
        declarations, HydeDeclarationParentInput
    ):
        raise IntakeRefusal("hyde_nordic_request_invalid", "Typed inputs required")
    if (
        any(not isinstance(item, HydeNativeWindowInput) for item in windows)
        or tuple(item.scenario for item in windows) != SCENARIOS
    ):
        raise IntakeRefusal(
            "hyde_nordic_scenario_order_invalid", "base, lower, upper required"
        )
    target = checked_path(destination)
    if target.exists() or target.is_symlink():
        raise IntakeRefusal("hyde_nordic_destination_exists", str(target))
    source_roots = tuple(checked_path(item.directory) for item in windows)
    declaration_paths = tuple(
        checked_path(path)
        for path in (
            declarations.file_inventory_path,
            declarations.inventory_report_path,
            declarations.header_inventory_path,
            declarations.conflict_report_path,
        )
    )
    if any(
        target == source
        or target.is_relative_to(source)
        or source.is_relative_to(target)
        for source in (*source_roots, *declaration_paths)
    ):
        raise IntakeRefusal("hyde_nordic_output_overlaps_input", str(target))
    producer = _producer_identity()
    captured = tuple(_capture_window_bytes(item) for item in windows)
    declaration_inventory = _read_declaration_parents(declarations)
    manifest = _manifest(captured, declaration_inventory, producer)
    manifest_bytes = encode(manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.pending-", dir=target.parent))
    for item in captured:
        child = stage / "scenarios" / item.request.scenario
        child.mkdir(parents=True)
        (child / "manifest.json").write_bytes(item.manifest_bytes)
        (child / "window.json").write_bytes(item.window_bytes)
    (stage / "manifest.json").write_bytes(manifest_bytes)
    manifest_sha256 = sha256(manifest_bytes)
    _read_bundle(stage, manifest_sha256)
    for item in captured:
        _source_bytes_unchanged(item)
    _declaration_parents_unchanged(declarations)
    if _producer_identity() != producer:
        raise IntakeRefusal("hyde_nordic_producer_changed", str(Path(__file__)))
    try:
        _publish_new_output_tree(final_output_root=target, staging_output_root=stage)
    except OSError as exc:
        raise IntakeRefusal("hyde_nordic_publish_failed", str(exc)) from exc
    return read_hyde_nordic_window_bundle(
        target, expected_manifest_sha256=manifest_sha256
    )


def main() -> int:
    """Publish one authenticated base/lower/upper private source-index bundle."""
    parser = argparse.ArgumentParser(description=__doc__)
    for scenario in SCENARIOS:
        parser.add_argument(f"--{scenario}-window", type=Path, required=True)
        parser.add_argument(f"--{scenario}-manifest-sha256", required=True)
    parser.add_argument("--file-inventory", type=Path, required=True)
    parser.add_argument("--file-inventory-sha256", default=_FILE_INVENTORY_SHA256)
    parser.add_argument("--inventory-report", type=Path, required=True)
    parser.add_argument("--inventory-report-sha256", default=_INVENTORY_REPORT_SHA256)
    parser.add_argument("--header-inventory", type=Path, required=True)
    parser.add_argument("--header-inventory-sha256", default=_HEADER_INVENTORY_SHA256)
    parser.add_argument("--conflict-report", type=Path, required=True)
    parser.add_argument("--conflict-report-sha256", default=_CONFLICT_REPORT_SHA256)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    windows = tuple(
        HydeNativeWindowInput(
            scenario,
            getattr(args, f"{scenario}_window"),
            getattr(args, f"{scenario}_manifest_sha256"),
        )
        for scenario in SCENARIOS
    )
    bundle = publish_hyde_nordic_window_bundle(
        windows=windows,
        declarations=HydeDeclarationParentInput(
            args.file_inventory,
            args.file_inventory_sha256,
            args.inventory_report,
            args.inventory_report_sha256,
            args.header_inventory,
            args.header_inventory_sha256,
            args.conflict_report,
            args.conflict_report_sha256,
        ),
        destination=args.destination,
    )
    print(
        encode(
            {
                "manifest_sha256": bundle.manifest_sha256,
                "scenario_token_instances": bundle.scenario_token_instances,
                "selected_index_positions": bundle.selected_index_positions,
            }
        ).decode("utf-8"),
        end="",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
