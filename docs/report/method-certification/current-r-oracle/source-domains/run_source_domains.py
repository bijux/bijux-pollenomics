"""Independent source-domain refusals and explicitly corrected forward profile."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))

from bijux_pollenomics_lra.api import (  # noqa: E402
    DistanceWeighting,
    ForwardConfig,
    LoveConfig,
    RevealsConfig,
    ValidationError,
    forward_deposition,
    prepare_forward_inputs,
    run_love,
    run_reveals,
)


@dataclass(frozen=True)
class DomainCase:
    id: str
    kind: str
    semantics: str
    method: str = "lsm unstable"
    radius: float = 10
    count: int = 2
    mask: str = "all"
    taxa_count: int = 3
    iterations: int = 1
    cover0: float = 0.6
    cover1: float = 0.1
    cover2: float = 0.3
    cover_profile: str = "closed-fractions"


def cases() -> list[DomainCase]:
    result = [
        DomainCase(
            f"S00{n}",
            "wrapper_refusal",
            "source-wrapper-refusal",
            taxa_count=1,
            iterations=n,
        )
        for n in [1, 2]
    ]
    result += [
        DomainCase("S003", "ring_refusal", "legacy-source-refusal", count=1),
        DomainCase("S004", "ring_refusal", "legacy-source-refusal", count=3),
        DomainCase(
            "S005", "optimized", "source-supported-zero-local", mask="zero_first"
        ),
        DomainCase(
            "S006",
            "optimized",
            "source-supported-zero-regional",
            count=3,
            mask="zero_last",
        ),
        DomainCase(
            "S007",
            "optimized",
            "source-supported-supplied-regional",
            taxa_count=1,
            count=1,
        ),
    ]
    result += [
        DomainCase(
            f"S{8 + i:03}",
            "analytical",
            "source-supported-supplied-regional",
            count=n,
            taxa_count=1,
        )
        for i, n in enumerate([1, 3, 4])
    ]
    for method in DistanceWeighting:
        for radius in [10.0, 40.0]:
            result.append(
                DomainCase(
                    f"F{len(result) - 9:03}",
                    "forward",
                    "corrected-matrix-forward",
                    method=method.value,
                    radius=radius,
                )
            )
    result += [
        DomainCase("F011", "forward", "corrected-matrix-single-local", count=1),
        DomainCase("F012", "forward", "corrected-matrix-single-regional", count=3),
        DomainCase(
            "F013",
            "forward",
            "corrected-matrix-rounded-cover",
            cover0=0.33333,
            cover1=0.33333,
            cover2=0.33333,
            cover_profile="disqover-rounded-fractions",
        ),
    ]
    return result


def parameters() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Taxon": ["Alnus", "Betula", "Pinus"],
            "fallspeed": [0.024, 0.035, 0.06],
            "ppe": [0.7, 2.2, 5.5],
            "ppe.error": [0.0, 0.0, 0.0],
        }
    )


def geometry(case: DomainCase) -> pd.DataFrame:
    edges = np.array(
        [case.radius, 3 * case.radius, 10 * case.radius, 50 * case.radius, 100000.0]
    )
    area = np.pi * np.diff(edges**2)
    fractions = np.array([1.0, 0.7, 0.9, 0.6])
    if case.mask in {"zero_first", "zero_last"}:
        fractions[0] = 0
    if case.mask == "zero_last":
        fractions[-1] = 0
    return pd.DataFrame(
        {
            "no": np.arange(1, len(edges)),
            "inner": edges[:-1],
            "outer": edges[1:],
            "mean": (edges[:-1] + edges[1:]) / 2,
            "ring": area,
            "terrestrial": area * fractions,
        }
    )


def expectation(case: DomainCase) -> np.ndarray:
    p = parameters().iloc[: case.taxa_count]
    rings = geometry(case)
    local = pd.DataFrame(
        {"coordinate": [1], "Alnus": [30], "Betula": [50], "Pinus": [20]}
    ).iloc[:, : case.taxa_count + 1]
    regional = pd.DataFrame(
        {"coordinate": [1], "Alnus": [60], "Betula": [10], "Pinus": [30]}
    ).iloc[:, : case.taxa_count + 1]
    if case.kind == "wrapper_refusal":
        try:
            run_reveals(
                regional,
                p,
                RevealsConfig(
                    "lake", 300, iterations=case.iterations, stochastic=False
                ),
            )
        except ValidationError as exc:
            if exc.reason_code == "unsupported_source_taxon_dimensions":
                return np.array([1.0])
            raise
        raise AssertionError("Source wrapper domain was unexpectedly admitted")
    if case.kind == "forward":
        prepared = prepare_forward_inputs(
            p,
            rings,
            [case.cover0, case.cover1, case.cover2],
            ForwardConfig(
                case.count,
                2 * case.radius,
                distance_weighting=case.method,
                regional_cover_profile=case.cover_profile,
            ),
        )
        prediction = forward_deposition(
            [0.2, 0.5, 0.3],
            prepared.regional_deposition,
            prepared.local_k,
            prepared.terrestrial_fraction,
            prepared.ppe,
        )
        return np.concatenate(
            [
                prepared.full_k.ravel(order="F"),
                prepared.regional_deposition,
                prediction.pollen_fraction,
            ]
        )
    repeats = 2 if case.kind == "analytical" else 1
    config = LoveConfig(
        method="analytical" if case.kind == "analytical" else "optimized",
        regional_basin_type="lake",
        regional_basin_diameter_m=300,
        local_basin_diameter_m=12,
        max_ring=case.count,
        repeats=repeats,
        stochastic=False,
    )
    candidates = (
        np.ones((1, 1))
        if case.taxa_count == 1
        else np.array([[0.2, 0.5, 0.3], [0.6, 0.1, 0.3], [0.25, 0.25, 0.5]])
    )
    try:
        result = run_love(
            local,
            regional,
            p,
            rings,
            config,
            replay_candidates=candidates if case.kind != "analytical" else None,
            regional_cover_draws=np.ones((repeats, 1))
            if case.taxa_count == 1
            else None,
        )
    except ValidationError as exc:
        if (
            case.kind == "ring_refusal"
            and exc.reason_code == "unsupported_source_ring_dimensions"
        ):
            return np.array([1.0])
        raise
    if case.kind == "ring_refusal":
        raise AssertionError("Legacy source ring dimensions unexpectedly admitted")
    second = (
        result.cover["sd"]
        if case.kind == "analytical"
        else result.pollen_percentages["mean"]
    )
    return np.concatenate(
        [
            result.cover["mean"].to_numpy().ravel(order="F"),
            second.to_numpy().ravel(order="F"),
        ]
    )


def _save(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--library", type=Path, default=ROOT / ".r-library")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=180)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    specs = cases()
    expected = {case.id: expectation(case) for case in specs}
    pd.DataFrame([asdict(case) for case in specs]).to_csv(
        output / "case_manifest.csv", index=False
    )
    _save(output / "case_manifest.json", [asdict(case) for case in specs])
    parameters().to_csv(output / "parameters.csv", index=False)
    for case in specs:
        geometry(case).to_csv(output / f"{case.id}-rings.csv", index=False)
    expected_directory = output / "python_expected_not_R_goldens"
    expected_directory.mkdir(exist_ok=True)
    for case_id, values in expected.items():
        np.save(expected_directory / f"{case_id}.npy", values, allow_pickle=False)
    retained_sources = {}
    for name in ["run_source_domains.py", "source_domains.R", "r_support.R"]:
        source = Path(__file__).with_name(name)
        content = source.read_bytes()
        (output / name).write_bytes(content)
        retained_sources[name] = hashlib.sha256(content).hexdigest()
    archive_hash = hashlib.sha256(
        (ROOT / "vendor/disqover_0.9.14.tar.gz").read_bytes()
    ).hexdigest()
    report: dict[str, object] = {
        "schema_version": "1.0.0",
        "profile": "disqover-source-domains-and-corrected-forward-v1",
        "retained_source_sha256": retained_sources,
        "source_version": "0.9.14",
        "source_archive_sha256": archive_hash,
        "prepared_cases": len(specs),
        "live_R_executed": False,
        "passed_cases": 0,
        "failed_cases": 0,
        "status": "prepared_not_executed",
        "scope": "Separate from the core 25-case oracle; no convergence or ecological acceptance claim",
    }
    _save(output / "report.json", report)
    if args.prepare_only:
        return 0
    if not shutil.which("Rscript"):
        report.update(status="blocked", reason="Rscript unavailable")
        _save(output / "report.json", report)
        return 2
    command = [
        "Rscript",
        "--vanilla",
        str(output / "source_domains.R"),
        str(output),
        str(args.library.resolve()),
        str(output / "r_support.R"),
        archive_hash,
    ]
    _save(output / "command.json", command)
    try:
        completed = subprocess.run(
            command, capture_output=True, text=True, timeout=args.timeout, check=False
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        report.update(status="blocked", reason=str(exc))
        _save(output / "report.json", report)
        return 2
    (output / "R_stdout.log").write_text(completed.stdout)
    (output / "R_stderr.log").write_text(completed.stderr)
    report["live_R_executed"] = True
    report["r_exit_code"] = completed.returncode
    if completed.returncode:
        report.update(
            status="blocked",
            reason="Reference setup or execution failed",
            r_exit_code=completed.returncode,
        )
        _save(output / "report.json", report)
        return 2
    comparisons = []
    for case in specs:
        actual = pd.read_csv(output / f"{case.id}-R.csv")["value"].to_numpy(float)
        target = expected[case.id]
        passed = actual.shape == target.shape and bool(
            np.allclose(actual, target, rtol=1e-10, atol=3e-10, equal_nan=True)
        )
        comparisons.append(
            {
                "id": case.id,
                "semantics": case.semantics,
                "passed": passed,
                "values": len(target),
            }
        )
    passed_count = sum(bool(row["passed"]) for row in comparisons)
    report.update(
        status="passed" if passed_count == len(specs) else "failed",
        passed_cases=passed_count,
        failed_cases=len(specs) - passed_count,
        cases=comparisons,
    )
    _save(output / "report.json", report)
    return 0 if passed_count == len(specs) else 1


if __name__ == "__main__":
    raise SystemExit(main())
