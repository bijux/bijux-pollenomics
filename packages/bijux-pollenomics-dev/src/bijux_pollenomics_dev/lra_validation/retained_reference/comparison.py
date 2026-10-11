"""Compare current calculations with the authenticated 43-core/23-domain reference."""

from __future__ import annotations

from dataclasses import asdict
import importlib
from importlib import metadata
import io
import json
from pathlib import Path
import stat
import sys
from typing import Any

import numpy as np
import pandas as pd

from bijux_pollenomics_dev.lra_validation.reference_replay import (
    comparison_outcome,
    normalize_r_numbers,
)
from bijux_pollenomics_dev.source_completion.publication.json_outputs import (
    publish_json_outputs,
)

from .identity import authenticate_bundle, read_member
from .sources import capture_sources, require_unchanged_sources


def _json(bundle: Path, name: str, identity: dict[str, Any]) -> Any:
    return json.loads(read_member(bundle, name, identity))


def read_vector(
    bundle: Path, name: str, identity: dict[str, Any], *, numeric: bool
) -> np.ndarray:
    """Preserve explicit numeric nonfinite values and character coordinates."""
    raw = pd.read_csv(
        io.BytesIO(read_member(bundle, name, identity)),
        dtype=str,
        keep_default_na=False,
    )
    if set(raw.columns) not in ({"kind", "value"}, {"value"}):
        raise ValueError("Retained vector columns differ")
    if "kind" in raw and set(raw["kind"]) != {"numeric" if numeric else "character"}:
        raise ValueError("Retained vector value kind differs")
    if not numeric:
        return raw["value"].to_numpy(str)
    return pd.to_numeric(
        raw["value"].replace({"NaN": np.nan, "NA": np.nan}), errors="raise"
    ).to_numpy(float)


def compare_core_case(
    row: dict[str, Any], case: Any, retained: np.ndarray
) -> dict[str, Any]:
    """Refuse input/tolerance/coordinate drift before evaluating numerical agreement."""
    if (
        any(
            row[key] != getattr(case, key)
            for key in ("name", "api", "mode", "rtol", "atol")
        )
        or row["exact_indices"] != list(case.exact_indices)
        or case.expected.ndim != 1
        or row["values"] != case.expected.size
        or retained.shape != case.expected.shape
    ):
        raise ValueError("Current core case contract differs from retained reference")
    return {
        "profile": (
            "prospective-optimized-love"
            if case.mode.startswith("prospective_")
            else "source-compatible-core"
        ),
        "id": row["id"],
        "name": case.name,
        "api": case.api,
        "mode": case.mode,
        "rtol": case.rtol,
        "atol": case.atol,
        **comparison_outcome(
            case.expected,
            retained,
            rtol=case.rtol,
            atol=case.atol,
            exact_indices=case.exact_indices,
        ),
    }


def require_core_population(manifest: list[dict[str, Any]], cases: list[Any]) -> None:
    """Require all source-compatible and prospective cases exactly once."""
    if (
        len(manifest) != 43
        or len(cases) != 43
        or {row["id"] for row in manifest} != {f"C{index:04d}" for index in range(43)}
        or len({row["name"] for row in manifest}) != 43
        or {row["name"] for row in manifest} != {case.name for case in cases}
    ):
        raise ValueError("Exact 43-core case identity population differs")


def contains_statement(statement: str, script: str) -> bool:
    """Require complete expression boundaries, including multi-line case blocks."""
    return ("\n" + normalize_r_numbers(statement) + "\n") in (
        "\n" + normalize_r_numbers(script) + "\n"
    )


def require_fixture_sources(current: dict[str, str], original: dict[str, str]) -> None:
    """Freeze original shared fixture observations separately from mutable arithmetic."""
    prefix = "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/"
    current_fixture = {
        key: value for key, value in current.items() if key.startswith(prefix)
    }
    original_fixture = {
        key: value for key, value in original.items() if key.startswith(prefix)
    }
    if not current_fixture or current_fixture != original_fixture:
        raise ValueError("Current shared oracle fixture source differs from original R")


def require_domain_parameters(retained: pd.DataFrame, current: pd.DataFrame) -> None:
    """Require exact shared domain labels and PPE/fall-speed parameter values."""
    if (
        list(retained.columns) != list(current.columns)
        or retained.shape != current.shape
    ):
        raise ValueError("Current shared domain parameter table shape differs")
    np.testing.assert_array_equal(retained.to_numpy(), current.to_numpy())


def require_shared_setup(setup: list[str], script: str) -> list[str]:
    """Authenticate every supplied setup expression instead of dropping missing inputs."""
    names = []
    for statement in setup:
        name = statement.split(" <-", 1)[0]
        if not contains_statement(statement, script):
            raise ValueError("Current shared R setup differs: " + name)
        names.append(name)
    return names


def compare_domain_case(
    case: Any,
    retained: np.ndarray,
    expected: np.ndarray,
    retained_rings: pd.DataFrame,
    expected_rings: pd.DataFrame,
) -> dict[str, Any]:
    """Keep source refusals, corrected forward geometry and vector shapes explicit."""
    if (
        list(retained_rings.columns) != list(expected_rings.columns)
        or retained_rings.shape != expected_rings.shape
        or retained.shape != expected.shape
        or expected.ndim != 1
    ):
        raise ValueError("Current source-domain geometry or vector shape differs")
    np.testing.assert_allclose(
        retained_rings.to_numpy(float),
        expected_rings.to_numpy(float),
        rtol=1e-14,
        atol=1e-10,
    )
    return {
        "profile": "source-domains-and-corrected-forward",
        "id": case.id,
        "semantics": case.semantics,
        "kind": case.kind,
        "rtol": 1e-10,
        "atol": 3e-10,
        **comparison_outcome(
            expected,
            retained,
            rtol=1e-10,
            atol=3e-10,
            exact_indices=tuple(range(len(expected)))
            if case.kind in {"wrapper_refusal", "ring_refusal"}
            else (),
        ),
    }


def replay(repository: Path, bundle: Path, output: Path) -> dict[str, Any]:
    """Publish current correspondence while keeping original R provenance independent."""
    repository = repository.resolve(strict=True)
    bundle = bundle.absolute()
    output = output.absolute()
    if (
        any(path.is_symlink() for path in (output, *output.parents))
        or output.exists()
        or output.is_symlink()
        or output.resolve(strict=False).is_relative_to(bundle.resolve(strict=True))
        or not output.resolve(strict=False).is_relative_to(repository / "artifacts")
    ):
        raise ValueError("Absent repository artifact output required")
    importlib.import_module("bijux_pollenomics_lra.api")
    sources = capture_sources(repository)
    identity = authenticate_bundle(bundle)
    certificate = _json(bundle, "certificate.json", identity)
    require_fixture_sources(
        sources["canonical_replay_inputs_sha256"], certificate["source_files"]
    )
    reference = repository / "packages/bijux-pollenomics-lra/tests/reference"
    output.mkdir(parents=True)
    output_stat = output.stat()
    output_identity = output_stat.st_dev, output_stat.st_ino
    sys.path.insert(0, str(reference))
    try:
        core = importlib.import_module("lra_oracle.cases")
        domains = importlib.import_module("lra_oracle.run_source_domains")
        setup, cases = core.build_cases(output / "inputs")
        manifest = _json(bundle, "oracle/case_manifest.json", identity)
        require_core_population(manifest, cases)
        script = read_member(bundle, "oracle/oracle.R", identity).decode()
        shared_setup = require_shared_setup(setup, script)
        by_name = {case.name: case for case in cases}
        results = []
        for row in manifest:
            case = by_name[row["name"]]
            expression = (
                f"run_case({core.r_literal(row['id'])},quote({case.expression}))"
            )
            if not contains_statement(expression, script):
                raise ValueError("Current R input expression differs: " + row["id"])
            retained = read_vector(
                bundle,
                f"oracle/{row['id']}.csv",
                identity,
                numeric=case.expected.dtype.kind not in "USO",
            )
            results.append(compare_core_case(row, case, retained))
        domain_manifest = _json(bundle, "source-domains/case_manifest.json", identity)
        specs = domains.cases()
        require_domain_parameters(
            pd.read_csv(
                io.BytesIO(
                    read_member(bundle, "source-domains/parameters.csv", identity)
                )
            ),
            domains.parameters(),
        )
        if len(specs) != 23 or [asdict(case) for case in specs] != domain_manifest:
            raise ValueError("Exact 23-domain shared input population differs")
        for spec in specs:
            rings = pd.read_csv(
                io.BytesIO(
                    read_member(bundle, f"source-domains/{spec.id}-rings.csv", identity)
                )
            )
            retained = read_vector(
                bundle, f"source-domains/{spec.id}-R.csv", identity, numeric=True
            )
            results.append(
                compare_domain_case(
                    spec,
                    retained,
                    domains.expectation(spec),
                    rings,
                    domains.geometry(spec),
                )
            )
    finally:
        sys.path.remove(str(reference))
    sources = require_unchanged_sources(repository, sources)
    if authenticate_bundle(bundle) != identity:
        raise ValueError("Retained reference identity changed after comparison")
    certificate = _json(bundle, "certificate.json", identity)
    original_sources = certificate["source_files"]
    current = sources["canonical_replay_inputs_sha256"]
    passed = sum(row["status"] == "passed" for row in results)
    report = {
        "schema_version": "source-locked-retained-r-python-comparison.v1",
        "status": "passed" if passed == 66 else "failed",
        "reference": identity,
        "current_sources": sources,
        "matching_reference_source_paths": sorted(
            path
            for path, value in current.items()
            if original_sources.get(path) == value
        ),
        "changed_reference_source_paths": sorted(
            path
            for path, value in current.items()
            if original_sources.get(path) != value
        ),
        "cases": results,
        "matched_shared_setup": shared_setup,
        "attempted_cases": 66,
        "evaluated_cases": len(results),
        "passed_cases": passed,
        "failed_cases": len(results) - passed,
        "refused_cases": 0,
        "fresh_R_executed": False,
        "original_R_executed": True,
        "scientific_admission_allowed": False,
        "release_certificate": False,
        "runtime": {"python": sys.version, "executable": sys.executable},
        "runtime_dependencies": {
            name: metadata.version(name)
            for name in (
                "bijux-pollenomics-repository",
                "bijux-pollenomics-dev",
                "bijux-pollenomics",
                "bijux-pollenomics-lra",
                "pollenomics",
                "numpy",
                "scipy",
                "pandas",
            )
        },
    }
    require_unchanged_sources(repository, sources)
    if authenticate_bundle(bundle) != identity:
        raise ValueError("Retained reference identity changed before publication")
    final_output_stat = output.lstat()
    if (
        not stat.S_ISDIR(final_output_stat.st_mode)
        or (final_output_stat.st_dev, final_output_stat.st_ino) != output_identity
        or any(path.is_symlink() for path in (output, *output.parents))
        or not output.resolve(strict=True).is_relative_to(repository / "artifacts")
    ):
        raise ValueError("Retained comparison output directory changed")
    publish_json_outputs([(output / "report.json", report)])
    return report
