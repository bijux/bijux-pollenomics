"""Independent custody and complete fixed-response transfer readback."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal, localcontext
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any

from bijux_pollenomics_dev.essd_reproduction.author_lra_spatial.products import (
    code_state,
)
from tests.source_completion.pollen_reconstruction.krageholm_regional_source_support.verification import (
    decode,
    pairs,
    refuse_constant,
    same,
)
from tests.source_completion.pollen_reconstruction.nordic_author_window_support.verification import (
    committed_protocol,
    ordinary,
    read_pin,
)

from .algebra import (
    PRECISION,
    compare,
    direct_prediction,
    metrics,
    number,
    predict,
    require,
)
from .algebra import (
    inverse as scalar_inverse,
)
from .population import METHODS, plan, summaries


def pointer(value: Any, path: str) -> Any:
    require(type(path) is str and path.startswith("/"), "absolute JSON pointer")
    for part in path[1:].split("/"):
        key = part.replace("~1", "/").replace("~0", "~")
        value = value[int(key)] if isinstance(value, list) else value[key]
    return value


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, allow_nan=False, sort_keys=True, separators=(",", ":")
    ).encode()


def json_value(body: bytes) -> Any:
    return json.loads(
        body,
        parse_float=Decimal,
        parse_constant=refuse_constant,
        object_pairs_hook=pairs,
    )


def response_identity(radius: Any, fall: Any, protocol: dict[str, Any]) -> str:
    transport = protocol["transport"]
    arguments = {
        "receiver_radius_m": float(radius),
        "inner_radius_m": float(radius),
        "outer_radius_m": float(transport["outer_radius_m"]),
        "fall_speed_m_s": float(fall),
        "wind_speed_m_s": float(transport["wind_speed_m_s"]),
        "diffusion_coefficient": float(transport["diffusion_coefficient"]),
        "turbulence_parameter": float(transport["turbulence_parameter"]),
        "absolute_tolerance": float(transport["python_absolute_tolerance"]),
        "relative_tolerance": float(transport["python_relative_tolerance"]),
        "quadrature_limit": transport["python_quadrature_limit"],
    }
    return "response:" + sha256(canonical(arguments)).hexdigest()


def source_binding(repository: Path, protocol: dict[str, Any]) -> dict[str, Any]:
    """Reuse authenticated qualified source accounting, without reopening native parts."""
    cap = protocol["source_max_bytes"]
    require(
        protocol["schema_version"] == "nordic-physical-transfer-protocol.v1"
        and protocol["taxa"] == ["Betula", "Pinus"],
        "declared point-transfer profile",
    )
    bodies = {
        key: read_pin(repository, pin, cap)
        for key, pin in protocol["qualified_products"].items()
    }
    original = decode(read_pin(repository, protocol["upstream_protocol"], cap))
    old = {key: decode(raw) for key, raw in bodies.items()}
    result, observed = old["result"], old["verification"]
    require(
        result["source_commit"]
        == observed["source_commit"]
        == protocol["upstream_source_commit"]
        and observed["status"] == "verified"
        and observed["source_guards_passed"] is True
        and observed["producer_result_sha256"]
        == protocol["qualified_products"]["result"]["sha256"]
        and observed["native_sample_owners_checked"] == 542
        and observed["requested_windows_checked"] == 42
        and observed["window_status_counts"] == {"supported": 41, "empty_window": 1},
        "qualified corrected pollen-role source population",
    )
    require(result["source_guards_passed"] is True, "qualified source guards")
    same(result["protocol"], protocol["upstream_protocol"])
    for key, pin in result["products"].items():
        require(
            key in bodies
            and Path(pin["path"]).name
            == Path(protocol["qualified_products"][key]["path"]).name
            and pin["bytes"] == len(bodies[key])
            and pin["sha256"] == sha256(bodies[key]).hexdigest(),
            "qualified source member identity",
        )
    parameters = old["parameters"]
    require(
        parameters["schema_version"] == "nordic-author-parameters.v1"
        and len(parameters["axis"]) == len(set(parameters["axis"])) == 31
        and len(parameters["mean_rows"]) == len(parameters["covariance_rows"]) == 31,
        "full qualified parameter axes",
    )
    names = parameters["axis"]
    require(
        [row["A.series"] for row in parameters["mean_rows"]] == names
        and [row["A.series"] for row in parameters["covariance_rows"]] == names,
        "ordered coherent parameter rows",
    )
    for i, name in enumerate(names):
        mean, covariance = parameters["mean_rows"][i], parameters["covariance_rows"][i]
        require(
            set(mean) == {"A.series", "alpha", "vg"}
            and set(covariance) == {"A.series", *names}
            and all(
                type(mean[key]) is str and Decimal(mean[key]).is_finite()
                for key in ("alpha", "vg")
            )
            and all(type(covariance[key]) is str for key in names)
            and Decimal(mean["alpha"]) > 0
            and Decimal(mean["vg"]) > 0
            and Decimal(covariance[name]) >= 0,
            "positive source means and covariance diagonal",
        )
        for j, other in enumerate(names):
            left, right = (
                Decimal(covariance[other]),
                Decimal(parameters["covariance_rows"][j][name]),
            )
            require(
                left.is_finite() and left == right, "finite symmetric full covariance"
            )
    selected = parameters["selected"]
    same(
        selected,
        {
            "taxa": protocol["taxa"],
            **{
                key: protocol["parameters"][key]
                for key in (
                    "alpha_text",
                    "fall_speed_m_s_text",
                    "covariance_text",
                    "literal_file_line_numbers",
                )
            },
        },
    )
    for axis, name in enumerate(protocol["taxa"]):
        i = names.index(name)
        require(
            selected["literal_file_line_numbers"][axis] == i + 2
            and selected["alpha_text"][axis] == parameters["mean_rows"][i]["alpha"]
            and selected["fall_speed_m_s_text"][axis]
            == parameters["mean_rows"][i]["vg"]
            and selected["covariance_text"][axis]
            == [parameters["covariance_rows"][i][n] for n in protocol["taxa"]],
            "literal selected parameter submatrix",
        )
    same(parameters["source_pins"], original["author_sources"])
    core_data = {}
    for core in protocol["cores"]:
        key, ledger = core["key"], old[core["source_ledger"]]
        source_core = next(c for c in original["cores"] if c["key"] == key)
        require(
            core["identity"] == source_core["identity"] == ledger["identity"]
            and core["physical_family"] == ledger["physical_family"]
            and ledger["country"]
            == {"SE": "Sweden", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}[
                core["country"]
            ]
            and source_core["chronology"] == core["chronology"]
            and ledger["taxon_axis"] == protocol["taxa"],
            "source core/chronology/family axis",
        )
        require(
            len(ledger["samples"]) == core["identity"]["source_sample_count"]
            and [w["window"] for w in ledger["windows"]] == protocol["windows"],
            "all source owners/windows retained",
        )
        for window in ledger["windows"]:
            members = [s for s in ledger["samples"] if s["window"] == window["window"]]
            require(
                window["sample_ids"] == [s["sample_id"] for s in members]
                and window["member_count"] == len(members),
                "exact source window membership",
            )
            if window["status"] == "supported":
                require(
                    all(
                        type(s["panel_counts"]) is list
                        and len(s["panel_counts"]) == 2
                        and all(type(n) is int and n >= 0 for n in s["panel_counts"])
                        for s in members
                    ),
                    "source sample integer counts including genuine zero",
                )
                totals = [sum(s["panel_counts"][i] for s in members) for i in range(2)]
                require(
                    window["panel_counts"] == totals
                    and window["panel_N"] == sum(totals)
                    and window["pollen_N"] - window["panel_N"]
                    == window["excluded_pollen_N"],
                    "qualified window panel/full/excluded closure",
                )
            else:
                require(
                    window["status"] == "empty_window"
                    and not members
                    and window["panel_counts"] is None,
                    "explicit source empty support",
                )
        core_data[key] = ledger
    require(
        sum(len(c["samples"]) for c in core_data.values()) == 542,
        "complete qualified source owner population",
    )
    for index, field in (
        (0, "primary_window_native_owners"),
        (2, "alternate_window_native_owners"),
    ):
        require(
            sum(
                w["member_count"]
                for key in protocol["profiles"][index]["cores"]
                for w in core_data[key]["windows"]
            )
            == protocol["population"][field],
            "primary/alternate native-owner denominators",
        )
    scientific = {
        key: read_pin(repository, pin, cap)
        for key, pin in protocol["scientific_sources"].items()
    }
    metadata = [
        decode(line)
        for line in scientific["metadata_records"].splitlines()
        if line.strip()
    ]
    for core in protocol["cores"]:
        rows = [
            row
            for row in metadata
            if row["source_locator"] == core["metadata_source_locator"]
        ]
        require(
            len(rows) == 1
            and rows[0]["inventory_sha256"] == core["metadata_inventory_sha256"],
            "source metadata workbook row identity",
        )
        values = {row["column"]: row["raw"] for row in rows[0]["values"]}
        require(
            all(values[key] == value for key, value in core["metadata_raw"].items()),
            "literal source metadata values",
        )
        require(
            values["Country"]
            == {"SE": "Sweden", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}[
                core["country"]
            ],
            "declared source country grouping",
        )
        for key, column in (
            ("radius_m", "siteradius"),
            ("latitude", "latdd"),
            ("longitude", "londd"),
        ):
            require(
                number(core[key]) == number(float(values[column])),
                "source geometry binary64 interpretation",
            )
    documents = {
        key: json_value(raw)
        for key, raw in scientific.items()
        if key
        not in {
            "metadata_records",
            "metadata_workbook",
            "receiver_numerical_source",
            "gpm_numerical_source",
            "independent_receiver_reference",
            "dependency_lock",
        }
    }
    for saved in protocol["retained_responses"]:
        source = documents[saved["source"]]
        require(
            number(pointer(source, saved["factor_pointer"])) == number(saved["factor"])
            and number(pointer(source, saved["error_pointer"]))
            == number(saved["estimated_absolute_error"]),
            "exact retained response factor/error pointer",
        )
        if saved["source"] == "nordic_response":
            row = source[int(saved["factor_pointer"].split("/")[1])]
            for name, other in (
                ("receiver_radius_m", "receiver_radius_m"),
                ("source_inner_radius_m", "source_inner_radius_m"),
                ("outer_radius_m", "regional_extent_m"),
                ("fall_speed_m_s", "fall_speed_m_s"),
            ):
                require(
                    number(saved[name]) == number(row[other]),
                    "retained Nordic tuple identity",
                )
        else:
            index = int(saved["factor_pointer"].split("/")[2])
            row = source["cores"][index]
            taxon = int(saved["factor_pointer"].split("/")[-1])
            require(
                number(row["metadata_static_radius_m"])
                == number(saved["receiver_radius_m"])
                and number(row["fall_speed_m_s"][taxon])
                == number(saved["fall_speed_m_s"]),
                "retained Swedish receiver/taxon identity",
            )
    for role in ("swedish_transport_protocol", "nordic_transport_protocol"):
        old_transport = documents[role]
        for key in ("diffusion_coefficient", "turbulence_parameter"):
            require(
                number(old_transport[key]) == number(protocol["transport"][key]),
                "retained transport convention",
            )
        require(
            number(old_transport["regional_extent_m"])
            == number(protocol["transport"]["outer_radius_m"]),
            "retained regional extent",
        )
    for role in ("receiver_numerical_source", "gpm_numerical_source"):
        pin = protocol["scientific_sources"][role]
        nordic = documents["nordic_imports"][pin["path"]]
        require(
            nordic["sha256"] == pin["sha256"],
            "retained Nordic numerical source identity",
        )
        found: list[dict[str, Any]] = []

        def find(
            value: Any, path: str = pin["path"], matches: list[dict[str, Any]] = found
        ) -> None:
            if isinstance(value, dict):
                if value.get("relative_path") == path:
                    matches.append(value)
                for child in value.values():
                    find(child)
            elif isinstance(value, list):
                for child in value:
                    find(child)

        find(documents["swedish_imports"])
        require(
            bool(found)
            and all(
                row["sha256"] == pin["sha256"] and row["bytes"] == pin["bytes"]
                for row in found
            ),
            "retained Swedish numerical source identity",
        )
    return {
        "cores": core_data,
        "parameters": parameters,
        "documents": documents,
        "source_bodies": {
            **{("qualified_products", k): v for k, v in bodies.items()},
            **{("scientific_sources", k): v for k, v in scientific.items()},
        },
    }


def responses(
    value: dict[str, Any], protocol: dict[str, Any]
) -> dict[tuple[Decimal, Decimal], dict[str, Any]]:
    require(
        set(value) == {"schema_version", "taxa", "transport", "rows"}
        and value["schema_version"] == "nordic-physical-responses.v1"
        and value["taxa"] == protocol["taxa"]
        and value["transport"] == protocol["transport"],
        "closed response population header",
    )
    require(len(value["rows"]) == 12, "all nine retained and three current tuples")
    expected = {
        (number(r["receiver_radius_m"]), number(r["fall_speed_m_s"])): r
        for r in [*protocol["retained_responses"], *protocol["new_response_requests"]]
    }
    require(len(expected) == 12, "unique prospective response tuples")
    found, ids = {}, set()
    for row in value["rows"]:
        require(
            set(row)
            == {
                "response_id",
                "receiver_radius_m",
                "inner_radius_m",
                "outer_radius_m",
                "fall_speed_m_s",
                "transport",
                "factor",
                "estimated_absolute_error",
                "rigorous_error_bound",
                "status",
                "origin",
                "source_ref",
                "diagnostics",
                "refusal",
            },
            "response row keys",
        )
        key = (number(row["receiver_radius_m"]), number(row["fall_speed_m_s"]))
        require(
            key in expected
            and key not in found
            and type(row["response_id"]) is str
            and row["response_id"] not in ids,
            "unique expected response row",
        )
        ids.add(row["response_id"])
        require(
            row["response_id"] == response_identity(key[0], key[1], protocol),
            "response native request identity",
        )
        source = expected[key]
        require(
            number(row["inner_radius_m"]) == key[0]
            and number(row["outer_radius_m"])
            == number(protocol["transport"]["outer_radius_m"])
            and row["transport"] == protocol["transport"]
            and row["rigorous_error_bound"] is False,
            "response model/geometry identity",
        )
        if "source" in source:
            require(
                row["origin"] == "retained"
                and row["status"] == "available"
                and row["refusal"] is None
                and row["diagnostics"] is None,
                "retained coefficient disposition",
            )
            same(
                row["source_ref"],
                {
                    "pin": protocol["scientific_sources"][source["source"]],
                    "factor_pointer": source["factor_pointer"],
                    "error_pointer": source["error_pointer"],
                },
            )
            require(
                number(row["factor"]) == number(source["factor"])
                and number(row["estimated_absolute_error"])
                == number(source["estimated_absolute_error"]),
                "retained coefficient unchanged",
            )
        else:
            require(
                row["origin"] == "current" and row["source_ref"] is None,
                "new coefficient source role",
            )
            if row["status"] == "available":
                require(
                    row["refusal"] is None and type(row["diagnostics"]) is dict,
                    "new coefficient successful diagnostic",
                )
                require(
                    set(row["diagnostics"]) == {"factor", "estimated_absolute_error"},
                    "new coefficient diagnostic keys",
                )
                require(
                    number(row["diagnostics"]["factor"]) == number(row["factor"])
                    and number(row["diagnostics"]["estimated_absolute_error"])
                    == number(row["estimated_absolute_error"]),
                    "new response diagnostic correspondence",
                )
            else:
                require(
                    row["status"] == "refused"
                    and row["factor"] is None
                    and row["estimated_absolute_error"] is None
                    and type(row["refusal"]) is dict
                    and set(row["refusal"]) == {"error_type", "reason_code", "message"}
                    and all(
                        type(v) is str and bool(v) for v in row["refusal"].values()
                    ),
                    "explicit new response refusal",
                )
                if row["diagnostics"] is not None:
                    diagnostic = row["diagnostics"]
                    require(
                        type(diagnostic) is dict
                        and set(diagnostic) == {"factor", "estimated_absolute_error"}
                        and number(diagnostic["estimated_absolute_error"]) >= 0,
                        "finite refused raw response diagnostics",
                    )
                    factor = number(diagnostic["factor"])
                    require(
                        (
                            factor == 0
                            and row["refusal"]["reason_code"]
                            == "nonpositive_receiver_response"
                        )
                        or (
                            factor > 1
                            and row["refusal"]["reason_code"]
                            == "invalid_receiver_response"
                        ),
                        "raw response domain refusal is not a usable K",
                    )
        if row["status"] == "available":
            require(
                0 < number(row["factor"]) <= 1
                and number(row["estimated_absolute_error"]) >= 0,
                "positive finite conditional response/error",
            )
        found[key] = row
    return found


def kernels(
    core: dict[str, Any],
    protocol: dict[str, Any],
    table: dict[tuple[Decimal, Decimal], dict[str, Any]],
) -> tuple[list[Any], list[str]]:
    rows = [
        table[(number(core["radius_m"]), Decimal(v))]
        for v in protocol["parameters"]["fall_speed_m_s_text"]
    ]
    return [row["factor"] for row in rows], [row["response_id"] for row in rows]


def context_identity(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row["profile"],
        row["experiment"],
        row["target_core"],
        *row["window_cal_bp"],
        row["scope"],
    )


def refusal_population(rows: Any, expected: list[tuple[str, str, str]]) -> None:
    require(
        type(rows) is list and len(rows) == len(expected),
        "complete owner refusal population",
    )
    for row, key in zip(rows, expected, strict=True):
        require(
            type(row) is dict
            and set(row) == {"operation", "core", "reason_code", "message"}
            and all(type(v) is str and bool(v) for v in row.values())
            and (row["operation"], row["core"], row["reason_code"]) == key,
            "refusal operation/owner/reason identity",
        )


def forecasts(
    value: dict[str, Any],
    protocol: dict[str, Any],
    bound: dict[str, Any],
    table: dict[tuple[Decimal, Decimal], dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    required_plan = {context_identity(r): r for r in plan(protocol)}
    cores = {r["key"]: r for r in protocol["cores"]}
    ppe = [Decimal(v) for v in protocol["parameters"]["alpha_text"]]
    require(
        len(value["contexts"]) == len(required_plan), "all requested forecast contexts"
    )
    seen, result = set(), {}
    for context in value["contexts"]:
        require(
            set(context)
            == {
                "context_id",
                "identity",
                "target",
                "required_sources",
                "excluded_sources",
                "families",
            },
            "closed context fields",
        )
        identity = context["identity"]
        key = context_identity(identity)
        require(
            key in required_plan and key not in seen,
            "unique prospective context identity",
        )
        seen.add(key)
        expected = required_plan[key]
        owner = cores[expected["target_core"]]
        window = expected["window_cal_bp"]
        identifier = f"{key[0]}/{key[1]}/{key[2]}/{window[0]}-{window[1]}/{key[-1]}"
        require(
            context["context_id"] == identifier and identifier not in result,
            "canonical context identifier",
        )
        same(
            identity,
            {
                k: expected[k]
                for k in (
                    "profile",
                    "experiment",
                    "target_core",
                    "window_cal_bp",
                    "scope",
                )
            }
            | {
                "physical_family": owner["physical_family"],
                "country": owner["country"],
                "axis": protocol["taxa"],
            },
        )
        target_k, target_ids = kernels(owner, protocol, table)
        compare(
            context["target"],
            {
                "core": owner["key"],
                "site": owner["identity"]["site_id"],
                "dataset": owner["identity"]["dataset_id"],
                "collection_unit": owner["identity"]["collection_unit_id"],
                "country": owner["country"],
                "physical_family": owner["physical_family"],
                "window_cal_bp": window,
                "axis": protocol["taxa"],
                "ppe": ppe,
                "kernels": [None if k is None else number(k) for k in target_k],
                "response_ids": target_ids,
                "receiver_radius_m": number(owner["radius_m"]),
                "metadata_source_locator": owner["metadata_source_locator"],
            },
            "count-free forecast target",
        )
        same(context["excluded_sources"], expected["excluded"])
        require(
            len(context["required_sources"]) == len(expected["required"]),
            "all structural sources required",
        )
        count_support = all(
            bound["cores"][r["core"]]["windows"][protocol["windows"].index(window)][
                "status"
            ]
            == "supported"
            for r in expected["required"]
        )
        can_invert = (
            count_support
            and all(v is not None for v in target_k)
            and all(
                all(
                    v is not None for v in kernels(cores[r["core"]], protocol, table)[0]
                )
                for r in expected["required"]
            )
        )
        numerical_sources: list[dict[str, Any]] = []
        bad_windows: list[str] = []
        bad_responses: list[str] = []
        for saved, required in zip(
            context["required_sources"], expected["required"], strict=True
        ):
            core = cores[required["core"]]
            index = protocol["windows"].index(window)
            source_window = bound["cores"][core["key"]]["windows"][index]
            k, ids = kernels(core, protocol, table)
            fields = {
                "core": core["key"],
                "country": core["country"],
                "physical_family": core["physical_family"],
                "site": core["identity"]["site_id"],
                "dataset": core["identity"]["dataset_id"],
                "collection_unit": core["identity"]["collection_unit_id"],
                "window_cal_bp": window,
                "weight_exact": required["weight_exact"],
                "weight": required["weight_decimal"],
                "window_status": source_window["status"],
                "counts": source_window["panel_counts"],
                "panel_N": source_window["panel_N"],
                "sample_ids": source_window["sample_ids"],
                "source_ref": {
                    "ledger": core["key"],
                    "window_index": index,
                    "window_sha256": sha256(canonical(source_window)).hexdigest(),
                },
                "kernels": [None if v is None else number(v) for v in k],
                "response_ids": ids,
                "ppe": ppe,
            }
            require(
                set(saved) == {*fields, "inverse"}, "closed structural source fields"
            )
            compare({name: saved[name] for name in fields}, fields, "required source")
            inverse = saved["inverse"]
            require(
                set(inverse) == {"status", "preclosure", "cover", "refusal"},
                "inverse diagnostic fields",
            )
            numerical_sources.append(
                {
                    "counts": fields["counts"],
                    "coefficients": k,
                    "weight": required["weight_decimal"],
                }
            )
            if source_window["status"] != "supported" or any(v is None for v in k):
                (
                    bad_windows
                    if source_window["status"] != "supported"
                    else bad_responses
                ).append(core["key"])
            if not can_invert:
                own_refused = count_support and any(v is None for v in k)
                require(
                    inverse["status"] == ("refused" if own_refused else "not_run")
                    and inverse["cover"] is None
                    and inverse["preclosure"] is None
                    and (
                        inverse["refusal"] is None
                        if inverse["status"] == "not_run"
                        else type(inverse["refusal"]) is dict
                        and bool(inverse["refusal"])
                    ),
                    "unexecuted or refused physical inversion remains explicit",
                )
                if own_refused:
                    refusal_population(
                        [inverse["refusal"]],
                        [("source_response", core["key"], "response_unavailable")],
                    )
            else:
                computed = scalar_inverse(fields["counts"], k, ppe)
                compare(
                    inverse,
                    {"status": "computed", **computed, "refusal": None},
                    "individual inverse",
                )
        require(set(context["families"]) == set(METHODS), "both matched methods")
        unavailable = bool(bad_responses) or any(k is None for k in target_k)
        if bad_windows or unavailable:
            refused = METHODS if bad_windows else ("physical_forward",)
            for method in refused:
                family = context["families"][method]
                require(
                    set(family)
                    == {
                        "status",
                        "pollen_fraction",
                        "cover",
                        "preclosure",
                        "reason",
                        "refusals",
                    }
                    and family["status"] == "refused"
                    and family["pollen_fraction"] is None
                    and family["cover"] is None
                    and family["preclosure"] is None
                    and family["reason"]
                    == (
                        "required_training_source_unavailable"
                        if bad_windows
                        else "response_unavailable"
                    )
                    and type(family["refusals"]) is list
                    and bool(family["refusals"]),
                    "required-source or channel-response refusal",
                )
            if bad_windows:
                refusal_population(
                    context["families"][METHODS[0]]["refusals"],
                    [
                        (
                            "training_window",
                            key,
                            bound["cores"][key]["windows"][
                                protocol["windows"].index(window)
                            ]["status"],
                        )
                        for key in bad_windows
                    ],
                )
                same(
                    context["families"][METHODS[0]]["refusals"],
                    context["families"][METHODS[1]]["refusals"],
                )
            else:
                refusal_population(
                    context["families"]["physical_forward"]["refusals"],
                    [
                        ("source_response", key, "response_unavailable")
                        for key in bad_responses
                    ]
                    + (
                        [("target_response", owner["key"], "response_unavailable")]
                        if any(k is None for k in target_k)
                        else []
                    ),
                )
                compare(
                    context["families"]["direct_panel_mean"],
                    {
                        "status": "predicted",
                        "pollen_fraction": direct_prediction(numerical_sources),
                        "cover": None,
                        "preclosure": None,
                        "reason": None,
                        "refusals": [],
                    },
                    "direct independence from missing K",
                )
        else:
            computed = predict(numerical_sources, target_k, ppe)
            compare(
                context["families"],
                {
                    "physical_forward": {
                        "status": "predicted",
                        "pollen_fraction": computed["physical"],
                        "cover": computed["weighted_cover"],
                        "preclosure": computed["forward_preclosure"],
                        "reason": None,
                        "refusals": [],
                    },
                    "direct_panel_mean": {
                        "status": "predicted",
                        "pollen_fraction": computed["direct"],
                        "cover": None,
                        "preclosure": None,
                        "reason": None,
                        "refusals": [],
                    },
                },
                "two transfer equations",
            )
        result[identifier] = context
    return result


def score_population(
    value: dict[str, Any],
    protocol: dict[str, Any],
    bound: dict[str, Any],
    contexts: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    require(
        set(value) == {"schema_version", "prediction_file", "rows"}
        and value["schema_version"] == "nordic-physical-scores.v1"
        and len(value["rows"]) == 432,
        "closed complete scored disposition population",
    )
    seen = set()
    for row in value["rows"]:
        require(
            set(row)
            == {
                "context_id",
                "identity",
                "method",
                "status",
                "reason",
                "target_counts",
                "target_panel_N",
                "target_sample_ids",
                "target_owner_count",
                "target_source_ref",
                "pollen_fraction",
                "metrics",
            },
            "closed score row",
        )
        key = (row["context_id"], row["method"])
        require(
            key[0] in contexts and key[1] in METHODS and key not in seen,
            "unique requested score slot",
        )
        seen.add(key)
        context = contexts[key[0]]
        identity = context["identity"]
        same(row["identity"], identity)
        index = protocol["windows"].index(identity["window_cal_bp"])
        window = bound["cores"][identity["target_core"]]["windows"][index]
        expected = {
            "target_counts": window["panel_counts"],
            "target_panel_N": window["panel_N"],
            "target_sample_ids": window["sample_ids"],
            "target_owner_count": window["member_count"],
            "target_source_ref": {
                "ledger": identity["target_core"],
                "window_index": index,
                "window_sha256": sha256(canonical(window)).hexdigest(),
            },
        }
        same({name: row[name] for name in expected}, expected)
        family = context["families"][key[1]]
        same(row["pollen_fraction"], family["pollen_fraction"])
        if window["status"] != "supported":
            require(
                row["status"] == "unavailable_target_observation"
                and row["metrics"] is None
                and type(row["reason"]) is str
                and bool(row["reason"]),
                "missing held target is not zero",
            )
        elif family["status"] == "refused":
            require(
                row["status"] == "prediction_refused"
                and row["metrics"] is None
                and row["reason"] == family["reason"],
                "prediction refusal remains unscored",
            )
        else:
            require(
                row["status"] == "scored" and row["reason"] is None,
                "defined prediction and target scored",
            )
            compare(
                row["metrics"],
                metrics(family["pollen_fraction"], window["panel_counts"]),
                "held target losses",
            )
    return list(value["rows"])


def verify(repository: Path, protocol_path: Path, products: Path) -> dict[str, Any]:
    with localcontext() as context:
        context.prec = PRECISION
        return _verify(repository, protocol_path, products)


def _verify(repository: Path, protocol_path: Path, products: Path) -> dict[str, Any]:
    started = time.monotonic()
    repository = repository.absolute()
    ordinary(repository, directory=True)
    protocol_path = (
        protocol_path if protocol_path.is_absolute() else repository / protocol_path
    )
    products = products if products.is_absolute() else repository / products
    ordinary(protocol_path)
    ordinary(products, directory=True)
    require(
        protocol_path.is_relative_to(repository)
        and products.is_relative_to(repository / "artifacts"),
        "confined scientific input/product locations",
    )
    committed_protocol(repository, protocol_path)
    before = code_state(repository)
    protocol_raw = protocol_path.read_bytes()
    require(0 < len(protocol_raw) < 1024**2, "bounded protocol")
    protocol = decode(protocol_raw)
    bound = source_binding(repository, protocol)
    cap = protocol["limits"]["max_output_bytes"]
    ordinary(products / "result.json")
    raw_result = (products / "result.json").read_bytes()
    require(len(raw_result) <= cap, "bounded result")
    result = decode(raw_result)
    require(
        set(result)
        == {
            "schema_version",
            "status",
            "source_commit",
            "index_sha256",
            "protocol",
            "sourcepins",
            "products",
            "source_guards_passed",
            "resources",
            "scope",
            "previously_exposed_development",
            "uncertainty_evaluated",
            "scientific_or_field_admission",
        }
        and result["schema_version"] == "nordic-physical-transfer-result.v1"
        and result["status"] == "produced_awaiting_independent_verification"
        and result["source_commit"] == before["head"]
        and result["index_sha256"] == before["index_sha256"]
        and result["source_guards_passed"] is True,
        "committed producer epoch and guards",
    )
    same(
        result["sourcepins"],
        [
            protocol["upstream_protocol"],
            *protocol["qualified_products"].values(),
            *protocol["scientific_sources"].values(),
        ],
    )
    require(
        result["scope"] == protocol["claim"]
        and result["previously_exposed_development"] is True
        and result["uncertainty_evaluated"] is False
        and result["scientific_or_field_admission"] is False,
        "conditional point-transfer scope preserved",
    )
    same(
        result["protocol"],
        {
            "path": str(protocol_path.relative_to(repository)),
            "bytes": len(protocol_raw),
            "sha256": sha256(protocol_raw).hexdigest(),
        },
    )
    names = {
        "responses": "responses.json",
        "prediction_freeze": "prediction-freeze.json",
        "scores": "scores.json",
        "summary": "summary.json",
    }
    require(
        set(result["products"]) == set(names),
        "four independently bound scientific members",
    )
    require(
        {path.name for path in products.iterdir()} == {"result.json", *names.values()},
        "closed five-file product set",
    )
    bodies = {}
    for key, name in names.items():
        require(
            result["products"][key]["path"] == name, "direct owned product filename"
        )
        bodies[key] = read_pin(products, result["products"][key], cap)
    require(
        sum(len(raw) for raw in bodies.values()) + len(raw_result) <= cap,
        "aggregate scientific output bound",
    )
    account = result["resources"]
    require(
        set(account) == {"elapsed_seconds", "peak_rss_bytes", "output_bytes"}
        and 0 <= number(account["elapsed_seconds"]) <= 180
        and type(account["peak_rss_bytes"]) is int
        and 0 < account["peak_rss_bytes"] <= 768 * 1024**2
        and type(account["output_bytes"]) is int
        and account["output_bytes"] == sum(len(raw) for raw in bodies.values()),
        "producer wall/RSS/serialized-product accounting",
    )
    decoded = {key: decode(bodies[key]) for key in ("responses", "prediction_freeze")}
    freeze = decoded["prediction_freeze"]
    require(
        set(freeze)
        == {"schema_version", "source_commit", "protocol", "response_file", "contexts"}
        and freeze["schema_version"] == "nordic-physical-predictions.v1"
        and freeze["source_commit"] == before["head"],
        "closed prediction freeze",
    )
    same(freeze["protocol"], result["protocol"])
    same(freeze["response_file"], result["products"]["responses"])
    table = responses(decoded["responses"], protocol)
    contexts = forecasts(freeze, protocol, bound, table)
    # Source outcomes are interpreted only after the entire closed forecast
    # population and its serialized digest have been authenticated.
    decoded.update({key: decode(bodies[key]) for key in ("scores", "summary")})
    same(decoded["scores"]["prediction_file"], result["products"]["prediction_freeze"])
    rows = score_population(decoded["scores"], protocol, bound, contexts)
    summaries(decoded["summary"], protocol, rows)
    for (family, key), raw in bound["source_bodies"].items():
        require(
            read_pin(repository, protocol[family][key], protocol["source_max_bytes"])
            == raw,
            "source bytes unchanged across independent readback",
        )
    read_pin(repository, protocol["upstream_protocol"], protocol["source_max_bytes"])
    require(
        protocol_path.read_bytes() == protocol_raw
        and (products / "result.json").read_bytes() == raw_result
        and code_state(repository) == before,
        "all scientific source/HEAD/index unchanged",
    )
    for key, raw in bodies.items():
        require(
            read_pin(products, result["products"][key], cap) == raw,
            "closed member unchanged",
        )
    return {
        "schema_version": "nordic-physical-transfer-verification.v1",
        "status": "verified",
        "source_commit": before["head"],
        "index_sha256": before["index_sha256"],
        "source_guards_passed": True,
        "producer_result_sha256": sha256(raw_result).hexdigest(),
        "contexts_checked": len(contexts),
        "method_slots_checked": len(rows),
        "source_owners_previously_qualified": 542,
        "source_windows_bound": 42,
        "responses_conditioned_on": 12,
        "retained_response_pointers_checked": 9,
        "parameter_rows_bound": 31,
        "covariance_cells_bound": 961,
        "decimal_precision": PRECISION,
        "absolute_tolerance": "1e-12",
        "arithmetic_scope": "Authenticated parameter strings and serialized conditional response values are evaluated in Decimal80; comparison is against the declared native binary64 outputs, including unnormalized inverse values.",
        "score_status_counts": dict(Counter(row["status"] for row in rows)),
        "scope": "Independent conditional saved-response Decimal80 transfer/source/weights/score verification; separate R agreement and no field/historical/uncertainty claim.",
        "kernel_calls": 0,
        "model_calls": 0,
        "source_acquisition": False,
        "elapsed_seconds": time.monotonic() - started,
    }
