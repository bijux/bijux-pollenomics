"""Export saved Nordic cutoff factors and compare an independent scalar R reference."""

from __future__ import annotations

import argparse
from collections.abc import Callable
import csv
import hashlib
from pathlib import Path
import stat
import types
from typing import Any, Protocol, cast

PROFILE = "nordic-regional-cutoff-scalar-reference.v1"
IDS = [f"extent-tuple:{i}" for i in range(1, 47)]
PARAMETERS = (
    "receiver_radius_m",
    "inner_radius_m",
    "outer_radius_m",
    "fall_speed_m_s",
    "diffusion_coefficient",
    "turbulence_parameter",
    "wind_speed_m_s",
)
COLUMNS = (
    "tuple_id",
    "receiver_radius_m",
    "source_inner_radius_m",
    "regional_extent_m",
    "fall_speed_m_s",
    "empirical_diffusion_coefficient",
    "turbulence_parameter",
    "wind_speed_m_s",
)
OUTCOMES = (
    *COLUMNS,
    "status",
    "error_message",
    "reason_code",
    "error_class",
    "factor",
    "raw_factor",
    "estimated_absolute_error",
    "tail_mass_bound",
    "subdivisions_used",
    "warnings",
)
DETAILS = (
    "tuple_id",
    "index",
    "left",
    "right",
    "coefficient",
    "exponent",
    "boundaries",
    "total",
    "estimated_error",
    "subdivisions",
    "reason_code",
    "original_refusal_message",
    "integrate_value",
    "integrate_abs.error",
    "integrate_subdivisions",
    "integrate_message",
)
SUMMARY = (
    "requests",
    "completed",
    "refused",
    "fatal",
    "not_run",
    "scientific_admission",
    "original_absolute_tolerance",
    "original_relative_tolerance",
    "original_quadrature_limit",
    "saved_python_report_unchanged",
)
KNOWN = {
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
}
TOLERANCE = 1e-8
MAX_REPORT = 4 * 1024**2
MAX_TSV = 256 * 1024
MAX_RESULT = 512 * 1024


_SCALAR_HELPER_DOCUMENTATION: tuple[tuple[str, bytes, bytes], ...] = (
    (
        "digest",
        b"def digest(raw: bytes) -> str:\n",
        b'    """Return the exact byte digest of a declared reference input."""\n',
    ),
    (
        "identity",
        b"def identity(value: str, size: int) -> str:\n",
        b'    """Require an exact lowercase hexadecimal identity of the declared width."""\n',
    ),
    (
        "physical",
        b"def physical(path: Path) -> Path:\n",
        b'    """Require an absolute normalized path without linked ancestors."""\n',
    ),
    (
        "read",
        b"def read(\n    path: Path, limit: int, expected: str | None = None\n) -> tuple[bytes, dict[str, Any]]:\n",
        b'    """Read one bounded regular input and verify any declared byte identity."""\n',
    ),
    (
        "pairs",
        b"def pairs(rows: list[tuple[str, Any]]) -> dict[str, Any]:\n",
        b'    """Preserve JSON key order while refusing duplicate keys."""\n',
    ),
    (
        "load",
        b"def load(raw: bytes) -> Any:\n",
        b'    """Decode ordered JSON while refusing duplicate keys and nonfinite constants."""\n\n',
    ),
    (
        "number",
        b"def number(value: Any, lower: float = 0, upper: float = math.inf) -> float:\n",
        b'    """Require a finite native number within its declared domain."""\n',
    ),
    (
        "decimal",
        b"def decimal(value: str, lower: float = 0, upper: float = math.inf) -> float:\n",
        b'    """Parse one strict decimal table cell within the declared bounds."""\n',
    ),
    (
        "encoded",
        b"def encoded(value: Any) -> bytes:\n",
        b'    """Encode finite reference metadata with deterministic key order."""\n',
    ),
    (
        "table",
        b"def table(columns: tuple[str, ...], rows: list[list[Any]]) -> bytes:\n",
        b'    """Write declared tab-separated columns and ordered scalar rows."""\n',
    ),
    (
        "parse_table",
        b"def parse_table(raw: bytes, columns: tuple[str, ...]) -> list[dict[str, str]]:\n",
        b'    """Require exact table columns and consistent row widths."""\n',
    ),
    (
        "source",
        b"def source(\n    args: argparse.Namespace,\n) -> tuple[list[dict[str, Any]], dict[str, Any], bytes]:\n",
        b'    """Validate reference inputs and preserve original response tuple support."""\n',
    ),
    (
        "destination",
        b"def destination(args: argparse.Namespace) -> Path:\n",
        b'    """Require an absent output beneath the physical repository artifact root."""\n',
    ),
    (
        "export",
        b"def export(args: argparse.Namespace) -> int:\n",
        b'    """Export admitted reference tuples with their original source identities."""\n',
    ),
    (
        "compare",
        b"def compare(args: argparse.Namespace) -> int:\n",
        b'    """Compare admitted responses with exact independent numerical outputs."""\n',
    ),
    (
        "main",
        b"def main(argv: list[str] | None = None) -> int:\n",
        b'    """Dispatch the declared reference export or comparison."""\n',
    ),
)


def _scalar_helper_historical_basis(current: bytes) -> bytes:
    """Invert only the declared literal documentation at its original header."""
    if (
        len(current) == 18897
        and hashlib.sha256(current).hexdigest()
        == "af2c288baefddd267e0a481a1fb6afbaba8dd94b5150a397ce1174ff0f902b56"
    ):
        return current
    body = current
    for _, header, documentation in _SCALAR_HELPER_DOCUMENTATION:
        marked = header + documentation
        if body.count(marked) != 1:
            raise ValueError("Unknown nordic_wind.py documentation or definition")
        body = body.replace(marked, header, 1)
    if (
        len(body) != 18897
        or hashlib.sha256(body).hexdigest()
        != "af2c288baefddd267e0a481a1fb6afbaba8dd94b5150a397ce1174ff0f902b56"
    ):
        raise ValueError(
            "scalar helper nordic_wind.py differs beyond its named documentation"
        )
    return body


# Load only the authenticated current sibling; historical bytes are a comparison basis.
_HELPER = Path(__file__).absolute().with_name("nordic_wind.py")
if (
    ".." in _HELPER.parts
    or any(path.is_symlink() for path in (_HELPER, *_HELPER.parents))
    or _HELPER.resolve(strict=True) != _HELPER
):
    raise ValueError("Physical sibling scalar helper required")
_helper_info = _HELPER.lstat()
if (
    not stat.S_ISREG(_helper_info.st_mode)
    or _helper_info.st_nlink != 1
    or not 0 < _helper_info.st_size <= 128 * 1024
):
    raise ValueError("Single-link regular scalar helper required")
_helper_buffer = _HELPER.read_bytes()
if len(_helper_buffer) != _helper_info.st_size:
    raise ValueError("Sibling scalar helper changed during read")
_helper_basis = _scalar_helper_historical_basis(_helper_buffer)
_helper_after = _HELPER.lstat()
_helper_stat_fields = (
    "st_dev",
    "st_ino",
    "st_mode",
    "st_nlink",
    "st_size",
    "st_mtime_ns",
    "st_ctime_ns",
)
if (
    any(
        getattr(_helper_info, field) != getattr(_helper_after, field)
        for field in _helper_stat_fields
    )
    or any(path.is_symlink() for path in (_HELPER, *_HELPER.parents))
    or _HELPER.read_bytes() != _helper_buffer
):
    raise ValueError("Sibling scalar helper changed during correspondence")
_HELPER_EXECUTION_IDENTITY = {
    "path": str(_HELPER),
    "sha256": hashlib.sha256(_helper_buffer).hexdigest(),
    "bytes": len(_helper_buffer),
    "historical_basis": {
        "sha256": hashlib.sha256(_helper_basis).hexdigest(),
        "bytes": len(_helper_basis),
    },
    "correspondence": "exact_named_documentation"
    if _helper_buffer != _helper_basis
    else "exact_original_bytes",
}
_helper_module = types.ModuleType("nordic_scalar_helpers")
_helper_module.__file__ = str(_HELPER)
exec(compile(_helper_buffer, str(_HELPER), "exec"), _helper_module.__dict__)
_helpers = _helper_module.__dict__


class _Read(Protocol):
    def __call__(
        self, path: Path, limit: int, expected: str | None = None
    ) -> tuple[bytes, dict[str, Any]]: ...


class _Number(Protocol):
    def __call__(self, value: Any, lower: float = 0, upper: float = ...) -> float: ...


class _Decimal(Protocol):
    def __call__(self, value: str, lower: float = 0, upper: float = ...) -> float: ...


digest = cast(Callable[[bytes], str], _helpers["digest"])
identity = cast(Callable[[str, int], str], _helpers["identity"])
physical = cast(Callable[[Path], Path], _helpers["physical"])
read = cast(_Read, _helpers["read"])
pairs = cast(Callable[[list[tuple[str, Any]]], dict[str, Any]], _helpers["pairs"])
load = cast(Callable[[bytes], Any], _helpers["load"])
number = cast(_Number, _helpers["number"])
decimal = cast(_Decimal, _helpers["decimal"])
encoded = cast(Callable[[Any], bytes], _helpers["encoded"])
table = cast(Callable[[tuple[str, ...], list[list[Any]]], bytes], _helpers["table"])
parse_table = cast(
    Callable[[bytes, tuple[str, ...]], list[dict[str, str]]], _helpers["parse_table"]
)
destination = cast(Callable[[argparse.Namespace], Path], _helpers["destination"])


def source(
    args: argparse.Namespace,
) -> tuple[list[dict[str, Any]], dict[str, Any], bytes]:
    """Validate reference inputs and preserve original response tuple support."""
    raw, report_pin = read(args.report, MAX_REPORT, args.report_sha256)
    report = load(raw)
    protocol_raw, _ = read(args.protocol, 16384, args.protocol_sha256)
    protocol = load(protocol_raw)
    if (
        report["schema_version"] != "nordic-conditional-regional-extent-result.v1"
        or report["protocol"] != protocol
        or report["protocol_sha256"] != args.protocol_sha256
        or protocol["schema_version"]
        != "nordic-conditional-regional-extent-sensitivity.v1"
        or protocol["alternative_regional_extent_m"] != [50000, 200000]
        or protocol["diffusion_coefficient"] != 0.12
        or protocol["turbulence_parameter"] != 0.25
        or protocol["baseline_regional_extent_m"] != 100000
        or protocol["wind_speed_m_s"] != 3
    ):
        raise ValueError("Saved source/protocol differs")
    if protocol["source_epoch"] != report["baseline_source_epoch"]:
        raise ValueError("Protocol baseline source epoch differs")
    if any(
        type(report[k]) is not int or report[k] != v
        for k, v in {
            "unique_physical_tuple_requests": 46,
            "requested_alternative_cases": 18,
            "requested_alternative_windows": 364,
            "computed_windows": 364,
            "refused_windows": 0,
        }.items()
    ):
        raise ValueError("Complete saved computed population required")
    identity(report["execution_epoch"], 40)
    identity(report["baseline_source_epoch"], 40)
    responses = report["physical_responses"]
    if type(responses) is not list or [row["tuple_id"] for row in responses] != IDS:
        raise ValueError("Exact ordered46 stable tuple identities required")
    bindings = []
    for row in responses:
        p = row["parameters"]
        if (
            set(p) != set(PARAMETERS)
            or row["status"] != "computed"
            or row["reason"] is not None
        ):
            raise ValueError("Saved computed factor required; refusals are not zeros")
        values = {key: number(p[key]) for key in PARAMETERS}
        if not (
            0
            < values["receiver_radius_m"]
            == values["inner_radius_m"]
            < values["outer_radius_m"]
            and values["outer_radius_m"] in (50000, 200000)
            and values["fall_speed_m_s"] > 0
            and values["diffusion_coefficient"] == protocol["diffusion_coefficient"]
            and values["turbulence_parameter"] == protocol["turbulence_parameter"]
            and values["wind_speed_m_s"] == protocol["wind_speed_m_s"]
        ):
            raise ValueError("Frozen physical domain differs")
        if set(row["response"]) != {"factor", "estimated_absolute_error"}:
            raise ValueError("Saved response shape differs")
        saved = number(row["response"]["factor"], 0, 1)
        if saved == 0:
            raise ValueError("Saved physical factor must be positive")
        bindings.append(
            {
                "tuple_id": row["tuple_id"],
                "parameters": values,
                "saved_factor": saved,
                "saved_estimated_absolute_error": number(
                    row["response"]["estimated_absolute_error"]
                ),
            }
        )
    by_id = {row["tuple_id"]: row for row in bindings}
    if (
        len({tuple(row["parameters"][key] for key in PARAMETERS) for row in bindings})
        != 46
    ):
        raise ValueError("Duplicate physical request")
    if any(
        sum(row["parameters"]["outer_radius_m"] == extent for row in bindings) != 23
        for extent in (50000, 200000)
    ):
        raise ValueError("Exact twenty-three tuples per cutoff required")
    cases = report["cases"]
    if len(cases) != 18 or len({case["case_id"] for case in cases}) != 18:
        raise ValueError("Exact eighteen case identities required")
    baseline_ids = {case["baseline_case_id"] for case in cases}
    expected_cases = {
        (case_id, extent) for case_id in baseline_ids for extent in (50000, 200000)
    }
    if (
        len(baseline_ids) != 9
        or {(case["baseline_case_id"], case["regional_extent_m"]) for case in cases}
        != expected_cases
    ):
        raise ValueError("Nine matched baseline cases at both cutoffs required")
    uses = []
    for case in cases:
        context = case["original_case_context"]
        if (
            context["case_id"] != case["baseline_case_id"]
            or case["case_id"]
            != case["baseline_case_id"] + f".extent_{case['regional_extent_m']}m"
        ):
            raise ValueError("Original case identity or cutoff suffix differs")
        speeds = context["fall_speed_m_s"]
        if (
            type(case["regional_extent_m"]) is not int
            or case["regional_extent_m"] not in (50000, 200000)
            or len(speeds) != len(case["physical_tuple_ids"])
        ):
            raise ValueError("Case tuple axis differs")
        for tuple_id, speed in zip(case["physical_tuple_ids"], speeds, strict=True):
            p = by_id[tuple_id]["parameters"]
            if (
                p["receiver_radius_m"] != number(context["static_geometry"]["radius_m"])
                or p["fall_speed_m_s"] != number(speed)
                or p["outer_radius_m"] != case["regional_extent_m"]
            ):
                raise ValueError("Case-to-physical tuple binding differs")
            uses.append(tuple_id)
    if len(uses) != 58 or set(uses) != set(IDS):
        raise ValueError("Exact58case uses of46tuple requests required")
    meta = {
        "schema_version": PROFILE,
        "report": report_pin,
        "protocol_sha256": args.protocol_sha256,
        "saved_source_epoch": report["baseline_source_epoch"],
        "saved_execution_epoch": report["execution_epoch"],
        "tuple_bindings": bindings,
        "execution_helpers": {"scalar": _HELPER_EXECUTION_IDENTITY},
    }
    tsv = table(
        COLUMNS,
        [
            [row["tuple_id"], *[repr(row["parameters"][key]) for key in PARAMETERS]]
            for row in bindings
        ],
    )
    return bindings, meta, tsv


def export(args: argparse.Namespace) -> int:
    """Export admitted reference tuples with their original source identities."""
    _, meta, tsv = source(args)
    out = destination(args)
    meta.update(
        export_execution_epoch=identity(args.execution_epoch, 40),
        python_source_sha256=digest(Path(__file__).read_bytes()),
        tuples={"name": "tuples.tsv", "sha256": digest(tsv), "bytes": len(tsv)},
    )
    body = encoded(meta)
    if len(body) > 65536 or len(tsv) > 65536:
        raise ValueError("Scalar export exceeds64KiB member bound")
    read(args.report, MAX_REPORT, args.report_sha256)
    out.mkdir()
    (out / "tuples.tsv").write_bytes(tsv)
    (out / "manifest.json").write_bytes(body)
    return 0


def compare(args: argparse.Namespace) -> int:
    """Compare admitted responses with exact independent numerical outputs."""
    bindings, meta, tsv = source(args)
    out = destination(args)
    directory = physical(args.input_directory)
    if {p.name for p in directory.iterdir()} != {"tuples.tsv", "manifest.json"}:
        raise ValueError("Exact exported input membership required")
    mb, mp = read(directory / "manifest.json", 65536, args.manifest_sha256)
    actual, _ = read(directory / "tuples.tsv", 65536, digest(tsv))
    manifest = load(mb)
    expected = {
        **meta,
        "export_execution_epoch": identity(args.execution_epoch, 40),
        "python_source_sha256": digest(Path(__file__).read_bytes()),
        "tuples": {
            "name": "tuples.tsv",
            "sha256": digest(actual),
            "bytes": len(actual),
        },
    }
    if manifest != expected:
        raise ValueError("Export source, tuples or execution identity differs")
    rd = physical(args.r_directory)
    if {p.name for p in rd.iterdir()} != {
        "tuple-outcomes.tsv",
        "integration-refusals.tsv",
        "summary.tsv",
        "scope.txt",
    }:
        raise ValueError("Exact independent R output membership required")
    raw, outcomes_pin = read(rd / "tuple-outcomes.tsv", MAX_TSV)
    outcomes = parse_table(raw, OUTCOMES)
    if [row["tuple_id"] for row in outcomes] != IDS:
        raise ValueError("R tuple population/order differs")
    raw, detail_pin = read(rd / "integration-refusals.tsv", MAX_TSV)
    details = parse_table(raw, DETAILS)
    raw, summary_pin = read(rd / "summary.tsv", 8192)
    summary = parse_table(raw, SUMMARY)
    _, scope_pin = read(rd / "scope.txt", 8192)
    result = []
    fatal_seen = False
    for saved, row in zip(bindings, outcomes, strict=True):
        for column, key in zip(COLUMNS[1:], PARAMETERS, strict=True):
            if decimal(row[column]) != saved["parameters"][key]:
                raise ValueError("R physical parameter differs")
        status = row["status"]
        if (
            status
            not in {
                "completed_compensated_reference",
                "refused",
                "fatal",
                "not_run_after_fatal",
            }
            or (fatal_seen and status != "not_run_after_fatal")
            or (not fatal_seen and status == "not_run_after_fatal")
        ):
            raise ValueError("R status sequence differs")
        difference = None
        if status == "completed_compensated_reference":
            if any(row[key] for key in ("error_message", "reason_code", "error_class")):
                raise ValueError("Completed row carries refusal")
            factor = decimal(row["factor"], 0, 1)
            decimal(row["raw_factor"], -1e-11, 1 + 1e-11)
            decimal(row["estimated_absolute_error"])
            decimal(row["tail_mass_bound"], 0, 9.85967654375977e-305)
            subdivisions = decimal(row["subdivisions_used"], 0, 3000)
            if not subdivisions.is_integer():
                raise ValueError("Integral subdivision count must be integer")
            difference = abs(factor - saved["saved_factor"])
        else:
            if any(
                row[k]
                for k in (
                    "factor",
                    "raw_factor",
                    "estimated_absolute_error",
                    "tail_mass_bound",
                    "subdivisions_used",
                )
            ):
                raise ValueError("Refused/unrun row carries manufactured factor")
            if status in {"refused", "fatal"} and (
                not row["error_message"] or not row["error_class"]
            ):
                raise ValueError("Missing refusal/fatal evidence")
            if status == "refused" and (
                row["reason_code"] not in KNOWN
                or "circular_receiver_reference_error"
                not in row["error_class"].split(",")
            ):
                raise ValueError("Unknown error cannot be a typed refusal")
            fatal_seen = fatal_seen or status == "fatal"
        result.append(
            {
                "tuple_id": saved["tuple_id"],
                "saved_python_factor": saved["saved_factor"],
                "r_status": status,
                "absolute_difference": difference,
                "passed": difference is not None and difference <= TOLERANCE,
                "R_diagnostics": row,
            }
        )
    counts = {
        s: sum(row["status"] == s for row in outcomes)
        for s in (
            "completed_compensated_reference",
            "refused",
            "fatal",
            "not_run_after_fatal",
        )
    }
    if len(summary) != 1 or summary[0] != dict(
        zip(
            SUMMARY,
            map(
                str,
                (
                    46,
                    counts["completed_compensated_reference"],
                    counts["refused"],
                    counts["fatal"],
                    counts["not_run_after_fatal"],
                    "FALSE",
                    "1e-11",
                    "1e-10",
                    1000,
                    "TRUE",
                ),
            ),
            strict=True,
        )
    ):
        raise ValueError("R summary population/tolerances differ")
    ids = [row["tuple_id"] for row in details]
    allowed = {
        row["tuple_id"] for row in outcomes if row["status"] in {"refused", "fatal"}
    }
    if len(ids) != len(set(ids)) or not set(ids) <= allowed:
        raise ValueError("Foreign or duplicate refusal detail")
    passed = all(row["passed"] for row in result)
    payload = {
        "schema_version": PROFILE,
        "passed": passed,
        "report": meta["report"],
        "saved_source_epoch": meta["saved_source_epoch"],
        "saved_execution_epoch": meta["saved_execution_epoch"],
        "reference_execution_epoch": args.execution_epoch,
        "execution_helpers": {"scalar": _HELPER_EXECUTION_IDENTITY},
        "manifest": mp,
        "r_outputs": [outcomes_pin, detail_pin, summary_pin, scope_pin],
        "absolute_tolerance": TOLERANCE,
        "requests": 46,
        "completed": counts["completed_compensated_reference"],
        "refused": counts["refused"],
        "fatal": counts["fatal"],
        "not_run": counts["not_run_after_fatal"],
        "rows": result,
        "refusal_details": details,
        "scope": "Independent scalar numerical agreement only; no Python kernel/moment rerun, original-author R, empirical extent, asymptotic convergence, chronology/physical uncertainty, field accuracy or whole scientific acceptance.",
    }
    body = encoded(payload)
    if len(body) > MAX_RESULT:
        raise ValueError("Scalar comparison exceeds512KiB")
    read(args.report, MAX_REPORT, args.report_sha256)
    with out.open("xb") as stream:
        stream.write(body)
    return 0 if passed else 1


def main(argv: list[str] | None = None) -> int:
    """Dispatch the declared reference export or comparison."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("export", "compare"))
    for name in ("repository", "report", "protocol", "output_root", "output"):
        parser.add_argument("--" + name.replace("_", "-"), type=Path, required=True)
    for name in ("report-sha256", "protocol-sha256", "execution-epoch"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--input-directory", type=Path)
    parser.add_argument("--manifest-sha256")
    parser.add_argument("--r-directory", type=Path)
    args = parser.parse_args(argv)
    if args.mode == "compare" and any(
        getattr(args, key) is None
        for key in ("input_directory", "manifest_sha256", "r_directory")
    ):
        parser.error("compare requires exact exported manifest and R output directory")
    try:
        return export(args) if args.mode == "export" else compare(args)
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        OverflowError,
        csv.Error,
    ) as error:
        print(str(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
