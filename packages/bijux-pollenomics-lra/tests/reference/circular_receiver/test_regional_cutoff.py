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

SOURCE = Path(__file__).with_name("regional_cutoff.py").absolute()
API = runpy.run_path(str(SOURCE))

pytestmark = pytest.mark.reference


def fixture(directory: Path) -> dict[str, Any]:
    repository = directory / "repository"
    output_root = repository / "artifacts"
    output_root.mkdir(parents=True)
    protocol = {
        "schema_version": "nordic-conditional-regional-extent-sensitivity.v1",
        "alternative_regional_extent_m": [50000, 200000],
        "baseline_regional_extent_m": 100000,
        "wind_speed_m_s": 3,
        "source_epoch": "1" * 40,
        "diffusion_coefficient": 0.12,
        "turbulence_parameter": 0.25,
    }
    responses: list[dict[str, Any]] = []
    for extent in (50000, 200000):
        for i in range(23):
            responses.append(
                {
                    "tuple_id": f"extent-tuple:{len(responses) + 1}",
                    "parameters": {
                        "receiver_radius_m": 1,
                        "inner_radius_m": 1,
                        "outer_radius_m": extent,
                        "fall_speed_m_s": 0.02 + i * 0.001,
                        "diffusion_coefficient": 0.12,
                        "turbulence_parameter": 0.25,
                        "wind_speed_m_s": 3,
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
    for extent, offset in ((50000, 0), (200000, 23)):
        for group, ids in enumerate(groups):
            rows = [responses[index + offset] for index in ids]
            cases.append(
                {
                    "case_id": f"artificial-{group}.extent_{extent}m",
                    "baseline_case_id": f"artificial-{group}",
                    "regional_extent_m": extent,
                    "physical_tuple_ids": [row["tuple_id"] for row in rows],
                    "original_case_context": {
                        "case_id": f"artificial-{group}",
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
        "schema_version": "nordic-conditional-regional-extent-result.v1",
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
    original_report = f["report_path"].read_bytes()
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
    assert f["report_path"].read_bytes() == original_report
    assert payload["saved_source_epoch"] == "1" * 40
    assert payload["saved_execution_epoch"] == "2" * 40
    assert payload["reference_execution_epoch"] == "3" * 40
    exported = API["parse_table"]((inputs / "tuples.tsv").read_bytes(), API["COLUMNS"])
    assert len(exported) == 46
    assert "factor" not in API["COLUMNS"] and "saved_factor" not in API["COLUMNS"]
    # The helper is source authority: wrong bytes and linked siblings must refuse.
    isolated = f["output_root"] / "helper-boundary"
    isolated.mkdir()
    program = isolated / "regional_cutoff.py"
    program.write_bytes(SOURCE.read_bytes())
    helper = isolated / "nordic_wind.py"
    helper.write_bytes(SOURCE.with_name("nordic_wind.py").read_bytes() + b"\n")
    for linked in (False, True):
        if linked:
            helper.unlink()
            helper.symlink_to(SOURCE.with_name("nordic_wind.py"))
        result = subprocess.run(
            [sys.executable, "-I", "-B", str(program), "--help"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        assert result.returncode != 0
        assert b"scalar helper" in result.stderr


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
        report["cases"][0]["physical_tuple_ids"][0] = "extent-tuple:46"
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
        rows[0]["wind_speed_m_s"] = "2"
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


@pytest.mark.parametrize(
    "mutation",
    [
        "wind-profile",
        "unrequested-extent",
        "wrong-extent-use",
        "duplicate-case-pair",
        "foreign-context",
        "protocol-axis",
        "source-epoch",
        "nonfinite",
    ],
)
def test_cutoff_axis_and_original_context_refuse(tmp_path: Path, mutation: str) -> None:
    f = fixture(tmp_path / mutation)
    report = copy.deepcopy(f["report"])
    if mutation == "wind-profile":
        report["physical_responses"][0]["parameters"]["wind_speed_m_s"] = 2
    elif mutation == "unrequested-extent":
        report["physical_responses"][0]["parameters"]["outer_radius_m"] = 100000
    elif mutation == "wrong-extent-use":
        report["cases"][0]["physical_tuple_ids"][0] = "extent-tuple:24"
    elif mutation == "duplicate-case-pair":
        report["cases"][9]["baseline_case_id"] = "artificial-1"
    elif mutation == "foreign-context":
        report["cases"][0]["original_case_context"]["case_id"] = "foreign"
    elif mutation == "protocol-axis":
        report["protocol"]["alternative_regional_extent_m"] = [50000, 100000]
        f["protocol_path"].write_bytes(API["encoded"](report["protocol"]))
        report["protocol_sha256"] = hashlib.sha256(
            f["protocol_path"].read_bytes()
        ).hexdigest()
    elif mutation == "source-epoch":
        report["baseline_source_epoch"] = "4" * 40
    else:
        report["physical_responses"][0]["parameters"]["fall_speed_m_s"] = float("nan")
    f["report_path"].write_bytes(json.dumps(report, allow_nan=True).encode())
    target = f["output_root"] / "inputs"
    assert API["main"](arguments(f, "export", target)) == 2
    assert not target.exists()


def test_documented_helper_identity_is_current_with_historical_basis() -> None:
    current = API["_HELPER"].read_bytes()
    identity = API["_HELPER_EXECUTION_IDENTITY"]
    assert identity["sha256"] == hashlib.sha256(current).hexdigest()
    assert identity["bytes"] == len(current)
    assert identity["historical_basis"] == {
        "sha256": "af2c288baefddd267e0a481a1fb6afbaba8dd94b5150a397ce1174ff0f902b56",
        "bytes": 18897,
    }
    assert len(API["_scalar_helper_historical_basis"](current)) == 18897


@pytest.mark.parametrize(
    "mutation",
    [
        "comment",
        "import",
        "doc-text",
        "doc-scope",
        "inline-comment",
        "header",
        "partial-docs",
        "export",
        "number-or-type",
    ],
)
def test_only_exact_named_helper_documentation_is_admitted(mutation: str) -> None:
    current = API["_HELPER"].read_bytes()
    _, header, documentation = API["_SCALAR_HELPER_DOCUMENTATION"][0]
    if mutation == "comment":
        changed = current + b"\n# unknown comment\n"
    elif mutation == "import":
        changed = current + b"\nimport math as unrelated\n"
    elif mutation == "doc-text":
        changed = current.replace(
            documentation, documentation.replace(b'"""', b'"""Altered ', 1), 1
        )
    elif mutation == "doc-scope":
        changed = current.replace(header + documentation, header, 1) + documentation
    elif mutation == "inline-comment":
        changed = current.replace(
            documentation, documentation.rstrip(b"\n") + b" # unknown\n", 1
        )
    elif mutation == "header":
        changed = current.replace(header, header.replace(b":", b" : ", 1), 1)
    elif mutation == "partial-docs":
        changed = current.replace(header + documentation, header, 1)
    elif mutation == "export":
        changed = current + b'\n__all__ = ["unknown"]\n'
    else:
        changed = current + b"\nUNKNOWN_NUMBER = 2\n"
    assert changed != current
    with pytest.raises(ValueError):
        API["_scalar_helper_historical_basis"](changed)
