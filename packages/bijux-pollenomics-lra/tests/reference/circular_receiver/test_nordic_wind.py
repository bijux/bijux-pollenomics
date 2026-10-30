"""Complete artificial scalar handoff controls; no R or scientific inputs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
from typing import Any

import pytest

SOURCE = Path(__file__).with_name("nordic_wind.py").absolute()
API = runpy.run_path(str(SOURCE))

pytestmark = pytest.mark.reference


def fixture(directory: Path) -> dict[str, Any]:
    repository = directory / "repository"
    output_root = repository / "artifacts"
    output_root.mkdir(parents=True)
    protocol = {
        "alternative_wind_speed_m_s": [2, 4],
        "regional_extent_m": 100000,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
    }
    responses: list[dict[str, Any]] = []
    for wind in (2, 4):
        for i in range(23):
            responses.append(
                {
                    "tuple_id": f"wind-tuple:{len(responses) + 1}",
                    "parameters": {
                        "receiver_radius_m": 1,
                        "inner_radius_m": 1,
                        "outer_radius_m": 100000,
                        "fall_speed_m_s": 0.02 + i * 0.001,
                        "diffusion_coefficient": 0.12,
                        "turbulence_parameter": 0.25,
                        "wind_speed_m_s": wind,
                    },
                    "status": "computed",
                    "reason": None,
                    "response": {"factor": 0.5, "estimated_absolute_error": 0},
                }
            )
    groups = [list(range(i, i + 3)) for i in range(0, 21, 3)] + [
        [21, 22, 0, 1],
        [2, 3, 4, 5],
    ]
    cases = []
    for wind, offset in ((2, 0), (4, 23)):
        for group, ids in enumerate(groups):
            rows = [responses[index + offset] for index in ids]
            cases.append(
                {
                    "case_id": f"artificial-{group}.wind-{wind}",
                    "wind_speed_m_s": wind,
                    "physical_tuple_ids": [row["tuple_id"] for row in rows],
                    "original_case_context": {
                        "static_geometry": {"radius_m": 1},
                        "fall_speed_m_s": [
                            row["parameters"]["fall_speed_m_s"] for row in rows
                        ],
                    },
                }
            )
    pb = API["encoded"](protocol)
    pp = output_root / "artificial-protocol.json"
    pp.write_bytes(pb)
    report = {
        "schema_version": "nordic-conditional-wind-sensitivity-result.v1",
        "protocol": protocol,
        "protocol_sha256": hashlib.sha256(pb).hexdigest(),
        "unique_physical_tuple_requests": 46,
        "requested_alternative_cases": 18,
        "requested_alternative_windows": 364,
        "computed_windows": 364,
        "refused_windows": 0,
        "execution_epoch": "2" * 40,
        "baseline_source_epoch": "1" * 40,
        "physical_responses": responses,
        "cases": cases,
    }
    rp = output_root / "artificial-report.json"
    rp.write_bytes(API["encoded"](report))
    return {
        "repository": repository,
        "output_root": output_root,
        "protocol_path": pp,
        "report_path": rp,
        "report": report,
    }


def arguments(f: dict[str, Any], mode: str, output: Path) -> list[str]:
    rp = f["report_path"]
    pp = f["protocol_path"]
    return [
        mode,
        "--repository",
        str(f["repository"]),
        "--report",
        str(rp),
        "--report-sha256",
        hashlib.sha256(rp.read_bytes()).hexdigest(),
        "--protocol",
        str(pp),
        "--protocol-sha256",
        hashlib.sha256(pp.read_bytes()).hexdigest(),
        "--execution-epoch",
        "3" * 40,
        "--output-root",
        str(f["output_root"]),
        "--output",
        str(output),
    ]


def create_r(f: dict[str, Any], r: Path) -> None:
    r.mkdir()
    report = f["report"]
    rows = []
    for response in report["physical_responses"]:
        values = [
            response["tuple_id"],
            *[repr(float(response["parameters"][key])) for key in API["PARAMETERS"]],
        ]
        rows.append(
            values
            + [
                "completed_compensated_reference",
                "",
                "",
                "",
                ".5",
                ".5",
                "0",
                "0",
                "3",
                "",
            ]
        )
    (r / "tuple-outcomes.tsv").write_bytes(API["table"](API["OUTCOMES"], rows))
    (r / "integration-refusals.tsv").write_bytes(API["table"](API["DETAILS"], []))
    (r / "summary.tsv").write_bytes(
        API["table"](
            API["SUMMARY"], [[46, 46, 0, 0, 0, "FALSE", "1e-11", "1e-10", 1000, "TRUE"]]
        )
    )
    (r / "scope.txt").write_text("Explicit artificial outcomes, no R evaluation.\n")


def test_complete_standalone_handoff(tmp_path: Path) -> None:
    f = fixture(tmp_path / "complete")
    inputs = f["output_root"] / "inputs"
    # The real standalone source entry is used for the complete positive pair.
    for mode in ("export", "compare"):
        target = inputs if mode == "export" else f["output_root"] / "comparison.json"
        argv = arguments(f, mode, target)
        if mode == "compare":
            create_r(f, f["output_root"] / "r")
            argv += [
                "--input-directory",
                str(inputs),
                "--manifest-sha256",
                hashlib.sha256((inputs / "manifest.json").read_bytes()).hexdigest(),
                "--r-directory",
                str(f["output_root"] / "r"),
            ]
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(SOURCE), *argv],
            capture_output=True,
            timeout=10,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(result.stderr.decode() + result.stdout.decode())

    payload = json.loads((f["output_root"] / "comparison.json").read_bytes())
    assert payload["passed"] is True
    assert payload["completed"] == 46
    assert len(payload["rows"]) == 46


@pytest.mark.parametrize(
    "mutation", ["missing", "duplicate", "boolean", "refused", "case-binding"]
)
def test_malformed_saved_input_refuses_before_export(
    tmp_path: Path, mutation: str
) -> None:
    g = fixture(tmp_path / mutation)
    report = copy.deepcopy(g["report"])
    if mutation == "missing":
        report["physical_responses"].pop()
    elif mutation == "duplicate":
        report["physical_responses"][1] = report["physical_responses"][0]
    elif mutation == "boolean":
        report["physical_responses"][0]["parameters"]["fall_speed_m_s"] = True
    elif mutation == "refused":
        report["physical_responses"][0].update(status="refused", response=None)
    else:
        report["cases"][0]["physical_tuple_ids"][0] = "wind-tuple:46"
    g["report_path"].write_bytes(API["encoded"](report))
    target = g["output_root"] / "inputs"
    assert API["main"](arguments(g, "export", target)) == 2 and not target.exists()


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate-r",
        "wrong-parameter",
        "underscore",
        "mismatch",
        "typed-refusal",
        "unknown-refusal",
        "fatal",
        "foreign-detail",
    ],
)
def test_complete_r_handoff_preserves_failure_dispositions(
    tmp_path: Path, mutation: str
) -> None:
    g = fixture(tmp_path / mutation)
    inputs = g["output_root"] / "inputs"
    assert API["main"](arguments(g, "export", inputs)) == 0
    r = g["output_root"] / "r"
    create_r(g, r)
    rows = API["parse_table"]((r / "tuple-outcomes.tsv").read_bytes(), API["OUTCOMES"])
    if mutation == "duplicate-r":
        rows[1] = dict(rows[0])
    elif mutation == "wrong-parameter":
        rows[0]["wind_speed_m_s"] = "3"
    elif mutation == "underscore":
        rows[0]["factor"] = "0_5"
    elif mutation == "mismatch":
        rows[0]["factor"] = ".50001"
    elif mutation in ("typed-refusal", "unknown-refusal"):
        rows[0].update(
            status="refused",
            error_message="Artificial refusal",
            reason_code="quadrature_not_converged",
            error_class="circular_receiver_reference_error,error,condition",
        )
        for k in (
            "factor",
            "raw_factor",
            "estimated_absolute_error",
            "tail_mass_bound",
            "subdivisions_used",
        ):
            rows[0][k] = ""
        (r / "summary.tsv").write_bytes(
            API["table"](
                API["SUMMARY"],
                [[46, 45, 1, 0, 0, "FALSE", "1e-11", "1e-10", 1000, "TRUE"]],
            )
        )
    elif mutation == "fatal":
        for i, row in enumerate(rows):
            row.update(
                status="fatal" if i == 0 else "not_run_after_fatal",
                error_message="Artificial unknown failure" if i == 0 else "",
                error_class="simpleError,error,condition" if i == 0 else "",
            )
            for k in (
                "factor",
                "raw_factor",
                "estimated_absolute_error",
                "tail_mass_bound",
                "subdivisions_used",
            ):
                row[k] = ""
        (r / "summary.tsv").write_bytes(
            API["table"](
                API["SUMMARY"],
                [[46, 0, 0, 1, 45, "FALSE", "1e-11", "1e-10", 1000, "TRUE"]],
            )
        )
    else:
        detail = dict.fromkeys(API["DETAILS"], "")
        detail["tuple_id"] = "foreign"
        (r / "integration-refusals.tsv").write_bytes(
            API["table"](API["DETAILS"], [[detail[k] for k in API["DETAILS"]]])
        )
    if mutation == "unknown-refusal":
        rows[0]["reason_code"] = "unrecognized_failure"
    (r / "tuple-outcomes.tsv").write_bytes(
        API["table"](
            API["OUTCOMES"], [[row[k] for k in API["OUTCOMES"]] for row in rows]
        )
    )
    target = g["output_root"] / "comparison.json"
    rc = API["main"](
        arguments(g, "compare", target)
        + [
            "--input-directory",
            str(inputs),
            "--manifest-sha256",
            hashlib.sha256((inputs / "manifest.json").read_bytes()).hexdigest(),
            "--r-directory",
            str(r),
        ]
    )
    if mutation in ("mismatch", "typed-refusal", "fatal"):
        assert rc == 1
        payload = json.loads(target.read_bytes())
        assert payload["passed"] is False
        assert len(payload["rows"]) == 46
        if mutation == "typed-refusal":
            assert (
                payload["completed"],
                payload["refused"],
                payload["fatal"],
                payload["not_run"],
            ) == (45, 1, 0, 0)
            assert (
                payload["rows"][0]["R_diagnostics"]["reason_code"]
                == "quadrature_not_converged"
            )
        elif mutation == "fatal":
            assert (
                payload["completed"],
                payload["refused"],
                payload["fatal"],
                payload["not_run"],
            ) == (0, 0, 1, 45)
        else:
            assert payload["completed"] == 46
            assert payload["rows"][0]["absolute_difference"] > API["TOLERANCE"]
    else:
        assert rc == 2 and not target.exists()
