"""Exact custody and independent scalar checks for controlled LRA owners."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

FAMILIES = ("optimizer-solution-quality", "paired-love-draws")
R_SHA = "d918ce5022d859e20c38094bb0b6199186cefd8bb96ffeb58618471c9a65a22d"
SOURCE_SHA = "ea496ae82807b52c9dd3d4b39b4dfa294bfac4068e20184ce56187bff70caf5c"
NATIVE_RECEIPT_SHA = "8b2b7f4b279a32ad0d3ddfa0653ecfa2fd8928aba2cf281451a045c699f00d04"
PRODUCTS = {
    "optimizer-solution-quality": (
        "python-fits.csv",
        "r-fits.csv",
        "r-session.txt",
        "report.json",
        "summary.csv",
    ),
    "paired-love-draws": (
        "draws.json",
        "python-values.csv",
        "r-session.txt",
        "r-values.csv",
        "report.json",
        "setup.json",
    ),
}


def require(value: object, message: str) -> None:
    if not value:
        raise ValueError(message)


def sha(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def pin(path: Path) -> dict[str, Any]:
    require(
        path.is_absolute()
        and path.resolve() == path
        and path.is_file()
        and not any(p.is_symlink() for p in (path, *path.parents)),
        "Physical regular input required",
    )
    return {"path": str(path), "sha256": sha(path), "bytes": path.stat().st_size}


def read(path: Path) -> Any:
    return json.loads(path.read_bytes())


def dump(path: Path, value: object) -> None:
    require(
        not path.exists() and not any(p.is_symlink() for p in (path, *path.parents)),
        "Fresh contained receipt required",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def original_library(repository: Path) -> dict[str, Any]:
    base = repository / "artifacts/science/native-reference-admission"
    public = repository / "data/method-certification/native-r-finite-covariance"
    receipt = base / "native/receipt.json"
    terminal = base / "terminal.json"
    manifest = public / "capture/capture.json"
    require(
        sha(manifest)
        == "008cb45fa66f8b7c96915678ee3f1ec3026924ba3fe81050ca773515e030199b",
        "Original public native capture differs",
    )
    authority = read(manifest)
    evidence = authority["source_context"]["evidence_members"]
    for name, identity in evidence.items():
        require(
            sha(public / name) == identity["sha256"]
            and (public / name).stat().st_size == identity["size"],
            "Original public execution evidence differs",
        )
    require(
        sha(receipt) == NATIVE_RECEIPT_SHA == sha(public / "capture/receipt.json"),
        "Original native receipt differs",
    )
    require(
        sha(terminal) == sha(public / "execution-evidence/terminal.json"),
        "Original native terminal differs",
    )
    record = read(terminal)
    require(
        record["exit_code"] == 0 and record["status"] == "passed",
        "Original native installation did not pass",
    )
    expected = {
        k.removeprefix("native/library/"): v
        for k, v in record["outputs_sha256"].items()
        if k.startswith("native/library/")
    }
    library = base / "native/library"
    actual = {
        p.relative_to(library).as_posix(): sha(p)
        for p in library.rglob("*")
        if p.is_file() and not p.is_symlink()
    }
    require(
        expected == actual and len(actual) == 913,
        "Original native installed-library membership or bytes differ",
    )
    require(
        (library / "disqover/SOURCE_SHA256").read_text().strip() == SOURCE_SHA,
        "Source archive marker differs",
    )
    return {
        "root": str(library),
        "receipt": pin(receipt),
        "terminal": pin(terminal),
        "public_native_capture": pin(manifest),
        "public_execution_evidence": [pin(public / name) for name in evidence],
        "installed_files": 913,
        "original_jsonlite_scope": "Version2.0.0 observed but individual jsonlite files were not originally pinned; the current full R/jsonlite tree is a fresh runtime identity, not recovered original file custody.",
    }


def objective(case: dict[str, Any], candidate: list[float]) -> float:
    require(
        all(math.isfinite(x) and 0 <= x <= 1 for x in candidate) and sum(candidate) > 0,
        "Invalid candidate",
    )
    cover = [x / sum(candidate) for x in candidate]
    values = [
        case["regional"][j]
        + sum(
            row[j] * cover[j] * case["ppe"][j] * f
            for row, f in zip(case["local_k"], case["local_fraction"], strict=True)
        )
        for j in range(len(cover))
    ]
    mass = sum(values)
    require(mass > 0 and all(x > 0 for x in values), "Nonpositive objective projection")
    return math.sqrt(
        sum(
            (math.log(v / mass) - math.log(observed + 0.001)) ** 2
            for v, observed in zip(values, case["observed"], strict=True)
        )
    )


def optimum(name: str) -> float:
    if name == "symmetric-interior":
        return math.sqrt(2) * abs(math.log(0.5 / 0.501))
    if name == "constrained-boundary":
        return math.hypot(math.log(0.75 / 1.001), math.log(0.25 / 0.001))
    require(name == "composition-ambiguous", "Unknown objective case")
    low, high = 1 / 3, 3 / 5
    for _ in range(80):
        p = (low + high) / 2
        derivative = (
            -4 * math.log((1 - p) / 0.502) / (1 - p) + 2 * math.log(p / 0.501) / p
        )
        if derivative > 0:
            high = p
        else:
            low = p
    p = (low + high) / 2
    return math.sqrt(2 * math.log((1 - p) / 0.502) ** 2 + math.log(p / 0.501) ** 2)


def check_optimizer(
    config: dict[str, Any],
    python: list[dict[str, str]],
    native: list[dict[str, str]],
    summary: list[dict[str, str]],
) -> dict[str, Any]:
    names = [c["name"] for c in config["cases"]]
    require(
        config["schema_version"] == "love-objective-cases.1"
        and config["iterations"] == 400
        and config["optimizer_seed"] == 7,
        "Prospective optimizer contract differs",
    )
    require(
        names
        == ["symmetric-interior", "constrained-boundary", "composition-ambiguous"],
        "Controlled objective membership differs",
    )
    require(
        all([r["case"] for r in rs] == names for rs in [python, native, summary]),
        "Ordered objective cases differ",
    )
    checks = []
    for case, py, r, sm in zip(config["cases"], python, native, summary, strict=True):
        n = len(case["regional"])
        a = [float(py[f"c{i + 1}"]) for i in range(n)]
        b = [float(r[f"c{i + 1}"]) for i in range(n)]
        pyvalue, rvalue = float(py["bestval"]), float(r["bestval"])
        known = optimum(case["name"])
        pa, pb = objective(case, a), objective(case, b)
        require(
            py["success"] == "true"
            and 0 < int(py["iter"]) <= 400
            and 0 < int(py["nfeval"]) <= 20000,
            "Python optimizer status or budget differs",
        )
        require(
            int(r["iter"]) == 400 and int(r["nfeval"]) == 400 * 10 * n + 10 * n,
            "R fixed-cap negative status differs",
        )
        require(
            -1e-12 <= pyvalue - known <= 1e-4 and -1e-12 <= rvalue - known <= 1e-4,
            "Known optimum gap fails",
        )
        require(
            max(abs(pa - pyvalue), abs(pb - rvalue), abs(float(r["r_at_python"]) - pa))
            <= 1e-10,
            "Independent scalar cross-evaluation fails",
        )
        expected = {
            "known_optimum": known,
            "python_best": pyvalue,
            "r_best": rvalue,
            "python_gap": pyvalue - known,
            "r_gap": rvalue - known,
            "python_at_r_gap": pb - rvalue,
            "r_at_python_gap": float(r["r_at_python"]) - pyvalue,
        }
        require(
            all(abs(float(sm[k]) - v) <= 1e-10 for k, v in expected.items()),
            "Retained summary does not match independent scalar values",
        )
        require(
            sm["python_success"] == "True" and int(sm["r_iterations"]) == 400,
            "Summary status differs",
        )
        checks.append(
            {
                "case": case["name"],
                "independent_scalar_python": pa,
                "independent_scalar_R": pb,
                "known_optimum": known,
                "R_iteration_cap_not_convergence": True,
            }
        )
    return {
        "ordered_cases": 3,
        "cases": checks,
        "cross_evaluation_threshold": 1e-10,
        "optimum_gap_threshold": 1e-4,
        "scientific_acceptance": "not_evaluated",
    }


def check_paired(
    python: list[dict[str, str]],
    native: list[dict[str, str]],
    draws: dict[str, Any],
    setup: dict[str, Any],
) -> dict[str, Any]:
    require(len(python) == len(native) == 400, "Paired output membership differs")
    require(
        draws["schema_version"] == "paired-love-draws.1"
        and draws["valid_ring_positions"] == [8, 9, 10]
        and len(draws["taxa"]) == 10,
        "Paired draw contract differs",
    )
    require(setup["pollen_columns"][1:] == draws["taxa"], "Setup/taxon order differs")
    expected = [
        (field, str(ring), taxon)
        for field in ["Mean", "Q10", "Q90", "SD"]
        for ring in range(1, 11)
        for taxon in draws["taxa"]
    ]
    finite = missing = 0
    maximum = 0.0
    for py, r, identity in zip(python, native, expected, strict=True):
        require(
            tuple(py[k] for k in ["field", "ring", "taxon"])
            == tuple(r[k] for k in ["field", "ring", "taxon"])
            == identity,
            "Paired ordered identity differs",
        )
        a, b = py["value"], r["value"]
        if a == "" or b == "":
            require(
                a == b == "" and int(identity[1]) not in [8, 9, 10],
                "Paired missing-mask differs",
            )
            missing += 1
        else:
            x, y = float(a), float(b)
            require(
                math.isfinite(x)
                and math.isfinite(y)
                and int(identity[1]) in [8, 9, 10],
                "Nonfinite or invalid-ring value",
            )
            error = abs(x - y)
            require(error <= 3e-10, "Prospective paired tolerance failed")
            maximum = max(maximum, error)
            finite += 1
    require((finite, missing) == (120, 280), "Finite/missing denominator differs")
    require(
        len(draws["regional_cover"]) == 10
        and abs(sum(draws["regional_cover"]) - 0.99999) <= 1e-14,
        "Rounded regional vector differs",
    )
    require(
        len(draws["local_ppe"]) == len(draws["local_counts"]) == 2,
        "Explicit repetition count differs",
    )
    total = sum(setup["local"][1:])
    for ppe, counts in zip(draws["local_ppe"], draws["local_counts"], strict=True):
        require(len(ppe) == len(counts) == 10, "Explicit ring count differs")
        for ps, cs in zip(ppe, counts, strict=True):
            require(
                len(ps) == len(cs) == 10
                and all(
                    type(x) in [int, float] and math.isfinite(x) and x > 0 for x in ps
                ),
                "PPE shape/domain differs",
            )
            require(
                all(type(x) is int and x >= 0 for x in cs) and sum(cs) == total,
                "Explicit counts/total differ",
            )
    return {
        "paired_finite_values": finite,
        "paired_missing_values": missing,
        "maximum_absolute_difference": maximum,
        "prospective_absolute_tolerance": 3e-10,
        "same_seed_trajectory_claim": False,
        "scientific_acceptance": "not_evaluated",
    }
