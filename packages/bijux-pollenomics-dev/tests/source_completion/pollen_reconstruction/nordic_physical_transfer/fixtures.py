"""Small synthetic qualified sources and injected point operators, never old models."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from bijux_pollenomics_dev.essd_reproduction.physical_forward.prediction import Target


def protocol() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[6]
    return cast(
        dict[str, Any],
        json.loads(
            (
                repository
                / "reports/science/pollen-reconstruction/nordic-physical-transfer/protocol.json"
            ).read_bytes()
        ),
    )


def synthetic_response(**kwargs: Any) -> SimpleNamespace:
    return SimpleNamespace(
        factor=0.1 + kwargs["receiver_radius_m"] / 1000, estimated_absolute_error=1e-12
    )


def inverse_callback(
    vector: tuple[int, int],
    kernels: tuple[float, ...],
    ppe: tuple[float, ...],
    covariance: tuple[tuple[float, ...], ...],
) -> tuple[float, ...]:
    assert len(covariance) == 2 and covariance[0][0] == float("0.092006056")
    values = [vector[i] / (kernels[i] * ppe[i]) for i in range(2)]
    return tuple(v / math.fsum(values) for v in values)


def forward_callback(target: Target, cover: tuple[float, ...]) -> tuple[float, ...]:
    values = [target.kernels[i] * (cover[i] * target.ppe[i]) for i in range(2)]
    return tuple(v / math.fsum(values) for v in values)


def packet_fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    profile = protocol()
    cores = {}
    members_by_core = (
        [5] * 6,
        [5] * 6,
        [5] * 6,
        [6, 5, 5, 5, 5, 0],
        [4] * 6,
        [5, 5, 5, 5, 5, 4],
        [2] * 6,
    )
    for i, (core, member_counts) in enumerate(
        zip(profile["cores"], members_by_core, strict=True)
    ):
        windows = []
        offset = 0
        for edges, members in zip(profile["windows"], member_counts, strict=True):
            vector = [members * (i + 2), members * (9 - i)] if members else None
            panel_n = sum(vector) if vector else None
            windows.append(
                {
                    "window": edges,
                    "sample_ids": list(
                        range(
                            100000 * (i + 1) + offset,
                            100000 * (i + 1) + offset + members,
                        )
                    ),
                    "member_count": members,
                    "unassignable_source_sample_ids": [],
                    "status": "supported" if members else "empty_window",
                    "panel_counts": vector,
                    "panel_N": panel_n,
                    "pollen_N": panel_n + members * 3 if panel_n is not None else None,
                    "excluded_pollen_N": members * 3 if members else None,
                }
            )
            offset += members
        cores[core["key"]] = {"declaration": deepcopy(core), "windows": windows}
    packet = {
        "cores": cores,
        "ppe": tuple(float(v) for v in profile["parameters"]["alpha_text"]),
        "covariance": tuple(
            tuple(float(v) for v in row)
            for row in profile["parameters"]["covariance_text"]
        ),
        "sourcepins": [],
        "scientific_documents": {},
    }
    response_rows = []
    for origin, specs in (
        ("retained", profile["retained_responses"]),
        ("current", profile["new_response_requests"]),
    ):
        for spec in specs:
            transport = profile["transport"]
            request = {
                k: float(spec[k])
                for k in ("receiver_radius_m", "outer_radius_m", "fall_speed_m_s")
            }
            request["inner_radius_m"] = float(
                spec.get("inner_radius_m", spec.get("source_inner_radius_m"))
            )
            request.update(
                {
                    k: float(transport[k])
                    for k in (
                        "wind_speed_m_s",
                        "diffusion_coefficient",
                        "turbulence_parameter",
                    )
                }
            )
            request.update(
                absolute_tolerance=float(transport["python_absolute_tolerance"]),
                relative_tolerance=float(transport["python_relative_tolerance"]),
                quadrature_limit=transport["python_quadrature_limit"],
            )
            checksum = hashlib.sha256(
                json.dumps(
                    request, sort_keys=True, ensure_ascii=True, separators=(",", ":")
                ).encode()
            ).hexdigest()
            current = synthetic_response(**request)
            factor = spec["factor"] if origin == "retained" else current.factor
            error = (
                spec["estimated_absolute_error"]
                if origin == "retained"
                else current.estimated_absolute_error
            )
            response_rows.append(
                {
                    "response_id": "response:" + checksum,
                    **{
                        k: request[k]
                        for k in (
                            "receiver_radius_m",
                            "inner_radius_m",
                            "outer_radius_m",
                            "fall_speed_m_s",
                        )
                    },
                    "transport": deepcopy(transport),
                    "factor": factor,
                    "estimated_absolute_error": error,
                    "rigorous_error_bound": False,
                    "status": "available",
                    "origin": origin,
                    "source_ref": {
                        "pin": profile["scientific_sources"][spec["source"]],
                        "factor_pointer": spec["factor_pointer"],
                        "error_pointer": spec["error_pointer"],
                    }
                    if origin == "retained"
                    else None,
                    "diagnostics": {"factor": factor, "estimated_absolute_error": error}
                    if origin == "current"
                    else None,
                    "refusal": None,
                }
            )
    responses = {
        "schema_version": "nordic-physical-responses.v1",
        "taxa": profile["taxa"],
        "transport": profile["transport"],
        "rows": response_rows,
    }
    return packet, profile, responses


def write_pin(
    repository: Path, relative: str, value: Any, *, raw: bool = False
) -> dict[str, Any]:
    body = value if raw else json.dumps(value, allow_nan=False).encode()
    path = repository / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)
    return {
        "path": relative,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def saved_inputs(repository: Path) -> tuple[dict[str, Any], Path]:
    packet, profile, _ = packet_fixture()
    author_pins = {
        key: {
            "path": "synthetic-author/" + key,
            "bytes": 1,
            "sha256": hashlib.sha256(key.encode()).hexdigest(),
        }
        for key in ("lookup", "mean", "covariance", "driver")
    }
    upstream = {
        "parameters": deepcopy(profile["parameters"]),
        "author_sources": author_pins,
        "cores": [
            {
                **{
                    k: deepcopy(c[k])
                    for k in ("key", "identity", "chronology", "physical_family")
                },
                "country": {
                    "SE": "Sweden",
                    "DK": "Denmark",
                    "FI": "Finland",
                    "NO": "Norway",
                }[c["country"]],
            }
            for c in profile["cores"]
        ],
    }
    profile["upstream_protocol"] = write_pin(
        repository, profile["upstream_protocol"]["path"], upstream
    )
    objects = {}
    countries = {"SE": "Sweden", "DK": "Denmark", "FI": "Finland", "NO": "Norway"}
    for i, core in enumerate(profile["cores"]):
        objects[core["key"]] = {
            "schema_version": "nordic-author-core-support.v1",
            "key": core["key"],
            "identity": core["identity"],
            "physical_family": core["physical_family"],
            "country": countries[core["country"]],
            "taxon_axis": profile["taxa"],
            "chronology": {"selected_chronology_id": core["chronology"]["selected_id"]},
            "samples": [
                {
                    "sample_id": 100000 * (i + 1) + j,
                    "window": next(
                        (
                            w["window"]
                            for w in packet["cores"][core["key"]]["windows"]
                            if 100000 * (i + 1) + j in w["sample_ids"]
                        ),
                        None,
                    ),
                    "panel_counts": [i + 2, 9 - i],
                }
                for j in range(core["identity"]["source_sample_count"])
            ],
            "windows": packet["cores"][core["key"]]["windows"],
        }
    names = [f"Synthetic author {i}" for i in range(31)]
    names[4] = "Betula"
    names[20] = "Pinus"
    selected = {
        "taxa": profile["parameters"]["targets"],
        **{
            k: profile["parameters"][k]
            for k in (
                "alpha_text",
                "fall_speed_m_s_text",
                "covariance_text",
                "literal_file_line_numbers",
            )
        },
    }
    means = [{"A.series": name, "alpha": "1", "vg": "0.1"} for name in names]
    means[4].update(alpha="5.10571", vg="0.024")
    means[20].update(alpha="6.05833", vg="0.031")
    covariance = [
        {
            "A.series": name,
            **{other: "1" if i == j else "0" for j, other in enumerate(names)},
        }
        for i, name in enumerate(names)
    ]
    covariance[4]["Betula"] = "0.092006056"
    covariance[20]["Pinus"] = "0.056016002"
    objects["parameters"] = {
        "schema_version": "nordic-author-parameters.v1",
        "axis": names,
        "selected": selected,
        "mean_rows": means,
        "covariance_rows": covariance,
        "source_pins": author_pins,
        "lookup": {
            "rows": 10788,
            "unique_source_names": 9731,
            "parameter_targets": 31,
            "excluded_targets": ["zz.do not use", "aage.cal.BP"],
        },
    }
    objects["input_manifest"] = {
        "protocol": profile["upstream_protocol"],
        "source_commit": profile["upstream_source_commit"],
    }
    outputpins = {}
    for key, value in objects.items():
        name = profile["qualified_products"][key]["path"]
        pin = write_pin(repository, name, value)
        profile["qualified_products"][key] = pin
        outputpins[key] = {**pin, "path": Path(name).name}
    result = {
        "source_commit": profile["upstream_source_commit"],
        "source_guards_passed": True,
        "products": outputpins,
        "protocol": profile["upstream_protocol"],
    }
    profile["qualified_products"]["result"] = write_pin(
        repository, profile["qualified_products"]["result"]["path"], result
    )
    verification = {
        "schema_version": "nordic-author-window-independent-check.v1",
        "status": "verified",
        "source_commit": profile["upstream_source_commit"],
        "source_guards_passed": True,
        "producer_result_sha256": profile["qualified_products"]["result"]["sha256"],
        "native_sample_owners_checked": 542,
        "requested_windows_checked": 42,
        "physical_sites": 6,
        "countries": 4,
        "window_status_counts": {"supported": 41, "empty_window": 1},
    }
    profile["qualified_products"]["verification"] = write_pin(
        repository, profile["qualified_products"]["verification"]["path"], verification
    )
    science: dict[str, Any] = {}
    for role in (
        "receiver_numerical_source",
        "gpm_numerical_source",
        "independent_receiver_reference",
        "dependency_lock",
        "metadata_workbook",
    ):
        profile["scientific_sources"][role] = write_pin(
            repository,
            profile["scientific_sources"][role]["path"],
            ("synthetic " + role).encode(),
            raw=True,
        )
    records = {}
    for core in profile["cores"]:
        records[core["metadata_source_locator"]] = {
            "schema_version": "essd-study-metadata-record.v1",
            "source_locator": core["metadata_source_locator"],
            "inventory_sha256": core["metadata_inventory_sha256"],
            "values": [
                {"column": k, "raw": v} for k, v in core["metadata_raw"].items()
            ],
        }
    profile["scientific_sources"]["metadata_records"] = write_pin(
        repository,
        profile["scientific_sources"]["metadata_records"]["path"],
        b"\n".join(json.dumps(r).encode() for r in records.values()),
        raw=True,
    )
    swedish: dict[str, Any] = {"cores": []}
    for core in profile["cores"][:3]:
        swedish["cores"].append(
            {
                "native_site_id": core["identity"]["site_id"],
                "metadata_static_radius_m": core["radius_m"],
                "fall_speed_m_s": [0.024, 0.031],
                "quadrature": [
                    {
                        "profile": "metadata_radius_wind_3",
                        "factors": [[0.1, 0.1]],
                        "estimated_absolute_error": [1e-12, 1e-12],
                        "rigorous_error_bound": False,
                    }
                ],
            }
        )
    nordic: list[dict[str, Any]] = [{} for _ in range(23)]
    for spec in profile["retained_responses"]:
        if spec["source"] == "swedish_response":
            tokens = spec["factor_pointer"].split("/")
            i, j = int(tokens[2]), int(tokens[-1])
            swedish["cores"][i]["quadrature"][0]["factors"][0][j] = spec["factor"]
            swedish["cores"][i]["quadrature"][0]["estimated_absolute_error"][j] = spec[
                "estimated_absolute_error"
            ]
        else:
            i = int(spec["factor_pointer"].split("/")[1])
            nordic[i] = {
                "receiver_radius_m": spec["receiver_radius_m"],
                "source_inner_radius_m": spec["source_inner_radius_m"],
                "regional_extent_m": spec["outer_radius_m"],
                "fall_speed_m_s": spec["fall_speed_m_s"],
                "wind_speed_m_s": 3,
                "empirical_diffusion_coefficient": 0.12,
                "turbulence_parameter": 0.25,
                "factor": spec["factor"],
                "estimated_absolute_error": spec["estimated_absolute_error"],
            }
    originpins = [
        profile["scientific_sources"][key]
        for key in ("receiver_numerical_source", "gpm_numerical_source")
    ]
    science.update(
        swedish_response=swedish,
        nordic_response=nordic,
        nordic_original_report={"scope": "synthetic old source receipt"},
        swedish_imports={
            "module_origins": [
                {
                    "relative_path": pin["path"],
                    "sha256": pin["sha256"],
                    "bytes": pin["bytes"],
                }
                for pin in originpins
            ]
        },
        nordic_imports={
            pin["path"]: {"sha256": pin["sha256"], "module_names": ["synthetic"]}
            for pin in originpins
        },
        swedish_independent_response={"scope": "synthetic old numerical qualification"},
        nordic_independent_response={"scope": "synthetic old numerical qualification"},
        swedish_transport_protocol={
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "regional_extent_m": 100000,
            "profiles": [
                {
                    "id": "metadata_radius_wind_3",
                    "radius_multiplier": 1,
                    "wind_speed_m_s": 3,
                }
            ],
        },
        nordic_transport_protocol={
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "regional_extent_m": 100000,
            "wind_speed_m_s": 3,
        },
    )
    for key, value in science.items():
        profile["scientific_sources"][key] = write_pin(
            repository, profile["scientific_sources"][key]["path"], value
        )
    path = repository / "protocol.json"
    path.write_text(json.dumps(profile))
    return profile, path
