"""Compare bounded static basin alternatives without claiming vegetation accuracy."""

from __future__ import annotations

import argparse
from dataclasses import asdict
import json
from math import isfinite
from pathlib import Path
import subprocess
from typing import Any

from bijux_pollenomics.analysis.lra.api import LRARefusal
from bijux_pollenomics_dev.ci.report_rebuild.artifact_paths import (
    require_absent_artifact_output,
)

from .calculation import calculate, extract
from .inputs import BASIN_SOURCES, load_inputs, materialize
from .protocol import profiles


def compare_profiles(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Use the full pairwise range, retaining undefined and clipped-away variation."""
    expected = {profile.name for profile in profiles()}
    if len(rows) != 3 or {row["profile"] for row in rows} != expected:
        raise ValueError("Exactly the three declared profiles required")
    refused = [row["profile"] for row in rows if row["status"] != "generated"]
    if refused:
        return {
            "status": "unavailable_refused_profile",
            "within_tolerance": None,
            "refused_profiles": refused,
        }
    spans = {}
    for name in ("signed_cover", "clipped_cover"):
        for row in rows:
            value = row[name]
            if (
                len(value) != 2
                or any(len(ring) != 2 for ring in value)
                or not all(isfinite(x) for ring in value for x in ring)
            ):
                raise ValueError("Complete finite two-ring/two-taxon covers required")
            if name == "clipped_cover" and any(
                any(x < 0 or x > 1 for x in ring) or abs(sum(ring) - 1) > 1e-12
                for ring in value
            ):
                raise ValueError("Closed physically bounded clipped covers required")
        spans[name] = [
            [
                100
                * (
                    max(row[name][r][t] for row in rows)
                    - min(row[name][r][t] for row in rows)
                )
                for t in range(2)
            ]
            for r in range(2)
        ]
    clipped = spans["clipped_cover"]
    signed = spans["signed_cover"]
    return {
        "status": "defined_conditional_sensitivity",
        "clipped_span_pp": clipped,
        "signed_span_pp": signed,
        "tolerance_percentage_points": 10,
        "within_tolerance": all(x <= 10 + 1e-12 for ring in clipped for x in ring),
        "clipping_masks_larger_span": any(
            signed[r][t] > clipped[r][t] + 1e-12 for r in range(2) for t in range(2)
        ),
        "scope": "Pairwise profile sensitivity on a two-taxon composition; not cover accuracy or field acceptance",
    }


def _frozen(repository: Path, source_sha: str) -> str:
    git = ["git", "-C", str(repository)]
    head = subprocess.check_output([*git, "rev-parse", "HEAD"], text=True).strip()
    if head != source_sha:
        raise ValueError("Frozen source revision differs")
    files = [
        str(p.relative_to(repository))
        for p in Path(__file__).absolute().parent.glob("*.py")
    ]
    files.append(str(BASIN_SOURCES))
    try:
        subprocess.run(
            [*git, "ls-files", "--error-unmatch", "--", *files],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                *git,
                "diff",
                "--exit-code",
                head,
                "--",
                *files,
                "packages/bijux-pollenomics/src/bijux_pollenomics/analysis/lra",
                "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra",
                "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/author_lra_development.py",
                "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/essd_reproduction/nordic_coupled/workflow.py",
            ],
            check=True,
            capture_output=True,
        )
    except subprocess.CalledProcessError as error:
        raise ValueError("Committed unchanged source required") from error
    return head


def run(repository: Path, output: Path, *, source_sha: str) -> dict[str, Any]:
    """Execute only after the parent freezes committed source; preserve every profile."""
    repository = repository.absolute()
    _frozen(repository, source_sha)
    output = require_absent_artifact_output(repository, output)
    inputs = load_inputs(repository)
    output.mkdir()
    result: dict[str, Any] = {
        "schema_version": "bokesjon-static-basin-sensitivity.v1",
        "source_commit": source_sha,
        "source_pins": list(inputs.source_pins),
        "scientific_acceptance": "not_evaluated",
        "question": "Conditional local basin-size sensitivity at2700–3200calBP; no historical geometry or vegetation accuracy",
        "taxa": ["Betula", "Ulmus"],
        "profiles": [],
    }
    for profile in inputs.profiles:
        directory = output / profile.name
        directory.mkdir()
        request = materialize(inputs, profile, directory / "inputs")
        (directory / "request.json").write_text(
            json.dumps(request, indent=2, allow_nan=False) + "\n"
        )
        try:
            row = calculate(request, directory / "inputs", directory / "native")
        except LRARefusal as error:
            row = error.as_dict()
        row.update(
            profile=profile.name, geometry=asdict(profile), rings=request["rings"]
        )
        result["profiles"].append(row)
        (output / "result.json").write_text(
            json.dumps(result, indent=2, allow_nan=False) + "\n"
        )
    baseline = next(
        row for row in result["profiles"] if row["profile"] == "metadata_80_m"
    )
    original = extract(inputs.directory)
    result["baseline_exact_match"] = baseline["status"] == "generated" and all(
        baseline[key] == value for key, value in original.items()
    )
    result["comparison"] = compare_profiles(result["profiles"])
    _frozen(repository, source_sha)
    load_inputs(repository)
    (output / "result.json").write_text(
        json.dumps(result, indent=2, allow_nan=False) + "\n"
    )
    if not result["baseline_exact_match"]:
        raise ValueError(
            "Saved nominal BOKE baseline differs; sensitivity is not qualified"
        )
    return result


def main() -> None:
    """Run the bounded study into a new owned artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--source-sha", required=True)
    args = parser.parse_args()
    run(args.repository, args.output, source_sha=args.source_sha)


if __name__ == "__main__":
    main()
