"""Replay current Python calculations against authenticated retained R vectors."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import hashlib
import importlib
from importlib import metadata
import json
from pathlib import Path
import re
import sys
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_dev.ci.lra_reference.evidence import validate_bundle

CERTIFICATE_SHA256 = "881c1f65b62c890fbb583c499493c21318f21857960998ca662fbb1cf2b94ae3"


def numeric_vector_values(values: pd.Series) -> np.ndarray:
    """Validate the established R lexical contract, then round original decimals."""
    # Pandas' numeric conversion can lose binary64 precision. Retain its
    # existing refusals (including underscores and overflow) as validation,
    # and obtain correctly rounded values from the original CSV tokens.
    normalized = values.mask(values.isin(["NaN", "NA"]), np.nan)
    pd.to_numeric(normalized, errors="raise")
    return np.fromiter(
        (np.nan if value in ("NaN", "NA", "") else float(value) for value in values),
        dtype=float,
        count=len(values),
    )


def normalize_r_numbers(expression: str) -> str:
    """Compare decimal and hexadecimal binary64 literals without changing strings."""
    tokens = re.compile(
        r'"(?:\\.|[^"\\])*"|(?<![\w.])(?:0x[0-9a-fA-F.]+p[+-]?\d+|\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)(?![\w.])'
    )

    def replace(match: re.Match[str]) -> str:
        token = match.group()
        if token.startswith('"'):
            return token
        value = float.fromhex(token) if token.startswith("0x") else float(token)
        return value.hex()

    return tokens.sub(replace, expression)


def compare_vectors(
    actual: np.ndarray,
    expected: np.ndarray,
    *,
    rtol: float,
    atol: float,
    exact_indices: tuple[int, ...] = (),
) -> dict[str, Any]:
    """Keep exact coordinates, nonfinite positions and approximate values distinct."""
    if actual.shape != expected.shape:
        raise AssertionError("R/Python vector dimensions differ")
    if expected.dtype.kind in "USO":
        np.testing.assert_array_equal(actual.astype(str), expected.astype(str))
        return {"values": len(expected), "max_abs_error": None}
    actual, expected = actual.astype(float), expected.astype(float)
    exact = np.asarray(exact_indices, dtype=int)
    if np.any(exact < 0) or np.any(exact >= len(expected)):
        raise AssertionError("Exact coordinate is outside vector")
    np.testing.assert_array_equal(actual[exact], expected[exact])
    approximate = np.ones(len(expected), dtype=bool)
    approximate[exact] = False
    np.testing.assert_allclose(
        actual[approximate],
        expected[approximate],
        rtol=rtol,
        atol=atol,
        equal_nan=True,
    )
    finite = np.isfinite(actual) & np.isfinite(expected)
    errors = np.abs(actual[finite] - expected[finite])
    return {
        "values": len(expected),
        "finite_values": int(finite.sum()),
        "nan_positions": np.flatnonzero(np.isnan(expected)).tolist(),
        "exact_indices": list(exact_indices),
        "max_abs_error": float(errors.max()) if errors.size else 0.0,
    }


def comparison_outcome(
    actual: np.ndarray, expected: np.ndarray, **options: Any
) -> dict[str, Any]:
    """Retain a failed comparison so it cannot erase later attempts."""
    try:
        return {**compare_vectors(actual, expected, **options), "status": "passed"}
    except AssertionError as error:
        return {"status": "failed", "reason": str(error), "values": len(expected)}


def _source_digest(path: Path, root: Path) -> str:
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError(f"Replay source symlink refused: {path}")
        current = current.parent
    if root.is_symlink() or not path.is_file():
        raise ValueError(f"Replay source must be a regular file: {path}")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_installed_replay_sources(repository: Path) -> None:
    source_root = (
        repository / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    )
    installed_replay = Path(__file__).absolute()
    installed_root = installed_replay.parent.parent
    relative_replay = Path("lra_validation/reference_replay.py")
    if _source_digest(installed_replay, installed_root) != _source_digest(
        source_root / relative_replay, source_root
    ):
        raise ValueError("Installed replay source differs from repository")
    reference_relative = Path("ci/lra_reference")
    installed_paths = {
        path.relative_to(installed_root)
        for path in (installed_root / reference_relative).rglob("*.py")
        if "__pycache__" not in path.parts
    }
    source_paths = {
        path.relative_to(source_root)
        for path in (source_root / reference_relative).rglob("*.py")
        if "__pycache__" not in path.parts
    }
    if not source_paths or installed_paths != source_paths:
        raise ValueError(
            "Installed R validator source path set differs from repository"
        )
    for relative in sorted(source_paths):
        if _source_digest(installed_root / relative, installed_root) != _source_digest(
            source_root / relative, source_root
        ):
            raise ValueError(f"Installed R validator source differs: {relative}")


def _replay_source_hashes(repository: Path) -> dict[str, str]:
    _require_installed_replay_sources(repository)
    lra = repository / "packages/bijux-pollenomics-lra/src"
    oracle = repository / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle"
    development = (
        repository / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev"
    )
    closure = sorted(
        set(lra.rglob("*.py"))
        | set(oracle.rglob("*"))
        | set(lra.rglob("*.npz"))
        | set(lra.rglob("*.json"))
        | set((development / "ci/lra_reference").rglob("*.py"))
        | {development / "lra_validation/reference_replay.py"}
    )
    return {
        path.relative_to(repository).as_posix(): _source_digest(path, repository)
        for path in closure
        if (path.is_file() or path.is_symlink()) and "__pycache__" not in path.parts
    }


def replay(repository: Path, bundle: Path, output: Path) -> dict[str, Any]:
    """Require unchanged R expressions before comparing every retained case."""
    repository, bundle, output = (p.resolve() for p in (repository, bundle, output))
    certificate_path = bundle / "certificate.json"
    if hashlib.sha256(certificate_path.read_bytes()).hexdigest() != CERTIFICATE_SHA256:
        raise ValueError("Retained R certificate differs from pinned original")
    certificate = json.loads(certificate_path.read_text())
    hashes = _replay_source_hashes(repository)
    validate_bundle(
        bundle,
        target_sha=certificate["source_commit"],
        expected_lock_sha256=certificate["lock_sha256"],
    )
    if output.exists():
        raise ValueError("Replay output must be absent")
    reference = repository / "packages/bijux-pollenomics-lra/tests/reference"
    output.mkdir(parents=True)
    sys.path.insert(0, str(reference))
    try:
        core = importlib.import_module("lra_oracle.cases")
        domains = importlib.import_module("lra_oracle.run_source_domains")
        setup, cases = core.build_cases(output / "inputs")
        script = (bundle / "oracle/oracle.R").read_text()
        normalized_script = normalize_r_numbers(script)
        shared_setup = []
        for statement in setup:
            name = statement.split(" <-", 1)[0]
            if not any(line.startswith(name + " <-") for line in script.splitlines()):
                continue
            if normalize_r_numbers(statement) not in normalized_script:
                raise ValueError(f"Current shared R setup differs: {name}")
            shared_setup.append(name)
        manifest = json.loads((bundle / "oracle/case_manifest.json").read_text())
        results = []
        by_name = {case.name: case for case in cases}
        for row in manifest:
            case = by_name[row["name"]]
            if any(
                row[k] != getattr(case, k)
                for k in ("name", "api", "mode", "rtol", "atol")
            ):
                raise ValueError("Core manifest or prospective tolerance differs")
            expression = (
                f"run_case({core.r_literal(row['id'])},quote({case.expression}))"
            )
            if normalize_r_numbers(expression) not in normalized_script:
                raise ValueError(f"Current R input expression differs: {row['id']}")
            raw = pd.read_csv(
                bundle / "oracle" / f"{row['id']}.csv", dtype=str, keep_default_na=False
            )
            actual = (
                raw["value"].to_numpy()
                if case.expected.dtype.kind in "USO"
                else numeric_vector_values(raw["value"])
            )
            results.append(
                {
                    "profile": "source-compatible-core",
                    "id": row["id"],
                    "name": case.name,
                    "api": case.api,
                    "mode": case.mode,
                    **comparison_outcome(
                        actual,
                        case.expected,
                        rtol=case.rtol,
                        atol=case.atol,
                        exact_indices=case.exact_indices,
                    ),
                }
            )
        domain_manifest = json.loads(
            (bundle / "source-domains/case_manifest.json").read_text()
        )
        specs = domains.cases()
        if [asdict(c) for c in specs] != domain_manifest:
            raise ValueError("Source-domain shared inputs differ")
        for case in specs:
            rings = pd.read_csv(bundle / "source-domains" / f"{case.id}-rings.csv")
            np.testing.assert_allclose(
                rings.to_numpy(float),
                domains.geometry(case).to_numpy(float),
                rtol=1e-14,
                atol=1e-10,
            )
            raw = pd.read_csv(
                bundle / "source-domains" / f"{case.id}-R.csv",
                dtype=str,
                keep_default_na=False,
            )
            actual = numeric_vector_values(raw["value"])
            results.append(
                {
                    "profile": "source-domains-and-corrected-forward",
                    "id": case.id,
                    "semantics": case.semantics,
                    **comparison_outcome(
                        actual, domains.expectation(case), rtol=1e-10, atol=3e-10
                    ),
                }
            )
    finally:
        sys.path.remove(str(reference))
    if _replay_source_hashes(repository) != hashes:
        raise ValueError("Replay dependency closure changed")
    missing = [
        {"name": c.name, "api": c.api, "reason": "no_result_in_original_R_bundle"}
        for c in cases
        if c.name not in {r["name"] for r in manifest}
    ]
    passed = sum(row["status"] == "passed" for row in results)
    report = {
        "schema_version": "retained-r-python-replay.1",
        "status": "passed" if passed == len(results) else "failed",
        "fresh_R_executed": False,
        "original_R_executed": True,
        "original_source_commit": certificate["source_commit"],
        "original_certificate_sha256": CERTIFICATE_SHA256,
        "source_archive_sha256": json.loads((bundle / "source-lock.json").read_text())[
            "reference"
        ]["sha256"],
        "current_inputs_sha256": hashes,
        "cases": results,
        "matched_shared_setup": shared_setup,
        "current_core_cases_without_retained_R": missing,
        "attempted_cases": len(results) + len(missing),
        "evaluated_cases": len(results),
        "passed_cases": passed,
        "failed_cases": len(results) - passed,
        "refused_cases": len(missing),
        "runtime_dependencies": {
            name: metadata.version(name) for name in ("numpy", "scipy", "pandas")
        },
        "release_certificate": False,
    }
    (output / "report.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n"
    )
    return report


def main() -> int:
    """Run the CLI to replay current Python calculations against authenticated retained R vectors."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.repository, args.bundle, args.output)
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
