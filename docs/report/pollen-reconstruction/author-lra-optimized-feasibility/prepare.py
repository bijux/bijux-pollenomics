"""Recreate source-bound author LOVE feasibility requests without retained artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from bijux_pollenomics.analysis.lra.execution.service import validate_lra_inputs
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import make_request
from bijux_pollenomics.analysis.lra_validation.splits import grouped_leave_one_out
from bijux_pollenomics_dev.essd_reproduction.author_lra_development import (
    materialize_author_lra_development,
)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True) + "\n")


def prepare(source_root: Path, output: Path) -> dict[str, object]:
    """Declare two bounded tests of a 30-taxon, prior-exposed training pair."""
    source_root, output = source_root.resolve(), output.resolve()
    if output.exists() or output.is_symlink():
        raise ValueError("Absent output destination required")
    source_inputs = materialize_author_lra_development(
        source_root, output / "source-inputs"
    )
    spec = SourceExperimentSpec(json.loads((source_inputs / "experiment.json").read_text()))
    by_site = {site.record.site_id: site for site in spec.sites}
    fold = next(
        fold
        for fold in grouped_leave_one_out([site.record for site in spec.sites])
        if "author:BROADOWN" in fold.test_record_ids
    )
    base = make_request(
        spec, by_site["LARKBARR"], by_site["BECKHAM"], fold, source_inputs
    )
    base_bytes = (json.dumps(base, sort_keys=True, separators=(",", ":")) + "\n").encode()
    if _sha(base_bytes) != "05802721173c2d8b30c042d0eca585b8c27b79dff82138aec0247611565774d5":
        raise ValueError("The source training pair differs from the retained base request")
    index = base["taxa"].index("Filipendula")
    if len(base["taxa"]) != 31 or index != 15 or base["parameters"][index]["fallspeed_m_s"] != 0.006:
        raise ValueError("The author taxon and fall-speed axis changed")
    excluded = sum(
        json.loads((source_inputs / site.raw.path).read_text())["sample"]["counts"][index]
        for site in spec.sites
    )
    total = sum(
        sum(json.loads((source_inputs / site.raw.path).read_text())["sample"]["counts"])
        for site in spec.sites
    )
    if (excluded, total) != (159, 20732):
        raise ValueError("The author source count denominator changed")
    budgets = (("initial", 40, 1000, 2), ("extended", 120, 20000, 1))
    prepared = []
    for label, iterations, evaluations, repeats in budgets:
        request = json.loads(json.dumps(base))
        input_root = output / label / "inputs"
        input_root.mkdir(parents=True)
        old_files = {}
        for evidence in request["evidence"]:
            raw = (source_inputs / evidence["path"]).read_bytes()
            if _sha(raw) != evidence["sha256"]:
                raise ValueError("The source evidence changed")
            old_files[evidence["path"]] = evidence["sha256"]
            shutil.copy2(source_inputs / evidence["path"], input_root / evidence["path"])
        removed = {}
        for role in ("regional", "local"):
            sample = request[role]["samples"][0]
            site_id = sample["site_id"].removeprefix("author:")
            path = input_root / f"{site_id}-raw.json"
            raw = json.loads(path.read_bytes())
            if raw["taxa"] != request["taxa"] or raw["sample"]["counts"] != sample["counts"]:
                raise ValueError("The selected source sample changed")
            removed[role] = sample["counts"].pop(index)
            raw["taxa"].pop(index)
            raw["sample"]["counts"].pop(index)
            _write(path, raw)
        for name in ("taxa.json", "parameters.json"):
            path = input_root / name
            value = json.loads(path.read_bytes())
            value["pilot_excluded_taxon"] = "Filipendula"
            value["pilot_original_source_sha256"] = old_files[name]
            value["retained_taxa"] = [
                taxon for i, taxon in enumerate(request["taxa"]) if i != index
            ]
            if name == "taxa.json":
                value["prepared_taxa"] = value["retained_taxa"]
            _write(path, value)
        decision_path = input_root / "decision.json"
        decision = json.loads(decision_path.read_bytes())
        decision["pilot_design"] = {
            "scope": "prior-exposed author English development, one training local/regional pair",
            "closed_subcomposition": "30 author prepared taxa excluding Filipendula",
            "removed_count_mass_in_pilot": removed,
            "cohort_removed_count_mass": {"excluded": excluded, "original": total},
            "method": "ring-taxon-preserving optimized LOVE",
            "interpretation": "numerical feasibility only; no held-out prediction, vegetation accuracy, or historical basin admission",
        }
        _write(decision_path, decision)
        request["taxa"].pop(index)
        request["parameters"].pop(index)
        geometry = json.loads((input_root / "LARKBARR-geometry.json").read_bytes())
        ring = dict(geometry["forward_rings"][2])
        if (ring["inner_m"], ring["outer_m"]) != (1000, 10000):
            raise ValueError("The declared regional ring changed")
        ring["geometry_evidence_id"] = "geometry:author:LARKBARR"
        request["rings"].append(ring)
        request["method_profile"] = "ring-taxon-preserving"
        for method in ("reveals", "love"):
            request["configuration"][method]["fall_speed_profile"] = "disqover-0.9.14-wrapper-v1"
        request["configuration"]["love"].update(
            method="optimized",
            optimized_profile="ring-taxon-preserving",
            optimizer_iterations=iterations,
            optimizer_max_evaluations=evaluations,
            optimizer_tolerance=0.01,
            repeats=repeats,
        )
        for evidence in request["evidence"]:
            evidence["sha256"] = _sha((input_root / evidence["path"]).read_bytes())
        request_path = input_root / "request.json"
        request_path.write_text(json.dumps(request, indent=2, sort_keys=True) + "\n")
        validate_lra_inputs(request, input_root=input_root)
        prepared.append(
            {
                "label": label,
                "request_sha256": _sha(request_path.read_bytes()),
                "local_removed_counts": removed["local"],
                "regional_removed_counts": removed["regional"],
                "iterations": iterations,
                "max_evaluations": evaluations,
                "repeats": repeats,
            }
        )
    return {
        "source_manifest_sha256": json.loads((source_inputs / "source-report.json").read_text())["source_manifest_sha256"],
        "source_request_sha256": _sha(base_bytes),
        "excluded_cohort_counts": excluded,
        "original_cohort_counts": total,
        "prepared": prepared,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--author-source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.author_source_root, args.output), indent=2))


if __name__ == "__main__":
    main()
