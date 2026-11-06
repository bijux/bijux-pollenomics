"""Synthetic receipts exercise the R checker without invoking a numerical kernel."""

from __future__ import annotations

import csv
import io
import json
import math
from pathlib import Path
import subprocess
from typing import Any

import pytest

from tests.source_completion.pollen_reconstruction.nordic_physical_transfer import (
    kernel_reference as reference,
)


def contract() -> dict[str, Any]:
    return {
        "schema_version": "nordic-physical-transfer-protocol.v1",
        "independent_kernel_check": {
            "required_new_tuple_count": 3,
            "reference_function": "circular_receiver_annulus_reference",
            "source_role": "independent_receiver_reference",
            "absolute_tolerance": 1e-11,
            "relative_tolerance": 1e-10,
            "quadrature_limit": 1000,
            "factor_agreement_absolute_tolerance": 1e-8,
            "max_wall_seconds": 60,
            "max_rss_bytes": 536870912,
            "max_output_bytes": 1048576,
        },
        "transport": {
            "wind_speed_m_s": 3,
            "diffusion_coefficient": 0.12,
            "turbulence_parameter": 0.25,
            "outer_radius_m": 100000,
        },
        "new_response_requests": [
            {
                "receiver_radius_m": r,
                "inner_radius_m": r,
                "outer_radius_m": 100000,
                "fall_speed_m_s": 0.031,
            }
            for r in (80, 69, 89)
        ],
    }


def producer() -> dict[str, Any]:
    return {
        "schema_version": "nordic-physical-responses.v1",
        "taxa": ["Betula", "Pinus"],
        "transport": contract()["transport"],
        "rows": [
            {
                "receiver_radius_m": r,
                "inner_radius_m": r,
                "outer_radius_m": 100000,
                "fall_speed_m_s": f,
                "transport": contract()["transport"],
                "origin": "current" if r in (80, 69, 89) and f == 0.031 else "retained",
                "factor": 0.2,
                "estimated_absolute_error": 2e-9,
                "rigorous_error_bound": False,
                "status": "available",
                "refusal": None,
            }
            for r in (98, 80, 69, 89, 285, 160)
            for f in (0.024, 0.031)
        ],
    }


def outcomes() -> list[dict[str, str]]:
    return [
        {
            "tuple_id": f"pinus-radius:{r}",
            "status": "completed",
            "factor": ".2",
            "raw_factor": ".2",
            "estimated_absolute_error": "1e-12",
            "tail_mass_bound": "0",
            "method": "displacement_circle_overlap_one_dimensional",
            "coefficient_from_parameters": ".777",
            "exponent": ".125",
            "absolute_tolerance": "1e-11",
            "relative_tolerance": "1e-10",
            "quadrature_limit": "1000",
            "subdivisions_used": "12",
            "error_class": "",
            "reason_code": "",
            "error_message": "",
            "warnings": "",
        }
        for r in (80, 69, 89)
    ]


def test_exact_complete_correspondence() -> None:
    facts = reference.audit_outcomes(
        reference._requests(contract()), outcomes(), producer()
    )
    assert facts["status"] == "passed"
    assert facts["requests"] == 3
    assert facts["rigorous_integral_certification"] is False
    assert all(c["absolute_difference_exact"] == "0.0" for c in facts["checks"])


@pytest.mark.parametrize(
    ("factor", "passed"),
    [
        (".20000001", True),
        (".20000001000000001", False),
        (".19999999", True),
        (".19999998999999999", False),
    ],
)
def test_absolute_agreement_boundary(factor: str, passed: bool) -> None:
    rows = outcomes()
    rows[0]["factor"] = rows[0]["raw_factor"] = factor
    facts = reference.audit_outcomes(reference._requests(contract()), rows, producer())
    assert (facts["status"] == "passed") is passed


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("raw_factor", ".3"),
        ("raw_factor", "-1"),
        ("factor", "NaN"),
        ("tail_mass_bound", "-1"),
        ("tail_mass_bound", "2"),
        ("estimated_absolute_error", "-1"),
        ("subdivisions_used", "3.5"),
        ("subdivisions_used", "3001"),
        ("subdivisions_used", "0"),
        ("absolute_tolerance", "1e-9"),
        ("relative_tolerance", "1e-8"),
        ("quadrature_limit", "100"),
        ("quadrature_limit", "1000.00000000000001"),
        ("method", "analytic_point_limit"),
        ("exponent", ".25"),
        ("coefficient_from_parameters", "0"),
        ("error_message", "refused"),
        ("status", "skipped"),
    ],
)
def test_invalid_success_fields_refuse(field: str, value: str) -> None:
    rows = outcomes()
    rows[0][field] = value
    with pytest.raises(ValueError):
        reference.audit_outcomes(reference._requests(contract()), rows, producer())


def test_typed_refusal_is_retained_not_zero() -> None:
    rows = outcomes()
    rows[0].update(dict.fromkeys(reference.VALUE_COLUMNS, ""))
    rows[0].update(
        status="refused",
        error_class="circular_receiver_reference_error,error,condition",
        reason_code="quadrature_not_converged",
        error_message="R adaptive integration refused",
    )
    facts = reference.audit_outcomes(reference._requests(contract()), rows, producer())
    assert facts["status"] == "refuse_unresolved"
    assert facts["checks"][0]["reference"] == rows[0]
    rows[0]["reason_code"] = "unknown"
    with pytest.raises(ValueError, match="Unknown refusal"):
        reference.audit_outcomes(reference._requests(contract()), rows, producer())


def test_unknown_fatal_is_preserved_without_success() -> None:
    rows = outcomes()
    rows[0].update(dict.fromkeys(reference.VALUE_COLUMNS, ""))
    rows[0].update(
        status="fatal",
        error_class="simpleError,error,condition",
        reason_code="",
        error_message="unexpected failure",
    )
    assert (
        reference.audit_outcomes(reference._requests(contract()), rows, producer())[
            "status"
        ]
        == "refuse_unresolved"
    )
    rows[0]["factor"] = "0"
    with pytest.raises(ValueError, match="invented"):
        reference.audit_outcomes(reference._requests(contract()), rows, producer())


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "reordered",
        "foreign",
        "producer_duplicate",
        "producer_foreign",
    ],
)
def test_complete_tuple_inventory(change: str) -> None:
    rows, native = outcomes(), producer()
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[2] = rows[0]
    elif change == "reordered":
        rows.reverse()
    elif change == "foreign":
        rows[0]["tuple_id"] = "other"
    elif change == "producer_duplicate":
        native["rows"][0] = native["rows"][1]
    else:
        native["rows"][0]["receiver_radius_m"] = 99
    with pytest.raises(ValueError):
        reference.audit_outcomes(reference._requests(contract()), rows, native)


@pytest.mark.parametrize("change", ["radii", "bool", "tolerance", "transport"])
def test_prospective_request_contract(change: str) -> None:
    p = contract()
    if change == "radii":
        p["new_response_requests"].reverse()
    elif change == "bool":
        p["independent_kernel_check"]["required_new_tuple_count"] = True
    elif change == "tolerance":
        p["independent_kernel_check"]["factor_agreement_absolute_tolerance"] = 1e-7
    else:
        p["transport"]["wind_speed_m_s"] = 2
    with pytest.raises(ValueError):
        reference._requests(p)


def _save(path: Path, value: Any) -> dict[str, Any]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(reference._encoded(value))
    return reference._pin(path, path.name)


@pytest.fixture
def saved(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    repo = tmp_path / "repo"
    repo.mkdir()
    checker = repo / "kernel_reference.py"
    checker.write_text("# artificial checker identity\n")
    checker.with_suffix(".R").write_text("# artificial wrapper identity\n")
    monkeypatch.setattr(reference, "__file__", str(checker))
    committed_body = checker.read_bytes()
    monkeypatch.setattr(
        reference,
        "_epoch",
        lambda repository: {
            "source_commit": "a" * 40,
            "index_sha256": "e" * 64,
        },
    )
    monkeypatch.setattr(
        reference, "_blob", lambda repository, commit, path: committed_body
    )
    monkeypatch.setattr(reference, "_ancestor", lambda repository, earlier, later: None)
    rpin = _save(repo / "receiver_reference.R", {"artificial": "no numerical function"})
    p = contract()
    p["scientific_sources"] = {"independent_receiver_reference": rpin}
    protocol = repo / "protocol.json"
    _save(protocol, p)
    products = repo / "products"
    response = _save(products / "responses.json", producer())
    freeze = _save(products / "prediction-freeze.json", {"response_file": response})
    _save(
        products / "result.json",
        {
            "source_commit": "a" * 40,
            "products": {"responses": response, "prediction_freeze": freeze},
        },
    )
    output = repo / "reference"
    reference.prepare(repo, protocol, products, output)
    rd = output / "r-reference"
    rd.mkdir()
    (rd / "outcomes.tsv").write_bytes(
        reference._tsv(reference.OUTCOME_COLUMNS, outcomes())
    )
    (rd / "runtime.tsv").write_bytes(
        reference._tsv(
            ("r_version", "platform", "stats_version", "base_version"),
            [
                {
                    "r_version": "synthetic R",
                    "platform": "synthetic platform",
                    "stats_version": "4",
                    "base_version": "4",
                }
            ],
        )
    )
    execution = repo / "execution.json"
    executable = repo / "Rscript"
    executable.write_text("synthetic executable identity; never executed")
    _save(
        execution,
        {
            "exit_code": 0,
            "wall_seconds": 1,
            "peak_rss_bytes": 1234,
            "command": [
                str(executable),
                str(checker.with_suffix(".R")),
                str(repo / rpin["path"]),
                str(output / "requests.tsv"),
                str(rd),
            ],
        },
    )
    return {
        "repository": repo,
        "protocol": protocol,
        "products": products,
        "output": output,
        "execution": execution,
    }


def test_closed_receipt_io(saved: dict[str, Path]) -> None:
    facts = reference.check(**saved)
    assert facts["status"] == "passed"
    assert facts["source_commit"] == "a" * 40
    assert facts["execution"]["facts"]["command"][0] == str(
        saved["repository"] / "Rscript"
    )
    assert (saved["output"] / "verification.json").is_file()
    with pytest.raises(FileExistsError):
        reference.check(**saved)


@pytest.mark.parametrize(
    "changed",
    [
        "protocol",
        "reference",
        "checker",
        "responses",
        "freeze",
        "request",
        "runtime",
        "extra",
        "command",
        "wall",
        "rss",
        "exit",
        "source_commit",
    ],
)
def test_io_custody_and_resource_tampering(
    saved: dict[str, Path], changed: str
) -> None:
    repo, output, products = saved["repository"], saved["output"], saved["products"]
    if changed in (
        "protocol",
        "reference",
        "checker",
        "responses",
        "freeze",
        "request",
    ):
        path = {
            "protocol": saved["protocol"],
            "reference": repo / "receiver_reference.R",
            "checker": repo / "kernel_reference.py",
            "responses": products / "responses.json",
            "freeze": products / "prediction-freeze.json",
            "request": output / "requests.tsv",
        }[changed]
        path.write_bytes(path.read_bytes() + b" ")
    elif changed == "runtime":
        (output / "r-reference/runtime.tsv").write_text("bad\n")
    elif changed == "extra":
        (output / "r-reference/undeclared.tsv").write_text("extra")
    elif changed == "source_commit":
        d = json.loads((products / "result.json").read_bytes())
        d["source_commit"] = "b" * 40
        _save(products / "result.json", d)
    else:
        resource = json.loads(saved["execution"].read_bytes())
        if changed == "command":
            resource["command"][-1] = "/other/outputs"
        else:
            key, value = {
                "wall": ("wall_seconds", 61),
                "rss": ("peak_rss_bytes", 536870913),
                "exit": ("exit_code", 1),
            }[changed]
            resource[key] = value
        _save(saved["execution"], resource)
    with pytest.raises((ValueError, KeyError)):
        reference.check(**saved)


def test_strict_json_and_path_identity(tmp_path: Path) -> None:
    for body in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":1e400}', b"[]"):
        with pytest.raises(ValueError):
            reference._json(body)
    with pytest.raises(ValueError):
        reference._child(tmp_path, "../escape")
    target = tmp_path / "target"
    target.write_text("original")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ValueError):
        reference._bytes(link)


def test_tsv_quoted_warning_preserved() -> None:
    rows = outcomes()
    rows[0]["warnings"] = 'tab\t and newline\n and "quote"'
    assert (
        reference._table(
            reference._tsv(reference.OUTCOME_COLUMNS, rows), reference.OUTCOME_COLUMNS
        )
        == rows
    )


def test_invalid_tsv_shape() -> None:
    stream = io.StringIO()
    csv.writer(stream, delimiter="\t").writerow(["tuple_id", "status"])
    with pytest.raises(ValueError):
        reference._table(stream.getvalue().encode(), reference.OUTCOME_COLUMNS)


@pytest.mark.parametrize("mutation", ["duplicate", "missing", "extra"])
def test_outcome_field_set_remains_exact(mutation: str) -> None:
    header = list(reference.OUTCOME_COLUMNS)
    if mutation == "duplicate":
        header[-1] = header[-2]
    elif mutation == "missing":
        header.pop()
    else:
        header.append("foreign")
    with pytest.raises(ValueError, match="header"):
        reference._table(("\t".join(header) + "\n").encode(), reference.OUTCOME_COLUMNS)


def test_only_outcomes_allow_header_permutation() -> None:
    columns = tuple(reversed(reference.OUTCOME_COLUMNS))
    assert (
        reference._table(reference._tsv(columns, outcomes()), reference.OUTCOME_COLUMNS)
        == outcomes()
    )
    with pytest.raises(ValueError, match="header"):
        reference._table(b"status\ttuple_id\n", ("tuple_id", "status"))


@pytest.mark.parametrize("field", ["absolute_tolerance", "relative_tolerance"])
def test_adjacent_binary64_control_is_not_accepted(field: str) -> None:
    rows = outcomes()
    current = float(rows[0][field])
    rows[0][field] = format(math.nextafter(current, math.inf), ".17g")
    with pytest.raises(ValueError, match="integration control"):
        reference.audit_outcomes(reference._requests(contract()), rows, producer())


def test_authentic_r_metadata_serialization_without_kernel() -> None:
    executable = Path("/usr/local/bin/Rscript")
    if not executable.is_file():
        pytest.skip("Rscript unavailable for source-free serialization control")
    # This evaluates only base-R list insertion and sprintf; no source() or kernel call.
    program = """
fields <- c("factor", "raw_factor", "estimated_absolute_error", "tail_mass_bound", "method",
 "coefficient_from_parameters", "exponent", "absolute_tolerance", "relative_tolerance",
 "quadrature_limit", "subdivisions_used")
values <- list(.2,.2,1e-12,0,"displacement_circle_overlap_one_dimensional",.777,.125,1e-11,1e-10,1000L,12L)
rows <- lapply(c(80,69,89),function(r) {
 row <- list(tuple_id=paste0("pinus-radius:",r),status="completed")
 for(i in seq_along(fields)) row[[fields[i]]] <- if(is.numeric(values[[i]])) sprintf("%.17g",values[[i]]) else values[[i]]
 row$error_class <- row$reason_code <- row$error_message <- ""
 row$warnings <- ""
 as.data.frame(row,stringsAsFactors=FALSE)
})
write.table(do.call(rbind,rows),stdout(),row.names=FALSE,quote=TRUE,sep="\\t")
"""
    completed = subprocess.run(
        [str(executable), "--vanilla", "-e", program],
        capture_output=True,
        timeout=15,
        check=True,
    )
    assert len(completed.stdout) < 8192
    header = next(csv.reader(io.StringIO(completed.stdout.decode()), delimiter="\t"))
    assert header[-4:] == ["error_message", "reason_code", "error_class", "warnings"]
    rows = reference._table(completed.stdout, reference.OUTCOME_COLUMNS)
    assert rows[0]["absolute_tolerance"] == "9.9999999999999994e-12"
    assert (
        reference.audit_outcomes(reference._requests(contract()), rows, producer())[
            "status"
        ]
        == "passed"
    )


def test_historical_python_builder_bound_without_rewriting_manifest(
    saved: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository, output = saved["repository"], saved["output"]
    before = (output / "manifest.json").read_bytes()
    checker = repository / "kernel_reference.py"
    original = checker.read_bytes()
    checker.write_text("# committed corrected observer\n")
    current = checker.read_bytes()
    monkeypatch.setattr(
        reference,
        "_epoch",
        lambda repository: {
            "source_commit": "b" * 40,
            "index_sha256": "f" * 64,
        },
    )

    def blob(repository: Path, commit: str, path: str) -> bytes:
        assert path == "kernel_reference.py"
        return {"a" * 40: original, "b" * 40: current}[commit]

    monkeypatch.setattr(reference, "_blob", blob)
    facts = reference.check(**saved)
    assert facts["source_commit"] == "a" * 40
    assert facts["observer_source_commit"] == "b" * 40
    assert facts["historical_builder_authenticated"] is True
    assert facts["checker_sources"][0] != facts["observer_checker_source"]
    assert (output / "manifest.json").read_bytes() == before


def test_historical_python_builder_requires_original_blob(
    saved: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checker = saved["repository"] / "kernel_reference.py"
    checker.write_text("# new corrected committed observer\n")
    monkeypatch.setattr(
        reference,
        "_epoch",
        lambda repository: {
            "source_commit": "b" * 40,
            "index_sha256": "f" * 64,
        },
    )
    monkeypatch.setattr(
        reference,
        "_blob",
        lambda repository, commit, path: (
            checker.read_bytes() if commit == "b" * 40 else b"wrong original blob"
        ),
    )
    with pytest.raises(ValueError, match="committed builder"):
        reference.check(**saved)


def test_original_r_wrapper_never_gets_historical_exception(
    saved: dict[str, Path],
) -> None:
    (saved["repository"] / "kernel_reference.R").write_text("# altered R wrapper\n")
    with pytest.raises(ValueError, match="Foreign checker"):
        reference.check(**saved)


@pytest.mark.parametrize("change", ["head", "index", "ancestry"])
def test_observer_epoch_stable_and_ancestral(
    saved: dict[str, Path],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    if change == "ancestry":

        def unrelated(repository: Path, earlier: str, later: str) -> None:
            raise ValueError("unrelated producer epoch")

        monkeypatch.setattr(reference, "_ancestor", unrelated)
    else:
        first = {"source_commit": "a" * 40, "index_sha256": "e" * 64}
        last = {
            **first,
            "source_commit" if change == "head" else "index_sha256": "b"
            * (40 if change == "head" else 64),
        }
        epochs = iter([first, last])
        monkeypatch.setattr(reference, "_epoch", lambda repository: next(epochs))
    with pytest.raises(ValueError):
        reference.check(**saved)


def test_producer_refusal_cannot_become_agreement() -> None:
    native = producer()
    row = next(r for r in native["rows"] if r["origin"] == "current")
    row.update(
        status="refused",
        factor=None,
        estimated_absolute_error=None,
        refusal={
            "error_type": "ValidationError",
            "reason_code": "invalid_input",
            "message": "refused",
        },
    )
    facts = reference.audit_outcomes(
        reference._requests(contract()), outcomes(), native
    )
    assert facts["status"] == "refuse_unresolved"
    assert facts["checks"][0]["producer_response"]["refusal"] == row["refusal"]
    row["factor"] = 0
    with pytest.raises(ValueError, match="invent"):
        reference.audit_outcomes(reference._requests(contract()), outcomes(), native)


def test_current_transport_cannot_be_substituted() -> None:
    native = producer()
    row = next(r for r in native["rows"] if r["origin"] == "current")
    row["transport"]["wind_speed_m_s"] = 4
    with pytest.raises(ValueError, match="transport"):
        reference.audit_outcomes(reference._requests(contract()), outcomes(), native)


def test_foreign_self_consistent_checker_manifest(saved: dict[str, Path]) -> None:
    output, repo = saved["output"], saved["repository"]
    manifest = json.loads((output / "manifest.json").read_bytes())
    p = repo / "foreign.py"
    p.write_text("self-consistent foreign checker")
    manifest["checker_sources"][0] = reference._pin(p, "foreign.py")
    _save(output / "manifest.json", manifest)
    with pytest.raises(ValueError, match="Foreign checker"):
        reference.check(**saved)


def test_aggregate_byte_limit(saved: dict[str, Path]) -> None:
    (saved["output"] / "additional-log.txt").write_bytes(b"x" * reference.MAX_BYTES)
    with pytest.raises(ValueError, match="Aggregate"):
        reference.check(**saved)
    assert not (saved["output"] / "verification.json").exists()
