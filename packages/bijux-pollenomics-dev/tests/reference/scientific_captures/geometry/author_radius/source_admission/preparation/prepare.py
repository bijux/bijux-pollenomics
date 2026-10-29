"""Freeze the real four-ledger paired consumer without rerunning any forward model."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import sysconfig
from typing import Any

from contracts import EXPECTED, PRODUCER_SHA, source_identity_only
from custody import A, B, R, authenticate, blob, identity, output_path, regular, sha

JsonObject = dict[str, Any]
PY = R / "artifacts/science/runtime/environment/bin/python"
BASE = "e1ca9def55e7cd3e68ac6f20270059e743373251"
FAMILY = "docs/report/pollen-reconstruction/author-lra-constrained"
NAME = FAMILY + "/radius-sensitivity/paired_comparison.py"
STUDY = {
    "radius_report": (
        B / "scored/report.json",
        "radius-sensitivity/scored/report.json",
    ),
    "radius_scores": (B / "scored/scores.csv", "radius-sensitivity/scored/scores.csv"),
    "direct_mae": (
        R / FAMILY / "direct-pollen/matched-scores.csv",
        "direct-pollen/matched-scores.csv",
    ),
    "direct_hellinger": (
        R / FAMILY / "direct-pollen/paired-hellinger.json",
        "direct-pollen/paired-hellinger.json",
    ),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert Path(sys.executable).absolute() == PY and sys.version_info[:2] == (3, 11)
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    out = output_path(args.output)
    manifest = A / "prepared-source-manifest.json"
    doc = json.loads(manifest.read_bytes())
    for row in doc["files"]:
        assert regular(A / row["path"]) == {**row, "path": str(A / row["path"])}
    peer = A / "independent-preparation-review.json"
    reviewed = json.loads(peer.read_bytes())
    assert reviewed["approved"] is True and reviewed["source_manifest_sha256"] == sha(
        manifest
    )
    producer = A / "proposal" / NAME
    assert sha(producer) == PRODUCER_SHA
    source_identity_only(blob(BASE, NAME), producer.read_bytes())
    original = authenticate()
    pins = {row["path"]: row for row in original["pins"]}
    paths = {
        manifest,
        peer,
        producer,
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
        R / "artifacts/science/runtime/receipt.json",
        R / "configs/mypy.ini",
        R / "configs/ruff.toml",
    }
    paths.update(A / row["path"] for row in doc["files"])
    sources = {}
    for label, (path, target) in STUDY.items():
        assert sha(path) == EXPECTED[label]
        sources[label] = {**regular(path), "target": target}
        paths.add(path)
    old = {}
    for label, suffix in [
        ("report", "paired/report.json"),
        ("scores", "paired/paired-scores.csv"),
    ]:
        p = R / FAMILY / "radius-sensitivity" / suffix
        raw = blob(BASE, p.relative_to(R).as_posix())
        assert p.read_bytes() == raw
        old[label] = regular(p)
        paths.add(p)
    # Capture complete current first-party source/resources and configured policy inputs.
    roots = [
        R / f"packages/{n}/src"
        for n in [
            "bijux-pollenomics-dev",
            "bijux-pollenomics",
            "bijux-pollenomics-lra",
            "pollenomics",
        ]
    ]
    for root in roots:
        for p in root.rglob("*"):
            assert not p.is_symlink()
            if (
                p.is_file()
                and "__pycache__" not in p.parts
                and p.suffix not in {".pyc", ".pyo"}
            ):
                paths.add(p)
    aliases = dict(original["runtime_entry_targets"])
    standard = Path(sysconfig.get_path("stdlib"))
    for runtime in [PY.parent.parent, standard]:
        for p in runtime.rglob("*"):
            if runtime == standard and "site-packages" in p.parts:
                continue
            if p.is_symlink():
                assert p.resolve().exists()
                aliases[str(p)] = str(p.resolve())
            if p.is_file() and p.suffix not in {".pyc", ".pyo"}:
                paths.add(p.resolve())
    for p in paths:
        row = regular(p)
        pins[row["path"]] = row
    assert identity() == before
    # All rejection guards precede output creation; retain exact producer inputs physically.
    out.mkdir()
    (out / "scratch").mkdir()
    for row in sources.values():
        target = out / "study" / row["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(Path(row["path"]).read_bytes())
        current = regular(target)
        assert current["sha256"] == row["sha256"] and current["bytes"] == row["bytes"]
        pins[str(target)] = current
    environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": os.pathsep.join(map(str, roots)),
        "TMPDIR": str(out / "scratch"),
        "PYTHONPYCACHEPREFIX": str(out / "pycache"),
        "PROJ_NETWORK": "OFF",
    }
    environment.update(
        dict.fromkeys(
            [
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
            ],
            "1",
        )
    )
    plan = {
        "id": "source-bound-radius-paired-"
        + args.candidate[:12]
        + "-"
        + sha(manifest)[:12],
        "candidate": args.candidate,
        "source_candidate": args.candidate,
        "repository": str(R),
        "output": str(out),
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "canonical_identity": before,
        "runtime_entry_targets": aliases,
        "input_pins": sorted(pins.values(), key=lambda r: r["path"]),
        "absent_input_paths": [],
        "producer": regular(producer),
        "source_guard_base": BASE,
        "source_guard_AST_identity_only": True,
        "radius_execution": {
            k: original[k]
            for k in [
                "original_source_candidate",
                "original_plan_sha256",
                "original_outer_sha256",
                "original_observer_sha256",
                "original_input_count",
                "original_input_transitions",
                "original_numerical_source_projection",
            ]
        },
        "sources": sources,
        "historical_paired": old,
        "stages": [
            {
                "id": "maintained-four-ledger-radius-paired-join",
                "argv": [
                    str(PY),
                    "-B",
                    str(producer),
                    "--study",
                    str(out / "study/radius-sensitivity"),
                    "--output",
                    str(out / "paired"),
                ],
                "timeout_seconds": 60,
                "must_succeed": True,
            },
            {
                "id": "independent-complete-paired-science-and-source-observer",
                "argv": [
                    str(PY),
                    "-B",
                    str(A / "observe.py"),
                    "--plan",
                    str(out / "plan.json"),
                ],
                "timeout_seconds": 90,
                "must_succeed": True,
            },
        ],
        "environment": environment,
        "resources": {
            "overall_timeout_seconds": 240,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 134217728,
            "maximum_parallel_workers": 1,
            "numerical_threads_per_worker": 1,
        },
        "scope": "Real paired table construction only, after genuine radius three-stage zero. Original forward execution candidate2784 and constrained candidate22c6 remain distinct. No forward, fit, inversion, optimizer or R repeat. Original full pins use exact old/current Git bridges with unchanged scientific source projection. No ecological, independent/equal-information ranking, physical-radius or rights acceptance.",
    }
    plan_path = out / "plan.json"
    plan_path.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {
                "plan": str(plan_path),
                "sha256": sha(plan_path),
                "inputs": len(pins),
                "stages": 2,
            }
        )
    )


if __name__ == "__main__":
    main()
