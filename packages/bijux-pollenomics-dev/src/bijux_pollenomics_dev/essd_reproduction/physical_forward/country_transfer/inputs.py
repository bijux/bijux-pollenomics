"""Bind qualified author-window products, static metadata and fixed response origins."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal
import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

from ...author_lra_spatial.inputs import canonical
from ...nordic_coupled.author_window_support.parameters import decimal as source_decimal
from ...nordic_coupled.literal_window_support.study import read_pin
from ..inputs import decode, require

AXIS = ("Betula", "Pinus")
CORE_KEYS = (
    "abborrtjarnen",
    "bokesjon",
    "bussjosjon",
    "solsoe81",
    "solsoe83",
    "laihalampi",
    "dalmutladdo",
)
METHODS = ("physical_forward", "direct_panel_mean")
COUNTRIES = {"SE": "Sweden", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
METRICS = ("mae_fraction", "hellinger_stable", "total_variation")


def semantic_sha(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def finite(value: object, *, positive: bool = False) -> float:
    require(type(value) in (int, float), "Finite typed number required")
    try:
        result = float(cast(int | float, value))
    except (ValueError, OverflowError) as exc:
        raise ValueError("Nonrepresentable source number") from exc
    require(
        math.isfinite(result) and (result > 0 if positive else result >= 0),
        "Finite source number outside domain",
    )
    return result


def counts(value: object) -> tuple[int, int]:
    require(type(value) is list and len(value) == 2, "Two exact count axes required")
    vector = cast(list[Any], value)
    require(
        all(type(v) is int and 0 <= v < 2**53 for v in vector),
        "Native exact integer count bound required",
    )
    require(0 < sum(vector) < 2**53, "Native positive exact total bound required")
    return cast(int, vector[0]), cast(int, vector[1])


def validate_protocol(protocol: dict[str, Any]) -> None:
    require(
        protocol["schema_version"] == "nordic-physical-transfer-protocol.v1"
        and protocol["taxa"] == list(AXIS)
        and tuple(c["key"] for c in protocol["cores"]) == CORE_KEYS
        and protocol["windows"] == [[n, n + 500] for n in range(2700, 5700, 500)]
        and [p["id"] for p in protocol["profiles"]]
        == ["equal_place_solsoe83", "equal_country_solsoe83", "equal_place_solsoe81"]
        and [p["weighting"] for p in protocol["profiles"]]
        == ["equal_physical_place", "equal_country_then_place", "equal_physical_place"]
        and len(protocol["retained_responses"]) == 9
        and len(protocol["new_response_requests"]) == 3,
        "Exact conditional transfer profile required",
    )
    primary = [k for k in CORE_KEYS if k != "solsoe81"]
    require(
        all(
            p["cores"]
            == (
                primary
                if i < 2
                else ["solsoe81" if k == "solsoe83" else k for k in primary]
            )
            for i, p in enumerate(protocol["profiles"])
        )
        and protocol["experiments"]
        == [
            {
                "id": "swedish_training_scope",
                "targets": list(CORE_KEYS[:3]),
                "scopes": ["swedish_only", "pooled_nordic"],
                "exclusion": "whole_target_physical_family",
            },
            {
                "id": "country_holdout",
                "targets": primary,
                "scopes": ["outside_target_country"],
                "exclusion": "whole_target_country_and_physical_family",
            },
        ],
        "Fixed complete structural cohort required",
    )
    for key, expected in (
        ("contexts", 216),
        ("method_dispositions", 432),
        ("upstream_owners", 542),
        ("upstream_sequences", 7),
        ("primary_physical_places", 6),
        ("primary_countries", 4),
        ("windows_per_place", 6),
        ("primary_window_native_owners", 155),
        ("alternate_window_native_owners", 157),
    ):
        require(
            type(protocol["population"][key]) is int
            and protocol["population"][key] == expected,
            "Declared source/context population differs",
        )
    require(
        protocol["source_max_bytes"] == 8 * 1024**2
        and protocol["limits"]
        == {
            "producer_wall_seconds": 180,
            "observer_wall_seconds": 180,
            "max_rss_bytes": 768 * 1024**2,
            "max_output_bytes": 16 * 1024**2,
        }
        and all(type(v) is int for v in protocol["limits"].values())
        and protocol["scientific_or_field_admission"] is False
        and protocol["source_acquisition"] is False
        and protocol["uncertainty_evaluated"] is False,
        "Original resource and conditional scope required",
    )


def pointer(value: Any, path: str) -> Any:
    require(
        type(path) is str and path.startswith("/"),
        "Literal JSON source pointer required",
    )
    for token in path[1:].split("/"):
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(
                key.isdigit() and str(int(key)) == key and int(key) < len(value),
                "Source pointer position differs",
            )
            value = value[int(key)]
        else:
            require(
                type(value) is dict and key in value, "Source pointer member differs"
            )
            value = value[key]
    return value


def normalized_request(row: dict[str, Any], protocol: dict[str, Any]) -> dict[str, Any]:
    transport = protocol["transport"]
    radius = finite(row["receiver_radius_m"], positive=True)
    inner = finite(
        row.get("inner_radius_m", row.get("source_inner_radius_m")), positive=True
    )
    outer = finite(row["outer_radius_m"], positive=True)
    require(radius == inner < outer, "Declared disk and shore annulus required")
    return {
        "receiver_radius_m": radius,
        "inner_radius_m": inner,
        "outer_radius_m": outer,
        "fall_speed_m_s": finite(row["fall_speed_m_s"], positive=True),
        "wind_speed_m_s": finite(transport["wind_speed_m_s"], positive=True),
        "diffusion_coefficient": finite(
            transport["diffusion_coefficient"], positive=True
        ),
        "turbulence_parameter": finite(
            transport["turbulence_parameter"], positive=True
        ),
        "absolute_tolerance": finite(
            transport["python_absolute_tolerance"], positive=True
        ),
        "relative_tolerance": finite(
            transport["python_relative_tolerance"], positive=True
        ),
        "quadrature_limit": transport["python_quadrature_limit"],
    }


def response_id(row: dict[str, Any], protocol: dict[str, Any]) -> str:
    return "response:" + semantic_sha(normalized_request(row, protocol))


def _metadata(records: bytes, declarations: list[dict[str, Any]]) -> None:
    wanted = {d["metadata_source_locator"] for d in declarations}
    selected = {}
    for line in records.splitlines():
        row = decode(line)
        if row["source_locator"] in wanted:
            require(
                row["source_locator"] not in selected,
                "Duplicate static metadata locator",
            )
            selected[row["source_locator"]] = row
    require(set(selected) == wanted, "Complete static metadata records required")
    for declaration in declarations:
        row = selected[declaration["metadata_source_locator"]]
        values = {v["column"]: v["raw"] for v in row["values"]}
        require(
            len(values) == len(row["values"])
            and row["inventory_sha256"] == declaration["metadata_inventory_sha256"]
            and all(values[k] == v for k, v in declaration["metadata_raw"].items())
            and finite(float(values["siteradius"]), positive=True)
            == declaration["radius_m"]
            and float(values["londd"]) == declaration["longitude"]
            and float(values["latdd"]) == declaration["latitude"]
            and values["Country"] == COUNTRIES[declaration["country"]],
            "Pinned source static geometry/rights metadata differs",
        )


def _origin(protocol: dict[str, Any], documents: dict[str, Any]) -> None:
    """Bind the nine fixed coefficients without retagging old execution environments."""
    transport = protocol["transport"]
    for role in ("swedish_transport_protocol", "nordic_transport_protocol"):
        old = documents[role]
        require(
            old["diffusion_coefficient"] == transport["diffusion_coefficient"]
            and old["turbulence_parameter"] == transport["turbulence_parameter"]
            and old["regional_extent_m"] == transport["outer_radius_m"],
            "Retained transport numerical parameters differ",
        )
        if role.startswith("swedish"):
            profiles = [
                r for r in old["profiles"] if r["id"] == "metadata_radius_wind_3"
            ]
            require(
                len(profiles) == 1
                and profiles[0]["radius_multiplier"] == 1
                and profiles[0]["wind_speed_m_s"] == transport["wind_speed_m_s"],
                "Retained Swedish wind/geometry profile differs",
            )
        else:
            require(
                old["wind_speed_m_s"] == transport["wind_speed_m_s"],
                "Retained Nordic wind profile differs",
            )
    for retained in protocol["retained_responses"]:
        body = documents[retained["source"]]
        require(
            pointer(body, retained["factor_pointer"]) == retained["factor"]
            and pointer(body, retained["error_pointer"])
            == retained["estimated_absolute_error"]
            and retained["rigorous_error_bound"] is False,
            "Retained coefficient/error source pointer differs",
        )
        request = normalized_request(retained, protocol)
        if retained["source"] == "nordic_response":
            row = pointer(body, retained["factor_pointer"].rsplit("/", 1)[0])
            expected = {
                "receiver_radius_m": request["receiver_radius_m"],
                "source_inner_radius_m": request["inner_radius_m"],
                "regional_extent_m": request["outer_radius_m"],
                "fall_speed_m_s": request["fall_speed_m_s"],
                "wind_speed_m_s": request["wind_speed_m_s"],
                "empirical_diffusion_coefficient": request["diffusion_coefficient"],
                "turbulence_parameter": request["turbulence_parameter"],
            }
            require(
                all(
                    type(row[k]) in (int, float) and row[k] == v
                    for k, v in expected.items()
                ),
                "Retained Nordic response tuple differs",
            )
        else:
            parts = retained["factor_pointer"].split("/")
            core = body["cores"][int(parts[2])]
            quad = core["quadrature"][int(parts[4])]
            axis = int(parts[-1])
            require(
                quad["profile"] == "metadata_radius_wind_3"
                and quad["rigorous_error_bound"] is False
                and core["metadata_static_radius_m"] == request["receiver_radius_m"]
                and core["fall_speed_m_s"][axis] == request["fall_speed_m_s"]
                and core["native_site_id"]
                in {c["identity"]["site_id"] for c in protocol["cores"][:3]},
                "Retained Swedish response profile differs",
            )
    sources = protocol["scientific_sources"]
    for report in (documents["swedish_imports"], documents["nordic_imports"]):
        for role in ("receiver_numerical_source", "gpm_numerical_source"):
            pin = sources[role]
            if "module_origins" in report:
                matches = [
                    r
                    for r in report["module_origins"]
                    if r.get("relative_path") == pin["path"]
                ]
                require(
                    any(
                        r.get("sha256") == pin["sha256"]
                        and r.get("bytes") == pin["bytes"]
                        for r in matches
                    ),
                    "Old numerical callable origin differs",
                )
            else:
                require(
                    report.get(pin["path"], {}).get("sha256") == pin["sha256"],
                    "Old numerical import closure differs",
                )


def load_inputs(repository: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    """Use only the declared qualified local products; never reopen original counts."""
    validate_protocol(protocol)
    maximum = protocol["source_max_bytes"]
    sourcepins = [
        deepcopy(protocol["upstream_protocol"]),
        *deepcopy(list(protocol["qualified_products"].values())),
        *deepcopy(list(protocol["scientific_sources"].values())),
    ]
    raw = {pin["path"]: read_pin(repository, pin, maximum) for pin in sourcepins}
    upstream = decode(raw[protocol["upstream_protocol"]["path"]])
    products = {
        k: decode(raw[p["path"]]) for k, p in protocol["qualified_products"].items()
    }
    result, verification = products["result"], products["verification"]
    require(
        result["source_commit"]
        == protocol["upstream_source_commit"]
        == verification["source_commit"]
        and result["source_guards_passed"] is True
        and verification["status"] == "verified"
        and verification["producer_result_sha256"]
        == protocol["qualified_products"]["result"]["sha256"]
        and verification["source_guards_passed"] is True
        and verification["native_sample_owners_checked"] == 542
        and verification["requested_windows_checked"] == 42,
        "Qualified source audit/independent result identity differs",
    )
    for key, pin in result["products"].items():
        declared = protocol["qualified_products"][key]
        require(
            Path(declared["path"]).name == pin["path"]
            and all(declared[k] == pin[k] for k in ("bytes", "sha256")),
            "Qualified upstream output identity differs",
        )
    require(
        set(result["products"]) == {*CORE_KEYS, "parameters", "input_manifest"},
        "Complete upstream product inventory required",
    )
    selected = products["parameters"]["selected"]
    expected = {
        "taxa": protocol["parameters"]["targets"],
        **{k: protocol["parameters"][k] for k in selected if k != "taxa"},
    }
    full = products["parameters"]
    names = full["axis"]
    means = full["mean_rows"]
    matrix = full["covariance_rows"]
    require(
        selected == expected
        and upstream["parameters"] == protocol["parameters"]
        and full["source_pins"] == upstream["author_sources"]
        and len(names) == 31
        and all(type(n) is str and n for n in names)
        and len(set(names)) == 31
        and [r["A.series"] for r in means] == names == [r["A.series"] for r in matrix]
        and all(set(r) == {"A.series", *names} for r in matrix)
        and all(set(r) == {"A.series", "alpha", "vg"} for r in means),
        "Coherent full author parameter profile differs",
    )
    for i, name in enumerate(names):
        require(
            source_decimal(means[i]["alpha"]) > 0
            and source_decimal(means[i]["vg"]) > 0
            and source_decimal(matrix[i][name]) >= 0,
            "Full author parameter number differs",
        )
        for j, other in enumerate(names):
            require(
                source_decimal(matrix[i][other]) == source_decimal(matrix[j][name])
                and (i == j or source_decimal(matrix[i][other]) == 0),
                "Full author covariance profile differs",
            )
    selected_indices = [names.index(t) for t in AXIS]
    require(
        [means[i]["alpha"] for i in selected_indices] == selected["alpha_text"]
        and [means[i]["vg"] for i in selected_indices]
        == selected["fall_speed_m_s_text"]
        and [[matrix[i][t] for t in AXIS] for i in selected_indices]
        == selected["covariance_text"]
        and [i + 2 for i in selected_indices] == selected["literal_file_line_numbers"],
        "Selected author block differs from full source rows",
    )
    originals = {c["key"]: c for c in upstream["cores"]}
    require(
        set(originals) == set(CORE_KEYS) and len(upstream["cores"]) == 7,
        "Complete upstream core contract required",
    )
    ppe = tuple(finite(float(v), positive=True) for v in selected["alpha_text"])
    covariance = tuple(
        tuple(float(Decimal(v)) for v in row) for row in selected["covariance_text"]
    )
    require(
        len(covariance) == 2
        and all(len(r) == 2 for r in covariance)
        and all(math.isfinite(v) for r in covariance for v in r),
        "Exact selected covariance dimensions differ",
    )
    cores = {}
    seen: set[int] = set()
    for declaration in protocol["cores"]:
        key = declaration["key"]
        ledger = products[key]
        original = originals[key]
        require(
            original["identity"] == declaration["identity"]
            and original["chronology"] == declaration["chronology"]
            and original["physical_family"] == declaration["physical_family"]
            and original["country"] == COUNTRIES[declaration["country"]],
            "Qualified upstream chronology/family/country contract differs",
        )
        require(
            ledger["schema_version"] == "nordic-author-core-support.v1"
            and ledger["identity"] == declaration["identity"]
            and ledger["physical_family"] == declaration["physical_family"]
            and ledger["country"] == COUNTRIES[declaration["country"]]
            and ledger["taxon_axis"] == list(AXIS)
            and ledger["chronology"]["selected_chronology_id"]
            == declaration["chronology"]["selected_id"]
            and len(ledger["samples"])
            == declaration["identity"]["source_sample_count"],
            "Source ledger owner/axis/point chronology differs",
        )
        ids = [r["sample_id"] for r in ledger["samples"]]
        require(
            all(type(i) is int for i in ids)
            and len(ids) == len(set(ids))
            and not seen.intersection(ids),
            "Duplicate or foreign upstream source owner",
        )
        seen.update(ids)
        windows = ledger["windows"]
        require(
            [w["window"] for w in windows] == protocol["windows"],
            "All six source windows required",
        )
        window_owners = []
        for cell in windows:
            members = cell["sample_ids"]
            window_owners.extend(members)
            require(
                type(cell["member_count"]) is int
                and cell["member_count"] == len(members)
                and set(members) <= set(ids)
                and len(set(members)) == len(members),
                "Source window membership differs",
            )
            if cell["status"] == "supported":
                vector = counts(cell["panel_counts"])
                require(
                    type(cell["panel_N"]) is int
                    and sum(vector) == cell["panel_N"]
                    and type(cell["pollen_N"]) is int
                    and cell["pollen_N"] >= cell["panel_N"]
                    and cell["excluded_pollen_N"] == cell["pollen_N"] - cell["panel_N"],
                    "Complete source panel/full-mass denominator differs",
                )
        require(
            len(window_owners) == len(set(window_owners)),
            "Source owner repeated between windows",
        )
        cores[key] = {
            "declaration": deepcopy(declaration),
            "windows": deepcopy(windows),
        }
    require(len(seen) == 542, "All upstream source owners required")
    for profile, count_key in (
        (protocol["profiles"][0], "primary_window_native_owners"),
        (protocol["profiles"][2], "alternate_window_native_owners"),
    ):
        require(
            sum(
                w["member_count"] for k in profile["cores"] for w in cores[k]["windows"]
            )
            == protocol["population"][count_key],
            "Qualified window owner denominator differs",
        )
    science = {
        key: raw[pin["path"]] for key, pin in protocol["scientific_sources"].items()
    }
    _metadata(science["metadata_records"], protocol["cores"])
    documents = {
        key: json.loads(value)
        for key, value in science.items()
        if protocol["scientific_sources"][key]["path"].endswith(".json")
    }
    _origin(protocol, documents)
    return {
        "cores": cores,
        "ppe": ppe,
        "covariance": covariance,
        "scientific_documents": documents,
        "sourcepins": sourcepins,
    }
