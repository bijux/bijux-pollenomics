"""Authenticate compact HYDE NetCDF declarations without opening native payloads."""

from __future__ import annotations

from collections import Counter
from pathlib import Path
import re
from typing import Literal, cast

from ...quarantine import IntakeRefusal
from ..local.contracts import digest
from .contracts import (
    SCENARIOS,
    VARIABLES,
    HydeNetcdfDeclarationInventory,
    NetcdfAxisDeclaration,
    NetcdfFileDeclaration,
    _mint_inventory,
)
from .parsing import (
    array,
    boolean,
    integer,
    json_lines,
    json_value,
    number,
    obj,
    read_pinned,
    string_object,
    text,
)

_FILE_LIMIT = 1024 * 1024
_REPORT_LIMIT = 64 * 1024
_HEADER_LIMIT = 12 * 1024 * 1024
_CONFLICT_LIMIT = 64 * 1024
_FILE_FIELDS = {"path", "bytes", "mtime_ns", "sha256", "ctime_ns", "inode"}
_HEADER_FIELDS = {
    "path",
    "bytes",
    "mtime_ns",
    "format",
    "attributes",
    "dimensions",
    "variables",
}
_DIMENSION_FIELDS = {"size", "unlimited"}
_AXIS_FIELDS = {"dtype", "dimensions", "shape", "attributes", "coordinate_values"}
_DATA_FIELDS = {"dtype", "dimensions", "shape", "attributes"}
_TIME_ATTRIBUTES = {"standard_name", "units", "calendar"}
_SPACE_ATTRIBUTES = {"standard_name", "long_name", "units"}
_DATA_ATTRIBUTES = {"_FillValue", "standard_name", "long_name", "units"}
_REPORT_FIELDS = {
    "status",
    "file_count",
    "byte_count",
    "archive_member_count",
    "source_stat_inventory_unchanged",
    "files_sha256",
    "elapsed_seconds",
}
_CONFLICT_FIELDS = {
    "schema_version",
    "inputs",
    "custody",
    "claims",
    "scenario_semantics",
    "conflicts",
    "admission",
}
_REQUIRED_CONFLICTS = {
    "calendar_mapping_unresolved",
    "coverage_end_year_conflict",
    "license_declaration_conflict",
    "release_identity_conflict",
    "scenario_uncertainty_semantics_unresolved",
    "zero_ad_calendar_interpretation_unresolved",
}
_REQUIRED_REVIEWS = [
    "qualified_release_identity",
    "qualified_release_specific_rights",
    "native_calendar_and_0ad_interpretation",
    "coverage_end_year",
    "scenario_uncertainty_semantics",
]


def _reopen_hyde_netcdf_declaration_inventory(
    canonical_bytes: bytes,
    *,
    file_inventory_path: Path,
    expected_file_inventory_sha256: str,
    inventory_report_path: Path,
    expected_inventory_report_sha256: str,
    header_inventory_path: Path,
    expected_header_inventory_sha256: str,
    conflict_report_path: Path,
    expected_conflict_report_sha256: str,
) -> HydeNetcdfDeclarationInventory:
    product = _read_hyde_netcdf_declaration_inventory(
        file_inventory_path=file_inventory_path,
        expected_file_inventory_sha256=expected_file_inventory_sha256,
        inventory_report_path=inventory_report_path,
        expected_inventory_report_sha256=expected_inventory_report_sha256,
        header_inventory_path=header_inventory_path,
        expected_header_inventory_sha256=expected_header_inventory_sha256,
        conflict_report_path=conflict_report_path,
        expected_conflict_report_sha256=expected_conflict_report_sha256,
    )
    if type(canonical_bytes) is not bytes or canonical_bytes != product.canonical_bytes:
        raise IntakeRefusal(
            "hyde_netcdf_canonical_identity_invalid", "source-bound canonical bytes"
        )
    return product


def _read_hyde_netcdf_declaration_inventory(
    *,
    file_inventory_path: Path,
    expected_file_inventory_sha256: str,
    inventory_report_path: Path,
    expected_inventory_report_sha256: str,
    header_inventory_path: Path,
    expected_header_inventory_sha256: str,
    conflict_report_path: Path,
    expected_conflict_report_sha256: str,
) -> HydeNetcdfDeclarationInventory:
    """Read four explicitly pinned compact inputs for internal verification."""
    contents = {
        "file_inventory": read_pinned(
            file_inventory_path,
            expected_file_inventory_sha256,
            _FILE_LIMIT,
            "file_inventory",
        ),
        "inventory_report": read_pinned(
            inventory_report_path,
            expected_inventory_report_sha256,
            _REPORT_LIMIT,
            "inventory_report",
        ),
        "header_inventory": read_pinned(
            header_inventory_path,
            expected_header_inventory_sha256,
            _HEADER_LIMIT,
            "header_inventory",
        ),
        "conflict_report": read_pinned(
            conflict_report_path,
            expected_conflict_report_sha256,
            _CONFLICT_LIMIT,
            "conflict_report",
        ),
    }
    file_rows = _file_inventory(contents["file_inventory"])
    report = _inventory_report(contents["inventory_report"], file_rows)
    conflict = _conflict_report(contents["conflict_report"], report)
    if report["files_sha256"] != expected_file_inventory_sha256:
        raise IntakeRefusal("hyde_netcdf_inventory_identity_invalid", "file inventory")
    if conflict["header_sha256"] != expected_header_inventory_sha256 or conflict[
        "header_bytes"
    ] != len(contents["header_inventory"]):
        raise IntakeRefusal("hyde_netcdf_conflict_identity_invalid", "header inventory")
    headers = array(
        json_value(contents["header_inventory"], "header_inventory"), "headers"
    )
    declarations, axes, header_claims = _headers(headers, file_rows)
    netcdf_paths = {path for path in file_rows if Path(path).suffix == ".nc"}
    if netcdf_paths != {row.path for row in declarations}:
        raise IntakeRefusal("hyde_netcdf_file_closure_invalid", "48 declared paths")
    _bind_conflict_claims(conflict, header_claims, declarations)
    return _mint_inventory(
        input_sha256=tuple(
            sorted(
                (
                    ("file_inventory", digest(expected_file_inventory_sha256)),
                    ("inventory_report", digest(expected_inventory_report_sha256)),
                    ("header_inventory", digest(expected_header_inventory_sha256)),
                    ("conflict_report", digest(expected_conflict_report_sha256)),
                )
            )
        ),
        custody_manifest_sha256=digest(conflict["custody_manifest_sha256"]),
        dataset_inventory_sha256=digest(conflict["dataset_inventory_sha256"]),
        dataset_file_count=integer(report["file_count"], "file_count"),
        dataset_byte_count=integer(report["byte_count"], "byte_count"),
        axes=axes,
        files=declarations,
        conflicts=tuple(sorted(_REQUIRED_CONFLICTS)),
    )


def _file_inventory(content: bytes) -> dict[str, dict[str, object]]:
    rows: dict[str, dict[str, object]] = {}
    for value in json_lines(content, "file_inventory"):
        row = obj(value, _FILE_FIELDS, "file_inventory row")
        path = text(row["path"], "file path")
        if path.startswith("/") or ".." in Path(path).parts or path in rows:
            raise IntakeRefusal("hyde_netcdf_file_identity_invalid", path)
        row["bytes"] = integer(row["bytes"], "file bytes")
        row["mtime_ns"] = integer(row["mtime_ns"], "file mtime")
        integer(row["ctime_ns"], "file ctime")
        integer(row["inode"], "file inode")
        row["sha256"] = digest(row["sha256"])
        rows[path] = row
    return rows


def _inventory_report(
    content: bytes, files: dict[str, dict[str, object]]
) -> dict[str, object]:
    report = obj(
        json_value(content, "inventory_report"),
        _REPORT_FIELDS,
        "inventory report",
    )
    if (
        report["status"] != "hashed_and_inventoried_not_admitted"
        or boolean(report["source_stat_inventory_unchanged"], "source stat") is not True
        or not digest(report["files_sha256"])
    ):
        raise IntakeRefusal("hyde_netcdf_inventory_posture_invalid", "report")
    count = integer(report["file_count"], "file_count")
    total = integer(report["byte_count"], "byte_count")
    integer(report["archive_member_count"], "archive_member_count")
    number(report["elapsed_seconds"], "elapsed_seconds")
    retained_bytes = sum(cast(int, row["bytes"]) for row in files.values())
    if count != len(files) or total != retained_bytes:
        raise IntakeRefusal("hyde_netcdf_inventory_denominator_invalid", "report")
    return report


def _conflict_report(content: bytes, report: dict[str, object]) -> dict[str, object]:
    source = obj(
        json_value(content, "conflict_report"),
        _CONFLICT_FIELDS,
        "conflict report",
    )
    if source["schema_version"] != "hyde-native-metadata-review.v1":
        raise IntakeRefusal("hyde_netcdf_conflict_identity_invalid", "schema")
    custody = obj(
        source["custody"],
        {"counts", "dataset_inventory_sha256", "manifest_sha256"},
        "custody",
    )
    counts = obj(
        custody["counts"],
        {
            "ancillary_file_count",
            "archive_file_count",
            "archive_member_count",
            "byte_count",
            "dataset_byte_count",
            "dataset_file_count",
            "file_count",
            "netcdf_named_file_count",
        },
        "custody counts",
    )
    if (
        integer(counts["dataset_file_count"], "dataset count") != report["file_count"]
        or integer(counts["dataset_byte_count"], "dataset bytes")
        != report["byte_count"]
        or integer(counts["netcdf_named_file_count"], "netcdf count") != 48
        or integer(counts["archive_member_count"], "archive count")
        != report["archive_member_count"]
    ):
        raise IntakeRefusal(
            "hyde_netcdf_custody_denominator_invalid", "conflict report"
        )
    scenarios = obj(
        source["scenario_semantics"],
        {
            "labels",
            "netcdf_header_counts",
            "role",
            "confidence_bounds_status",
            "pointwise_ordering_contract",
        },
        "scenario semantics",
    )
    scenario_counts = obj(
        scenarios["netcdf_header_counts"], set(SCENARIOS), "scenario counts"
    )
    if (
        array(scenarios["labels"], "scenario labels") != list(SCENARIOS)
        or scenarios["role"] != "provider_estimate_scenarios"
        or scenarios["confidence_bounds_status"] != "not_declared"
        or scenarios["pointwise_ordering_contract"] != "none"
        or any(integer(scenario_counts[name], name) != 16 for name in SCENARIOS)
    ):
        raise IntakeRefusal("hyde_netcdf_scenario_semantics_invalid", "conflict report")
    conflicts = {
        text(value, "conflict") for value in array(source["conflicts"], "conflicts")
    }
    if conflicts != _REQUIRED_CONFLICTS:
        raise IntakeRefusal("hyde_netcdf_conflicts_invalid", "conflict report")
    admission = obj(
        source["admission"],
        {
            "native_release_status",
            "scientific_acceptance",
            "public_release_allowed",
            "country_projection_allowed",
            "canonical_calendar_conversion_allowed",
            "required_reviews",
        },
        "admission",
    )
    if (
        admission["native_release_status"] != "refused_pending_review"
        or admission["scientific_acceptance"] != "not_evaluated"
        or admission["public_release_allowed"] is not False
        or admission["country_projection_allowed"] is not False
        or admission["canonical_calendar_conversion_allowed"] is not False
        or array(admission["required_reviews"], "required reviews") != _REQUIRED_REVIEWS
    ):
        raise IntakeRefusal("hyde_netcdf_admission_invalid", "conflict report")
    inputs = [
        obj(value, {"role", "bytes", "sha256"}, "conflict input")
        for value in array(source["inputs"], "inputs")
    ]
    header_inputs = [row for row in inputs if row["role"] == "netcdf_headers"]
    if len(header_inputs) != 1:
        raise IntakeRefusal("hyde_netcdf_conflict_identity_invalid", "header input")
    header_bytes = integer(header_inputs[0]["bytes"], "header input bytes")
    return {
        "claims": source["claims"],
        "custody_manifest_sha256": custody["manifest_sha256"],
        "dataset_inventory_sha256": custody["dataset_inventory_sha256"],
        "header_sha256": digest(header_inputs[0]["sha256"]),
        "header_bytes": header_bytes,
    }


def _headers(
    values: list[object], files: dict[str, dict[str, object]]
) -> tuple[
    tuple[NetcdfFileDeclaration, ...],
    tuple[NetcdfAxisDeclaration, ...],
    dict[str, str],
]:
    if len(values) != 48:
        raise IntakeRefusal("hyde_netcdf_header_denominator_invalid", str(len(values)))
    declarations: list[NetcdfFileDeclaration] = []
    shared_axes: tuple[NetcdfAxisDeclaration, ...] | None = None
    releases: set[str] = set()
    descriptions: set[str] = set()
    licenses: set[str] = set()
    calendars: set[str] = set()
    calendar_units: set[str] = set()
    for value in values:
        header = obj(value, _HEADER_FIELDS, "header")
        declaration, axes = _header(header, files)
        if shared_axes is None:
            shared_axes = axes
        elif axes != shared_axes:
            raise IntakeRefusal("hyde_netcdf_axis_identity_invalid", declaration.path)
        attributes = dict(declaration.global_attributes)
        releases.add(attributes.get("version", ""))
        descriptions.add(attributes.get("description", ""))
        licenses.add(attributes.get("license", ""))
        time = axes[0]
        calendars.add(time.calendar or "")
        calendar_units.add(time.units)
        declarations.append(declaration)
    declarations.sort(key=lambda row: (row.scenario, row.variable))
    expected = {
        (scenario, variable) for scenario in SCENARIOS for variable in VARIABLES
    }
    actual = {(row.scenario, row.variable) for row in declarations}
    if len(declarations) != len(actual) or actual != expected:
        raise IntakeRefusal("hyde_netcdf_variable_closure_invalid", "16x3")
    _bind_variable_declarations(declarations)
    claims = {
        "release": _one(releases, "release"),
        "release_description": _one(descriptions, "release_description"),
        "license": _one(licenses, "license"),
        "calendar": _one(calendars, "calendar"),
        "calendar_units": _one(calendar_units, "calendar_units"),
    }
    assert shared_axes is not None
    return tuple(declarations), shared_axes, claims


def _header(
    header: dict[str, object], files: dict[str, dict[str, object]]
) -> tuple[NetcdfFileDeclaration, tuple[NetcdfAxisDeclaration, ...]]:
    path = text(header["path"], "header path")
    match = re.fullmatch(
        r"original/gbc2025_7apr_(base|lower|upper)/NetCDF/([a-z_]+)\.nc", path
    )
    if match is None or match[2] not in VARIABLES:
        raise IntakeRefusal("hyde_netcdf_path_invalid", path)
    inventory = files.get(path)
    if inventory is None:
        raise IntakeRefusal("hyde_netcdf_file_identity_invalid", path)
    size = integer(header["bytes"], "header bytes")
    mtime = integer(header["mtime_ns"], "header mtime")
    if size != inventory["bytes"] or mtime != inventory["mtime_ns"]:
        raise IntakeRefusal("hyde_netcdf_file_identity_invalid", path)
    if header["format"] != "NETCDF4":
        raise IntakeRefusal("hyde_netcdf_format_invalid", path)
    dimensions = obj(header["dimensions"], {"time", "lat", "lon"}, "dimensions")
    variables = obj(header["variables"], {"time", "lat", "lon", match[2]}, "variables")
    axes = tuple(
        _axis(name, variables[name], dimensions[name])
        for name in ("time", "lat", "lon")
    )
    data = obj(variables[match[2]], _DATA_FIELDS, "data variable")
    data_dimensions = tuple(
        text(value, "data dimension")
        for value in array(data["dimensions"], "data dimensions")
    )
    data_shape = tuple(
        integer(value, "data shape") for value in array(data["shape"], "data shape")
    )
    if data_dimensions != ("time", "lat", "lon") or data_shape != tuple(
        axis.size for axis in axes
    ):
        raise IntakeRefusal("hyde_netcdf_data_dimensions_invalid", path)
    data_attributes = obj(data["attributes"], _DATA_ATTRIBUTES, "data attributes")
    global_attributes = string_object(header["attributes"], "global attributes")
    retained_attributes = tuple(sorted(global_attributes.items()))
    return (
        NetcdfFileDeclaration(
            scenario=cast(Literal["base", "lower", "upper"], match[1]),
            variable=match[2],
            path=path,
            bytes=size,
            mtime_ns=mtime,
            source_sha256=digest(inventory["sha256"]),
            file_format="NETCDF4",
            global_attributes=retained_attributes,
            dtype=text(data["dtype"], "data dtype"),
            dimensions=data_dimensions,
            shape=data_shape,
            standard_name=text(data_attributes["standard_name"], "standard_name"),
            long_name=text(data_attributes["long_name"], "long_name"),
            units=text(data_attributes["units"], "units"),
            fill_value=number(data_attributes["_FillValue"], "fill value"),
        ),
        axes,
    )


def _axis(name: str, value: object, dimension_value: object) -> NetcdfAxisDeclaration:
    variable = obj(value, _AXIS_FIELDS, f"{name} axis")
    dimension = obj(dimension_value, _DIMENSION_FIELDS, f"{name} dimension")
    size = integer(dimension["size"], f"{name} size")
    dimensions = array(variable["dimensions"], f"{name} dimensions")
    shape = array(variable["shape"], f"{name} shape")
    values = tuple(
        number(item, f"{name} coordinate")
        for item in array(variable["coordinate_values"], f"{name} coordinates")
    )
    if dimensions != [name] or shape != [size] or len(values) != size or size < 2:
        raise IntakeRefusal("hyde_netcdf_axis_dimensions_invalid", name)
    spacing = tuple(values[index + 1] - values[index] for index in range(size - 1))
    if all(step > 0 for step in spacing):
        orientation = "ascending"
    elif all(step < 0 for step in spacing):
        orientation = "descending"
    else:
        raise IntakeRefusal("hyde_netcdf_axis_order_invalid", name)
    expected_orientation = "descending" if name == "lat" else "ascending"
    if orientation != expected_orientation:
        raise IntakeRefusal("hyde_netcdf_axis_order_invalid", name)
    fields = _TIME_ATTRIBUTES if name == "time" else _SPACE_ATTRIBUTES
    attributes = obj(variable["attributes"], fields, f"{name} attributes")
    standard_names = {"time": "time", "lat": "latitude", "lon": "longitude"}
    if attributes["standard_name"] != standard_names[name]:
        raise IntakeRefusal("hyde_netcdf_axis_identity_invalid", name)
    return NetcdfAxisDeclaration(
        name=cast(Literal["time", "lat", "lon"], name),
        dtype=text(variable["dtype"], f"{name} dtype"),
        dimension=name,
        size=size,
        unlimited=boolean(dimension["unlimited"], f"{name} unlimited"),
        standard_name=standard_names[name],
        long_name=(
            None
            if name == "time"
            else text(attributes["long_name"], f"{name} long name")
        ),
        units=text(attributes["units"], f"{name} units"),
        calendar=text(attributes["calendar"], "calendar") if name == "time" else None,
        coordinate_values=values,
        spacing=spacing,
        orientation=cast(Literal["ascending", "descending"], orientation),
    )


def _one(values: set[str], label: str) -> str:
    if len(values) != 1 or "" in values:
        raise IntakeRefusal("hyde_netcdf_header_claim_invalid", label)
    return next(iter(values))


def _bind_variable_declarations(declarations: list[NetcdfFileDeclaration]) -> None:
    """Require each variable's scientific declaration to agree across scenarios."""
    for variable in VARIABLES:
        rows = [row for row in declarations if row.variable == variable]
        signatures = {
            (
                row.dtype,
                row.dimensions,
                row.shape,
                row.standard_name,
                row.long_name,
                row.units,
                row.fill_value,
            )
            for row in rows
        }
        if len(rows) != 3 or len(signatures) != 1:
            raise IntakeRefusal("hyde_netcdf_variable_declaration_invalid", variable)


def _bind_conflict_claims(
    conflict: dict[str, object],
    header_claims: dict[str, str],
    declarations: tuple[NetcdfFileDeclaration, ...],
) -> None:
    claims = [
        obj(value, {"topic", "source", "value", "context"}, "claim")
        for value in array(conflict["claims"], "claims")
    ]
    retained: dict[str, str] = {}
    for claim in claims:
        topic = text(claim["topic"], "claim topic")
        if claim["source"] == "netcdf_headers" and claim["context"] == "48_of_48":
            if topic in retained:
                raise IntakeRefusal("hyde_netcdf_header_claim_invalid", topic)
            retained[topic] = text(claim["value"], "claim value")
    if retained != header_claims:
        raise IntakeRefusal("hyde_netcdf_header_claim_invalid", "conflict binding")
    counts = Counter(row.scenario for row in declarations)
    if counts != Counter(dict.fromkeys(SCENARIOS, 16)):
        raise IntakeRefusal("hyde_netcdf_scenario_denominator_invalid", "headers")
