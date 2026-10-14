"""Independently inspect retained diagnostics using only standard-library scalars."""

from __future__ import annotations

import argparse
import ast
from collections.abc import Sequence
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import stat
import struct
import sys
from typing import Any
import zipfile

CAPTURE = "data/method-certification/native-r-finite-covariance/capture"
MANIFEST_SHA256 = "008cb45fa66f8b7c96915678ee3f1ec3026924ba3fe81050ca773515e030199b"
PETR_PATH = "docs/report/method-certification/petrkunes-r-comparison/taxa.csv"
PETR_SHA256 = "b37211fda3a692d1b903501a14323ab14820950d434f8a2953b9ea25a269b915"


def _raw(root: Path, relative: str) -> bytes:
    path = root / relative
    if Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError("Confined retained path required")
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError("Retained path alias refused")
        current = current.parent
    details = path.stat()
    if not stat.S_ISREG(details.st_mode) or details.st_nlink != 1:
        raise ValueError("Retained file identity differs")
    return path.read_bytes()


def _npy(raw: bytes) -> list[float | str]:
    """Decode only the pinned one-dimensional float64/Unicode saved arrays."""
    if raw[:6] != b"\x93NUMPY":
        raise ValueError("Retained NPY signature differs")
    if raw[6:8] == b"\x01\x00":
        length = struct.unpack("<H", raw[8:10])[0]
        offset = 10
    elif raw[6:8] == b"\x02\x00":
        length = struct.unpack("<I", raw[8:12])[0]
        offset = 12
    else:
        raise ValueError("Unsupported retained NPY encoding")
    header = ast.literal_eval(raw[offset : offset + length].decode("latin1"))
    if len(header["shape"]) != 1 or header["fortran_order"] is not False:
        raise ValueError("Retained vector shape differs")
    size = header["shape"][0]
    body = raw[offset + length :]
    kind = header["descr"]
    if kind == "<f8":
        if len(body) != size * 8:
            raise ValueError("Retained float vector size differs")
        return list(struct.unpack("<" + "d" * size, body))
    if kind.startswith("<U"):
        width = int(kind[2:]) * 4
        if len(body) != size * width:
            raise ValueError("Retained label vector size differs")
        return [
            body[i * width : (i + 1) * width].decode("utf-32-le").rstrip("\x00")
            for i in range(size)
        ]
    raise ValueError("Unexpected retained vector dtype")


def _same(left: float, right: float) -> bool:
    return left == right or (math.isnan(left) and math.isnan(right))


def _encoded(value: float | str) -> float | str:
    if isinstance(value, str) or math.isfinite(value):
        return value
    return "NaN" if math.isnan(value) else ("Infinity" if value > 0 else "-Infinity")


def verify_metrics(
    actual: Sequence[float | str], expected: Sequence[float | str], row: dict[str, Any]
) -> int:
    """Check every reported vector difference, mask and original threshold outcome."""
    if len(actual) != len(expected) or row["values"] != len(expected):
        raise ValueError("Diagnostic population differs")
    strings = bool(expected and isinstance(expected[0], str))
    if row["comparison_kind"] != ("exact_strings" if strings else "numeric"):
        raise ValueError("Diagnostic comparison kind differs")
    if (
        row["relative_error_denominator"]
        != "abs(expected), excluding zero and nonfinite reference values"
    ):
        raise ValueError("Diagnostic relative denominator differs")
    differences = []
    failures = []
    absolute = []
    relative = []
    zero_reference = []
    nonfinite_mismatch = []
    expected_nonfinite = []
    actual_nonfinite = []
    for index, (left, right) in enumerate(zip(actual, expected, strict=True)):
        if strings:
            equal = str(left) == str(right)
            accepted = equal
        else:
            a, b = float(left), float(right)
            equal = _same(a, b)
            finite = math.isfinite(a) and math.isfinite(b)
            if not math.isfinite(a):
                actual_nonfinite.append({"index": index, "value": _encoded(a)})
            if not math.isfinite(b):
                expected_nonfinite.append({"index": index, "value": _encoded(b)})
            accepted = equal or (
                finite
                and index not in row["exact_indices"]
                and abs(a - b) <= row["atol"] + row["rtol"] * abs(b)
            )
            if finite:
                absolute.append(abs(a - b))
                if b != 0:
                    relative.append(abs(a - b) / abs(b))
                elif not equal:
                    zero_reference.append(index)
            elif not equal:
                nonfinite_mismatch.append(index)
        if not equal:
            detail: dict[str, Any] = {
                "index": index,
                "actual": _encoded(left),
                "expected": _encoded(right),
            }
            if not strings:
                a, b = float(left), float(right)
                detail["within_original_tolerance"] = accepted
                if math.isfinite(a) and math.isfinite(b):
                    detail["absolute_error"] = _encoded(abs(a - b))
                    detail["relative_error"] = (
                        _encoded(abs(a - b) / abs(b)) if b else None
                    )
            differences.append(detail)
        if not accepted:
            failures.append(index)
    claims = {
        "differing_entries": differences,
        "differing_entry_count": len(differences),
        "out_of_tolerance_indices": failures,
        "zero_reference_difference_indices": zero_reference,
        "nonfinite_mismatch_indices": nonfinite_mismatch,
        "expected_nonfinite_entries": expected_nonfinite,
        "actual_nonfinite_entries": actual_nonfinite,
        "status": "failed" if failures else "passed",
        "max_absolute_error": None if strings else _encoded(max(absolute, default=0.0)),
        "max_relative_error": None if strings else _encoded(max(relative, default=0.0)),
    }
    for name, value in claims.items():
        if row[name] != value:
            raise ValueError("Diagnostic scalar-derived claim differs: " + name)
    return len(expected)


def verify(repository: Path, report_path: Path, protocol_path: Path) -> dict[str, Any]:
    """Use independent NPY decoding and scalar arithmetic on original raw bytes."""
    root = repository / CAPTURE
    manifest_raw = _raw(root, "capture.json")
    if hashlib.sha256(manifest_raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("Original native manifest differs")
    manifest = json.loads(manifest_raw)
    base = Path(CAPTURE).parent.as_posix()
    expected_inputs = {CAPTURE + "/capture.json": MANIFEST_SHA256}
    expected_inputs.update(
        {
            CAPTURE + "/" + name: pin["sha256"]
            for name, pin in manifest["raw_members"].items()
        }
    )
    evidence = {
        "capture/receipt.json": manifest["execution_receipt"],
        **manifest["source_context"]["evidence_members"],
    }
    review = manifest["independent_terminal_review"]
    evidence[review["path"]] = review
    evidence.update({pin["path"]: pin for pin in manifest["public_archives"].values()})
    acquisition = manifest["public_acquisition"]
    evidence[acquisition["path"]] = acquisition
    expected_inputs.update(
        {base + "/" + name: pin["sha256"] for name, pin in evidence.items()}
    )
    if len(expected_inputs) != 153:
        raise ValueError("Exact original capture input inventory required")
    expected_inputs[PETR_PATH] = PETR_SHA256
    for relative, digest in expected_inputs.items():
        if hashlib.sha256(_raw(repository, relative)).hexdigest() != digest:
            raise ValueError("Original retained input identity differs")
    report = json.loads(report_path.read_bytes())
    if (
        report["protocol_sha256"]
        != hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    ):
        raise ValueError("Diagnostics protocol identity differs")
    if (
        report["fresh_R_executed"]
        or report["python_expectations_regenerated"]
        or report["tolerances_modified"]
    ):
        raise ValueError("Retained-only diagnostics scope differs")
    if report["retained_input_sha256"] != expected_inputs:
        raise ValueError("Diagnostic retained input inventory differs")
    if (
        report["captured_core_cases"],
        report["captured_domain_cases"],
        report["petrkunes_retained_mean_pairs"],
        report["petrkunes_retained_standard_error_pairs"],
    ) != (43, 23, 124, 124) or report["release_certificate"] is not False:
        raise ValueError("Diagnostic declared source scope differs")
    rows = report["cases"]
    if (
        report["schema_version"] != "retained-native-oracle-vector-diagnostics.v1"
        or report["native_capture_manifest_sha256"] != MANIFEST_SHA256
        or report["native_source_revision"] != manifest["source_revision"]
    ):
        raise ValueError("Diagnostic native source identity differs")
    if report["status"] != (
        "passed" if all(row["status"] == "passed" for row in rows) else "failed"
    ):
        raise ValueError("Diagnostic aggregate status differs")
    if len(rows) != 74 or len({(r["profile"], r["id"]) for r in rows}) != 74:
        raise ValueError("Exact 74-row diagnostics population required")
    scalar_count = 0
    core = json.loads((root / "oracle/case_manifest.json").read_bytes())
    with zipfile.ZipFile(root / "oracle/python_expected_not_R_goldens.npz") as saved:
        for index, spec in enumerate(core):
            row = rows[index]
            if (
                row["profile"] != "core"
                or row["name"] != spec["name"]
                or row["mode"] != spec["mode"]
            ):
                raise ValueError("Diagnostic core source labels differ")
            if (
                row["id"] != spec["id"]
                or row["rtol"] != spec["rtol"]
                or row["atol"] != spec["atol"]
                or row["exact_indices"] != spec["exact_indices"]
            ):
                raise ValueError("Original core protocol differs")
            expected = _npy(saved.read(spec["id"] + ".npy"))
            csv_rows = list(
                csv.DictReader(
                    io.StringIO((root / "oracle" / (spec["id"] + ".csv")).read_text())
                )
            )
            actual = [
                r["value"]
                if expected and isinstance(expected[0], str)
                else float(r["value"].replace("NA", "nan"))
                for r in csv_rows
            ]
            scalar_count += verify_metrics(actual, expected, row)
    domains = json.loads((root / "source-domains/case_manifest.json").read_bytes())
    for index, spec in enumerate(domains, start=43):
        row = rows[index]
        if row["profile"] != "source-domains" or row["semantics"] != spec["semantics"]:
            raise ValueError("Diagnostic domain source labels differ")
        if (
            row["id"] != spec["id"]
            or row["rtol"] != 1e-10
            or row["atol"] != 3e-10
            or row["exact_indices"] != []
        ):
            raise ValueError("Original domain protocol differs")
        expected = _npy(
            (
                root
                / "source-domains/python_expected_not_R_goldens"
                / (spec["id"] + ".npy")
            ).read_bytes()
        )
        actual = [
            float(r["value"].replace("NA", "nan"))
            for r in csv.DictReader(
                io.StringIO(
                    (root / "source-domains" / (spec["id"] + "-R.csv")).read_text()
                )
            )
        ]
        scalar_count += verify_metrics(actual, expected, row)
    raw = _raw(repository, PETR_PATH)
    if hashlib.sha256(raw).hexdigest() != PETR_SHA256:
        raise ValueError("Original tagged R table differs")
    taxa = list(csv.DictReader(io.StringIO(raw.decode())))
    index = 66
    for scenario in ("single", "unequal_pair", "six_sites", "full_grid"):
        selected = [r for r in taxa if r["scenario"] == scenario]
        for quantity in ("cover", "se"):
            row = rows[index]
            if row[
                "profile"
            ] != "petrkunes_original_vs_tagged_R_retained_precision" or row[
                "taxon_axis"
            ] != [item["taxon"] for item in selected]:
                raise ValueError("Diagnostic tagged source axis differs")
            if (
                row["id"] != scenario + "_" + quantity
                or row["rtol"] != 0
                or row["atol"] != 0
            ):
                raise ValueError("Tagged R serialized exact protocol differs")
            scalar_count += verify_metrics(
                [float(r["secondary_" + quantity]) for r in selected],
                [float(r["original_" + quantity]) for r in selected],
                row,
            )
            index += 1
    return {
        "schema_version": "retained-oracle-diagnostics-independent-review.v1",
        "status": "passed",
        "case_rows": 74,
        "scalar_pairs": scalar_count,
        "report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "native_capture_sha256": MANIFEST_SHA256,
        "stdlib_only": True,
        "fresh_R_executed": False,
        "model_executed": False,
        "scope": "Independent standard-library NPY decoder and scalar residual/threshold review of original saved vectors. No source models, new draws, historical execution or scientific admission.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--protocol", required=True, type=Path)
    args = parser.parse_args(argv)
    if "numpy" in sys.modules or "scipy" in sys.modules:
        raise ValueError("Independent observer must use only standard-library imports")
    root = args.repository.resolve(strict=True)
    output = args.output.absolute()
    if (
        ".." in output.parts
        or not output.is_relative_to(root / "artifacts")
        or output.exists()
    ):
        raise ValueError("Absent confined artifact output required")
    current = output
    while current != root:
        if current.is_symlink():
            raise ValueError("Output alias refused")
        current = current.parent
    result = verify(root, args.report, args.protocol)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
