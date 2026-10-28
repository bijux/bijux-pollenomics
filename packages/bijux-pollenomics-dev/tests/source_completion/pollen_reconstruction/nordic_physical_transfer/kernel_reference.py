"""Custody and numerical correspondence for three independently evaluated R tuples."""

from __future__ import annotations

import argparse
import csv
from decimal import Decimal, InvalidOperation
import hashlib
import io
import json
import math
from pathlib import Path
import sys
from typing import Any

MAX_BYTES = 1 << 20
MAX_INPUT_BYTES = 16 << 20
REQUEST_COLUMNS = (
    "tuple_id",
    "receiver_radius_m",
    "inner_radius_m",
    "outer_radius_m",
    "fall_speed_m_s",
    "diffusion_coefficient",
    "turbulence_parameter",
    "wind_speed_m_s",
    "absolute_tolerance",
    "relative_tolerance",
    "quadrature_limit",
)
VALUE_COLUMNS = (
    "factor",
    "raw_factor",
    "estimated_absolute_error",
    "tail_mass_bound",
    "method",
    "coefficient_from_parameters",
    "exponent",
    "absolute_tolerance",
    "relative_tolerance",
    "quadrature_limit",
    "subdivisions_used",
)
OUTCOME_COLUMNS = (
    "tuple_id",
    "status",
    *VALUE_COLUMNS,
    "error_class",
    "reason_code",
    "error_message",
    "warnings",
)
REFUSALS = frozenset(
    (
        "invalid_parameter",
        "invalid_geometry",
        "invalid_budget",
        "survival_unresolved",
        "point_unresolved",
        "geometry_transform_unresolved",
        "distance_unresolved",
        "overlap_unresolved",
        "quadrature_not_converged",
        "response_invalid",
    )
)


def _ordinary(path: Path) -> Path:
    if ".." in path.parts or any(p.is_symlink() for p in (path, *path.parents)):
        raise ValueError("Ordinary paths without parent traversal required")
    return path


def _child(root: Path, relative: str) -> Path:
    p = Path(relative)
    if p.is_absolute() or not relative or ".." in p.parts:
        raise ValueError("Relative owned path required")
    return _ordinary(root / p)


def _bytes(path: Path) -> bytes:
    _ordinary(path)
    if not path.is_file() or path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("Missing or oversized regular input")
    return path.read_bytes()


def _pin(path: Path, relative: str) -> dict[str, Any]:
    b = _bytes(path)
    return {"path": relative, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()}


def _bound(root: Path, pin: dict[str, Any]) -> bytes:
    if set(pin) != {"path", "bytes", "sha256"} or type(pin["bytes"]) is not int:
        raise ValueError("Exact byte identity required")
    p = _child(root, pin["path"])
    if _pin(p, pin["path"]) != pin:
        raise ValueError("Byte identity mismatch")
    return _bytes(p)


def _pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def _json(body: bytes) -> dict[str, Any]:
    def invalid(value: str) -> None:
        raise ValueError(f"Nonfinite JSON constant: {value}")

    def finite(value: str) -> float:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite JSON number")
        return number

    d = json.loads(
        body, object_pairs_hook=_pairs, parse_constant=invalid, parse_float=finite
    )
    if not isinstance(d, dict):
        raise ValueError("JSON object required")
    return d


def _encoded(value: Any) -> bytes:
    return (
        json.dumps(value, allow_nan=False, sort_keys=True, indent=2) + "\n"
    ).encode()


def _write(path: Path, body: bytes) -> None:
    _ordinary(path)
    if len(body) > MAX_BYTES:
        raise ValueError("Output byte ceiling")
    with path.open("xb") as stream:
        stream.write(body)


def _number(value: Any) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("Finite numeric value required")
    try:
        number = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal") from exc
    if not number.is_finite():
        raise ValueError("Nonfinite number")
    return number


def _requests(protocol: dict[str, Any]) -> list[dict[str, str]]:
    if protocol["schema_version"] != "nordic-physical-transfer-protocol.v1":
        raise ValueError("Unknown transfer protocol")
    control = protocol["independent_kernel_check"]
    required = {
        "required_new_tuple_count": 3,
        "absolute_tolerance": 1e-11,
        "relative_tolerance": 1e-10,
        "quadrature_limit": 1000,
        "factor_agreement_absolute_tolerance": 1e-8,
        "max_wall_seconds": 60,
        "max_rss_bytes": 536870912,
        "max_output_bytes": MAX_BYTES,
    }
    for key, expected in required.items():
        if type(control[key]) is not type(expected) or control[key] != expected:
            raise ValueError("Prospective R control mismatch")
    if control["reference_function"] != "circular_receiver_annulus_reference":
        raise ValueError("Unknown reference function")
    if control["source_role"] != "independent_receiver_reference":
        raise ValueError("Unknown reference authority")
    transport = protocol["transport"]
    for key, expected in (
        ("wind_speed_m_s", 3),
        ("diffusion_coefficient", 0.12),
        ("turbulence_parameter", 0.25),
        ("outer_radius_m", 100000),
    ):
        if _number(transport[key]) != _number(expected):
            raise ValueError("Transport profile mismatch")
    supplied = protocol["new_response_requests"]
    if len(supplied) != 3:
        raise ValueError("Exactly three new tuples required")
    rows = []
    for radius, raw in zip((80, 69, 89), supplied, strict=True):
        tuple_expected = {
            "receiver_radius_m": radius,
            "inner_radius_m": radius,
            "outer_radius_m": 100000,
            "fall_speed_m_s": 0.031,
        }
        if set(raw) != set(tuple_expected) or any(
            _number(raw[k]) != _number(v) for k, v in tuple_expected.items()
        ):
            raise ValueError("Ordered missing-tuple inventory mismatch")
        rows.append(
            dict(
                zip(
                    REQUEST_COLUMNS,
                    (
                        f"pinus-radius:{radius}",
                        str(radius),
                        str(radius),
                        "100000",
                        ".031",
                        ".12",
                        ".25",
                        "3",
                        "1e-11",
                        "1e-10",
                        "1000",
                    ),
                    strict=True,
                )
            )
        )
    return rows


def _tsv(columns: tuple[str, ...], rows: list[dict[str, str]]) -> bytes:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream, fieldnames=columns, delimiter="\t", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue().encode()


def _table(body: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:
    reader = csv.DictReader(io.StringIO(body.decode(), newline=""), delimiter="\t")
    if reader.fieldnames != list(columns):
        raise ValueError("Exact TSV header required")
    rows = list(reader)
    if any(set(r) != set(columns) or any(v is None for v in r.values()) for r in rows):
        raise ValueError("Incomplete TSV record")
    return rows


def prepare(
    repository: Path, protocol: Path, products: Path, output: Path
) -> dict[str, Any]:
    """Close the exact requests and all consumed source/product byte identities."""
    repository, products, output = map(_ordinary, (repository, products, output))
    protocol_pin = _pin(protocol, str(protocol.relative_to(repository)))
    contract = _json(_bytes(protocol))
    requests = _requests(contract)
    reference = contract["scientific_sources"]["independent_receiver_reference"]
    _bound(repository, reference)
    result_pin = _pin(products / "result.json", "result.json")
    result = _json(_bytes(products / "result.json"))
    response_pin = result["products"]["responses"]
    responses = _json(_bound(products, response_pin))
    if responses["transport"] != contract["transport"]:
        raise ValueError("Producer transport differs from protocol")
    freeze_pin = result["products"]["prediction_freeze"]
    freeze = _json(_bound(products, freeze_pin))
    if freeze["response_file"] != response_pin:
        raise ValueError("Closed prediction response binding differs")
    if responses["schema_version"] != "nordic-physical-responses.v1":
        raise ValueError("Unknown response schema")
    wrapper = Path(__file__).with_suffix(".R")
    code_pins = [
        _pin(p, str(p.relative_to(repository))) for p in (Path(__file__), wrapper)
    ]
    manifest = {
        "schema_version": "nordic-physical-kernel-reference-inputs.v1",
        "protocol": protocol_pin,
        "reference": reference,
        "checker_sources": code_pins,
        "producer_result": result_pin,
        "responses": response_pin,
        "prediction_freeze": freeze_pin,
        "source_commit": result["source_commit"],
        "requests": requests,
        "python_version": sys.version,
    }
    output.mkdir(parents=False, exist_ok=False)
    _write(output / "requests.tsv", _tsv(REQUEST_COLUMNS, requests))
    manifest["request_file"] = _pin(output / "requests.tsv", "requests.tsv")
    _write(output / "manifest.json", _encoded(manifest))
    return manifest


def audit_outcomes(
    requests: list[dict[str, str]],
    rows: list[dict[str, str]],
    responses: dict[str, Any],
) -> dict[str, Any]:
    """Check correspondence without substituting refused or clipped reference values."""
    if responses["taxa"] != ["Betula", "Pinus"] or len(responses["rows"]) != 12:
        raise ValueError("Complete twelve-tuple producer response inventory required")
    keys = ("receiver_radius_m", "inner_radius_m", "outer_radius_m", "fall_speed_m_s")
    native: dict[tuple[Decimal, ...], dict[str, Any]] = {}
    for row in responses["rows"]:
        key = tuple(_number(row[k]) for k in keys)
        if key in native:
            raise ValueError("Duplicate producer tuple")
        native[key] = row
    expected_keys = {
        (Decimal(r), Decimal(r), Decimal(100000), f)
        for r in (98, 80, 69, 89, 285, 160)
        for f in (Decimal(".024"), Decimal(".031"))
    }
    if set(native) != expected_keys:
        raise ValueError("Foreign or missing producer tuple")
    if len(rows) != 3 or [r["tuple_id"] for r in rows] != [
        r["tuple_id"] for r in requests
    ]:
        raise ValueError("Missing, foreign, duplicate or reordered R outcome")
    checks = []
    for request, row in zip(requests, rows, strict=True):
        key = tuple(_number(request[k]) for k in keys)
        production = native[key]
        if production["transport"] != responses["transport"]:
            raise ValueError("Current tuple transport differs from response profile")
        for field in ("wind_speed_m_s", "turbulence_parameter"):
            if _number(production["transport"][field]) != _number(request[field]):
                raise ValueError("R and producer transport differ")
        if _number(production["transport"]["diffusion_coefficient"]) != _number(
            request["diffusion_coefficient"]
        ):
            raise ValueError("R and producer diffusion differ")
        if (
            production["origin"] != "current"
            or production["rigorous_error_bound"] is not False
        ):
            raise ValueError("New current nonrigorous response required")
        result: dict[str, Any] = {
            "tuple_id": request["tuple_id"],
            "reference": row,
            "producer_response": production,
        }
        if production["status"] == "available":
            if (
                not 0 <= _number(production["factor"]) <= 1
                or _number(production["estimated_absolute_error"]) < 0
                or production["refusal"] is not None
            ):
                raise ValueError("Invalid available producer response")
        elif production["status"] == "refused":
            if (
                not production["refusal"]
                or production["factor"] is not None
                or production["estimated_absolute_error"] is not None
            ):
                raise ValueError("Refused producer response must not invent factor")
        else:
            raise ValueError("Unknown producer response status")
        if row["status"] != "completed":
            if any(row[k] for k in VALUE_COLUMNS) or not row["error_message"]:
                raise ValueError(
                    "Refusal must preserve evidence without invented numbers"
                )
            if row["status"] == "refused":
                if row["reason_code"] not in REFUSALS or (
                    "circular_receiver_reference_error"
                    not in row["error_class"].split(",")
                ):
                    raise ValueError(
                        "Unknown refusal cannot be typed reference refusal"
                    )
            elif row["status"] != "fatal" or not row["error_class"]:
                raise ValueError("Unknown outcome status")
            result["agreement"] = False
        else:
            if any(row[k] for k in ("error_class", "reason_code", "error_message")):
                raise ValueError("Completed row carries refusal")
            values = {k: _number(row[k]) for k in VALUE_COLUMNS if k != "method"}
            if row["method"] != "displacement_circle_overlap_one_dimensional":
                raise ValueError("Unexpected reference method")
            if not -Decimal("1e-11") <= values["raw_factor"] <= 1 + Decimal("1e-11"):
                raise ValueError("Raw factor outside admitted reference domain")
            if values["factor"] != min(
                Decimal(1), max(Decimal(0), values["raw_factor"])
            ):
                raise ValueError("Clipped and raw factors disagree")
            if (
                not values["estimated_absolute_error"] >= 0
                or not 0 <= values["tail_mass_bound"] <= 1
            ):
                raise ValueError("Negative error or invalid tail")
            if values["coefficient_from_parameters"] <= 0 or values[
                "exponent"
            ] != Decimal(".125"):
                raise ValueError("Invalid reference survival diagnostics")
            for field in (
                "absolute_tolerance",
                "relative_tolerance",
                "quadrature_limit",
            ):
                if values[field] != _number(request[field]):
                    raise ValueError("Changed reference integration control")
            subdivisions = values["subdivisions_used"]
            if (
                subdivisions != subdivisions.to_integral_value()
                or not 1 <= subdivisions <= 3000
            ):
                raise ValueError("Invalid subdivision accounting")
            if production["status"] == "available":
                factor = _number(production["factor"])
                error = _number(production["estimated_absolute_error"])
                if (
                    not 0 <= factor <= 1
                    or error < 0
                    or production["refusal"] is not None
                ):
                    raise ValueError("Invalid available producer response")
                difference = abs(values["factor"] - factor)
                result.update(
                    absolute_difference_exact=str(difference),
                    agreement=difference <= Decimal("1e-8"),
                )
            elif production["status"] == "refused" and production["refusal"]:
                if (
                    production["factor"] is not None
                    or production["estimated_absolute_error"] is not None
                ):
                    raise ValueError("Refused producer response must not invent factor")
                result["agreement"] = False
            else:
                raise ValueError("Unknown producer response status")
        checks.append(result)
    return {
        "status": "passed"
        if all(c["agreement"] for c in checks)
        else "refuse_unresolved",
        "requests": 3,
        "checks": checks,
        "absolute_agreement_tolerance": "1e-8",
        "rigorous_integral_certification": False,
        "scientific_or_field_admission": False,
        "arithmetic_scope": "R direct parameter A versus Python -log(rounded one-metre survival)",
    }


def check(
    repository: Path, protocol: Path, products: Path, output: Path, execution: Path
) -> dict[str, Any]:
    """Authenticate closed artifacts before and after numerical receipt inspection."""
    manifest_pin = _pin(output / "manifest.json", "manifest.json")
    manifest = _json(_bytes(output / "manifest.json"))
    if manifest["schema_version"] != "nordic-physical-kernel-reference-inputs.v1":
        raise ValueError("Unknown checker manifest")
    if _pin(protocol, str(protocol.relative_to(repository))) != manifest["protocol"]:
        raise ValueError("Protocol changed")
    contract = _json(_bound(repository, manifest["protocol"]))
    if (
        manifest["reference"]
        != contract["scientific_sources"]["independent_receiver_reference"]
    ):
        raise ValueError("Reference provenance changed")
    requests = _requests(contract)
    if requests != manifest["requests"] or _bound(
        output, manifest["request_file"]
    ) != _tsv(REQUEST_COLUMNS, requests):
        raise ValueError("Requests changed")
    repo_pins = [
        manifest["protocol"],
        manifest["reference"],
        *manifest["checker_sources"],
    ]
    expected_sources = [
        _pin(p, str(p.relative_to(repository)))
        for p in (Path(__file__), Path(__file__).with_suffix(".R"))
    ]
    if manifest["checker_sources"] != expected_sources:
        raise ValueError("Foreign checker source identities")
    product_pins = [
        manifest[k] for k in ("producer_result", "responses", "prediction_freeze")
    ]
    for pin in repo_pins:
        _bound(repository, pin)
    for pin in product_pins:
        _bound(products, pin)
    native = _json(_bound(products, manifest["producer_result"]))
    freeze = _json(_bound(products, manifest["prediction_freeze"]))
    responses = _json(_bound(products, manifest["responses"]))
    if responses["transport"] != contract["transport"]:
        raise ValueError("Producer transport differs from protocol")
    if (
        native["source_commit"] != manifest["source_commit"]
        or native["products"]["responses"] != manifest["responses"]
        or freeze["response_file"] != manifest["responses"]
    ):
        raise ValueError("Producer closure changed")
    rdir = _child(output, "r-reference")
    if sorted(p.name for p in rdir.iterdir()) != ["outcomes.tsv", "runtime.tsv"]:
        raise ValueError("Exact R artifact inventory required")
    if sum(_ordinary(p).stat().st_size for p in rdir.iterdir()) > MAX_BYTES:
        raise ValueError("Aggregate reference artifact byte ceiling")
    output_pins = [
        _pin(rdir / name, f"r-reference/{name}")
        for name in ("outcomes.tsv", "runtime.tsv")
    ]
    runtime = _table(
        _bytes(rdir / "runtime.tsv"),
        ("r_version", "platform", "stats_version", "base_version"),
    )
    if len(runtime) != 1 or any(not v for v in runtime[0].values()):
        raise ValueError("R runtime identity required")
    execution_pin = _pin(execution, str(execution))
    resource = _json(_bytes(execution))
    if set(resource) != {"exit_code", "wall_seconds", "peak_rss_bytes", "command"}:
        raise ValueError("Exact execution receipt required")
    if (
        type(resource["exit_code"]) is not int
        or resource["exit_code"] != 0
        or type(resource["peak_rss_bytes"]) is not int
    ):
        raise ValueError("Successful bounded R execution receipt required")
    if (
        not 0 <= _number(resource["wall_seconds"]) <= 60
        or not 0 < resource["peak_rss_bytes"] <= 536870912
    ):
        raise ValueError("R execution exceeded prospective resources")
    expected_command = [
        str(repository / manifest["checker_sources"][1]["path"]),
        str(repository / manifest["reference"]["path"]),
        str(output / "requests.tsv"),
        str(rdir),
    ]
    command = resource["command"]
    if (
        not isinstance(command, list)
        or len(command) < 5
        or command[-4:] != expected_command
        or not all(isinstance(v, str) and v for v in command)
    ):
        raise ValueError("Actual R command does not bind this wrapper and requests")
    if (
        not Path(command[0]).is_absolute()
        or Path(command[0]).name != "Rscript"
        or command[1:-4] not in ([], ["--vanilla"])
    ):
        raise ValueError("Explicit Rscript executable and controlled flags required")
    executable = Path(command[0]).resolve(strict=True)
    executable_pin = _pin(executable, str(executable))
    result = audit_outcomes(
        requests, _table(_bytes(rdir / "outcomes.tsv"), OUTCOME_COLUMNS), responses
    )
    result.update(
        schema_version="nordic-physical-kernel-reference-verification.v1",
        manifest=manifest_pin,
        protocol=manifest["protocol"],
        producer_result=manifest["producer_result"],
        responses=manifest["responses"],
        checker_sources=manifest["checker_sources"],
        reference=manifest["reference"],
        source_commit=manifest["source_commit"],
        runtime=runtime[0],
        execution={"identity": execution_pin, "facts": resource},
        rscript_executable=executable_pin,
        r_products=output_pins,
    )
    for pin in repo_pins:
        _bound(repository, pin)
    for pin in product_pins:
        _bound(products, pin)
    for pin in output_pins:
        _bound(output, pin)
    if (
        _pin(output / "manifest.json", "manifest.json") != manifest_pin
        or _pin(execution, str(execution)) != execution_pin
    ):
        raise ValueError("Checker receipt changed during inspection")
    if _pin(executable, str(executable)) != executable_pin:
        raise ValueError("Rscript executable changed during inspection")
    body = _encoded(result)
    paths = list(output.rglob("*"))
    if (
        any(p.is_symlink() for p in paths)
        or sum(p.stat().st_size for p in paths if p.is_file()) + len(body) > MAX_BYTES
    ):
        raise ValueError("Aggregate reference artifact byte ceiling")
    _write(output / "verification.json", body)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=("prepare", "check"))
    for name in ("repository", "protocol", "products", "output"):
        parser.add_argument(f"--{name}", type=Path, required=True)
    parser.add_argument("--execution", type=Path)
    args = parser.parse_args(argv)
    common = (
        args.repository.absolute(),
        args.protocol.absolute(),
        args.products.absolute(),
        args.output.absolute(),
    )
    if args.operation == "prepare":
        prepare(*common)
        return 0
    if args.execution is None:
        parser.error("check requires --execution")
    return 0 if check(*common, args.execution.absolute())["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
