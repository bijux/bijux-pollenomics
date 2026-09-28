"""Bind author-harmonized Swedish pollen targets to the author REVEALS inputs."""

from __future__ import annotations

import argparse
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .neotoma_parameter_mass import _identity

MASS = Path("docs/report/source-relations/neotoma/author-taxonomy-mass/report.json")
PARAMETERS = Path("author/run.REVEALS.files/av-RPP.all.landclimII.csv")
COVARIANCE = Path("author/run.REVEALS.files/avar-RPP.all.landclimII.csv")
AUTHOR_SCRIPT = Path("author/Kunes_REVEALS_iterate_across_sitelists.R")
SOURCE_HASHES = {
    PARAMETERS: "066ebadbe6ab10aead80c74a184284e05b9db3cd1f5daff04249596170a663e2",
    COVARIANCE: "8821de94682c454e3a751897b487c8bf1612cf60994dc6246fb33284a73e9918",
    AUTHOR_SCRIPT: "bc20b58bc1dc5933eb046233d44739d7da006624031aa4863e9a2731b077e341",
}


def _source_identity(root: Path, relative: Path) -> dict[str, object]:
    raw = (root / relative).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if digest != SOURCE_HASHES[relative]:
        raise ValueError(f"LandClim author input changed: {relative}")
    return {"path": relative.as_posix(), "bytes": len(raw), "sha256": digest}


def publish(repository: Path, author_source_root: Path, output: Path) -> dict[str, Any]:
    """Resolve the exact author source profile; leave basin admission untouched."""
    repository = repository.resolve()
    author_source_root = author_source_root.resolve()
    source_inputs = [
        _source_identity(author_source_root, path) for path in SOURCE_HASHES
    ]
    mass_path = repository / MASS
    mass = json.loads(mass_path.read_text(encoding="utf-8"))
    if (
        mass["schema_version"] != "swedish-neotoma-landclim-author-taxonomy-mass.v1"
        or mass["site_count"] != 3
        or mass["common_bin_count"] != 39
        or mass["lra_admitted_samples"] != 0
        or mass["scientific_admission_allowed"] is not False
    ):
        raise ValueError("Author taxonomy mass scope changed")

    with (author_source_root / PARAMETERS).open(encoding="utf-8", newline="") as handle:
        parameters = list(csv.DictReader(handle))
    with (author_source_root / COVARIANCE).open(encoding="utf-8", newline="") as handle:
        covariance = list(csv.DictReader(handle))
    names = [row["A.series"] for row in parameters]
    if (
        len(names) != 31
        or len(set(names)) != 31
        or names != [row["A.series"] for row in covariance]
        or names != list(covariance[0])[1:]
        or set(parameters[0]) != {"A.series", "alpha", "vg"}
    ):
        raise ValueError("Author parameter and covariance targets disagree")
    counts: Counter[str] = Counter()
    all_native = author_assigned = 0
    for site in mass["sites"]:
        targets = site["author_target_counts"]
        if sum(targets.values()) != site["author_assigned_nisp"]:
            raise ValueError("Author target counts do not close")
        counts.update(targets)
        all_native += site["all_native_nisp"]
        author_assigned += site["author_assigned_nisp"]
    if set(counts) - set(names) or sum(counts.values()) != author_assigned:
        raise ValueError("Author lookup has targets outside the parameter source")

    rows: list[dict[str, object]] = []
    nonzero_offdiagonal = 0
    for index, (name, parameter) in enumerate(zip(names, parameters, strict=True)):
        alpha = float(parameter["alpha"])
        vg = float(parameter["vg"])
        variance = float(covariance[index][name])
        if not all(math.isfinite(value) for value in (alpha, vg, variance)):
            raise ValueError("Nonfinite author model parameter")
        if alpha <= 0 or vg <= 0 or variance < 0:
            raise ValueError("Invalid author model parameter")
        for column in names:
            entry = float(covariance[index][column])
            if not math.isfinite(entry) or entry != float(
                covariance[names.index(column)][name]
            ):
                raise ValueError("Invalid author covariance matrix")
            if column != name and entry != 0:
                nonzero_offdiagonal += 1
        rows.append(
            {
                "author_target": name,
                "alpha_source_text": parameter["alpha"],
                "fall_speed_source_text": parameter["vg"],
                "alpha_variance_source_text": covariance[index][name],
                "swedish_native_nisp_assigned": counts[name],
            }
        )
    report: dict[str, Any] = {
        "schema_version": "swedish-landclim-author-parameter-binding.v1",
        "source_role": "exact_author_lookup_target_to_author_REVEALS_parameter_binding",
        "author_target_count": 31,
        "targets_with_swedish_native_nisp": sum(counts[name] > 0 for name in names),
        "swedish_all_native_nisp": all_native,
        "swedish_author_assigned_nisp": author_assigned,
        "covariance_nonzero_offdiagonal_cells": nonzero_offdiagonal,
        "lra_admitted_samples": 0,
        "scientific_admission_allowed": False,
        "interpretation": (
            "This exact author code profile binds lookup target names to the author's "
            "alpha, fall-speed and PPE covariance inputs. It does not resolve "
            "sample-time lake geometry, source exclusions, unmapped counts, "
            "or a valid Swedish LRA sample."
        ),
        "parameters": rows,
        "inputs": [_identity(mass_path, repository), *source_inputs],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = publish(args.repository, args.author_source_root, args.output)
    print(f"{report['author_target_count']} author REVEALS parameters source-bound")


if __name__ == "__main__":
    main()
