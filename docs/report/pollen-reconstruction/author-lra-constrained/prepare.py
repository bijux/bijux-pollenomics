"""Prepare a closed author taxon composition for constrained LOVE folds."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def prepare(source: Path, destination: Path) -> dict[str, object]:
    """Copy one hash-verified source scope and declare its excluded count mass."""
    source, destination = source.resolve(), destination.resolve()
    if destination.exists() or destination.is_symlink():
        raise ValueError("Absent output destination required")
    original = json.loads((source / "experiment.json").read_text())
    spec = SourceExperimentSpec(original)
    report = json.loads((source / "source-report.json").read_text())
    if report["experiment_sha256"] != _hash(source / "experiment.json"):
        raise ValueError("Author source experiment identity changed")
    references = [(site.raw.path, site.raw.sha256) for site in spec.sites]
    references.extend((site.geometry.path, site.geometry.sha256) for site in spec.sites)
    references.extend(
        (row["path"], row["sha256"]) for row in original["request_template"]["evidence"]
    )
    for path, digest in references:
        if _hash(source / path) != digest:
            raise ValueError(f"Source reference changed: {path}")
    taxa = original["request_template"]["taxa"]
    if len(taxa) != 31 or taxa[15] != "Filipendula":
        raise ValueError("The author taxon axis changed")
    shutil.copytree(source, destination)
    excluded = total = 0
    for site in original["sites"]:
        raw_path = destination / site["raw"]["path"]
        raw = json.loads(raw_path.read_text())
        counts = raw["sample"]["counts"]
        total += sum(counts)
        excluded += counts.pop(15)
        raw["taxa"].pop(15)
        _write(raw_path, raw)
        site["raw"]["sha256"] = _hash(raw_path)

        geometry_path = destination / site["geometry"]["path"]
        geometry = json.loads(geometry_path.read_text())
        if len(geometry["inversion_rings"]) != 2 or (
            geometry["forward_rings"][2]["inner_m"],
            geometry["forward_rings"][2]["outer_m"],
        ) != (1000, 10000):
            raise ValueError(
                "The regional annulus differs from declared source geometry"
            )
        geometry["inversion_rings"].append(geometry["forward_rings"][2])
        _write(geometry_path, geometry)
        site["geometry"]["sha256"] = _hash(geometry_path)
    if (excluded, total) != (159, 20732):
        raise ValueError("The author count denominator changed")

    template = original["request_template"]
    template["taxa"].pop(15)
    template["parameters"].pop(15)
    template["method_profile"] = "ring-taxon-preserving"
    for method in ("love", "reveals"):
        template["configuration"][method]["fall_speed_profile"] = (
            "disqover-0.9.14-wrapper-v1"
        )
    template["configuration"]["love"].update(
        method="optimized",
        optimized_profile="ring-taxon-preserving",
        optimizer_backend="scipy.slsqp-simplex-uniform",
        optimizer_iterations=300,
        optimizer_max_evaluations=16000,
        optimizer_tolerance=1e-8,
        repeats=1,
    )
    taxonomy_path = destination / "taxa.json"
    taxonomy = json.loads(taxonomy_path.read_text())
    taxonomy["prepared_taxa"].pop(15)
    taxonomy["excluded_taxon"] = "Filipendula"
    taxonomy["excluded_nisp"] = excluded
    taxonomy["original_nisp"] = total
    _write(taxonomy_path, taxonomy)
    decision_path = destination / "decision.json"
    decision = json.loads(decision_path.read_text())
    decision["constrained_love_design"] = {
        "study": "prior-exposed author English development",
        "closed_taxon_axis": "30 of 31 author targets; Filipendula excluded",
        "optimizer": "uniform-start SLSQP simplex; 300 iterations; 16000 evaluations; ftol 1e-8",
        "evidence_limit": "fold-specific LRA-derived vegetation, not independent measured vegetation",
    }
    _write(decision_path, decision)
    for evidence in template["evidence"]:
        evidence["sha256"] = _hash(destination / evidence["path"])
    SourceExperimentSpec(original)
    _write(destination / "experiment.json", original)
    report.update(
        experiment_sha256=_hash(destination / "experiment.json"),
        closed_taxon_count=30,
        excluded_taxon="Filipendula",
        excluded_taxon_nisp=excluded,
        original_count_denominator=total,
        optimizer_backend="scipy.slsqp-simplex-uniform",
    )
    _write(destination / "source-report.json", report)
    return {
        "source_manifest_sha256": report["source_manifest_sha256"],
        "experiment_sha256": report["experiment_sha256"],
        "eligible_sites": len(spec.sites),
        "excluded_nisp": excluded,
        "original_nisp": total,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.source, args.destination), sort_keys=True))


if __name__ == "__main__":
    main()
