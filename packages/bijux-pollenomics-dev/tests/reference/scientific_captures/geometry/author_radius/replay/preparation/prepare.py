"""Freeze a source-bound radius comparison; never run forward transport here."""

import argparse
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

from contracts import canonical_pins
from custody import authenticate, regular, sha

A = Path(__file__).absolute().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
PACKAGES = (
    "bijux-pollenomics-dev",
    "bijux-pollenomics",
    "bijux-pollenomics-lra",
    "pollenomics",
)
PRODUCER = (
    "docs/report/pollen-reconstruction/author-lra-constrained/radius_sensitivity.py"
)
PRODUCER_SHA = "6fab1e6e225b2d9308bc75a3ff167ea6a5be621357f66ac1f0b3bf8109a1a469"
OLD = {
    "frozen": (
        "radius-sensitivity/frozen/predictions.json",
        "ca244e33f47ac9768dab60b3e62e59ea06e524cdd0e3d7e21477cb61bb592c44",
    ),
    "report": (
        "radius-sensitivity/scored/report.json",
        "d2c10a128acb00425c5c785ce195ad245bcf1b428f0f4a4d75d0f7aa95f11129",
    ),
    "scores": (
        "radius-sensitivity/scored/scores.csv",
        "60bf6b4cc25bf94a9afbb241370d55e7be17239c20e25881b4cc862e452eb494",
    ),
}


def identity():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    assert git("branch", "--show-current").strip() == b"main"
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def output_path(path):
    path = path.absolute()
    assert not path.exists() and ".." not in path.parts
    assert path.is_relative_to(R / "artifacts") and path.resolve() == path
    assert not any(p.is_symlink() for p in (path, *path.parents))
    assert path.parent.is_dir()
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-inputs-only", action="store_true")
    args = parser.parse_args()
    assert (
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix).absolute() == PY.parent.parent
        and sys.version_info[:2] == (3, 11)
    )
    before = identity()
    assert before["candidate"] == args.candidate and before["status"] == ""
    out = output_path(args.output)
    manifest = A / "prepared-source-manifest.json"
    document = json.loads(manifest.read_bytes())
    for row in document["files"]:
        assert regular(A / row["path"]) == {**row, "path": str(A / row["path"])}
    peer = A / "independent-preparation-review.json"
    review = json.loads(peer.read_bytes())
    assert review["approved"] is True and review["source_manifest_sha256"] == sha(
        manifest
    )
    original = authenticate()
    pins = {row["path"]: row for row in original["pins"]}
    roots = [R / "packages" / package / "src" for package in PACKAGES]
    sys.path[:0] = list(map(str, roots))
    modules = {}
    for package, module in zip(
        PACKAGES,
        [
            "bijux_pollenomics_dev",
            "bijux_pollenomics",
            "bijux_pollenomics_lra",
            "pollenomics",
        ],
        strict=True,
    ):
        location = Path(importlib.import_module(module).__file__).absolute()
        assert location.is_relative_to(R / "packages" / package / "src")
        modules[module] = regular(location)
    producer = R / PRODUCER
    assert sha(producer) == PRODUCER_SHA
    spec = importlib.util.spec_from_file_location("radius_source_contract", producer)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    work = (
        R / "artifacts/science/current-constrained-author-complete-source/retained-work"
    )
    inputs, predictions = work / "constrained-inputs", work / "predictions"
    # Maintained metadata-only intake; neither freeze nor score is called during preparation.
    _, source = module._sources(inputs, predictions)
    assert (
        module.PUBLISHED_PREDICTIONS_SHA
        == "85ce8fd89d992db10a17f15b799fa5c96de0c658eb0eec1a9e117e51a008e110"
    )
    historical = {}
    for label, (name, expected) in OLD.items():
        path = R / "docs/report/pollen-reconstruction/author-lra-constrained" / name
        assert sha(path) == expected
        historical[label] = regular(path)
        pins[str(path)] = regular(path)
    paths = {
        manifest,
        peer,
        producer,
        R / "docs/report/pollen-reconstruction/author-lra-constrained/predictions.csv",
        R / "docs/report/pollen-reconstruction/author-lra-constrained/scores.csv",
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
        R / "artifacts/science/runtime/receipt.json",
        PY.parent.parent / "pyvenv.cfg",
    }
    paths.update(A / row["path"] for row in document["files"])
    for root in roots:
        for path in root.rglob("*"):
            assert not path.is_symlink()
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix not in {".pyc", ".pyo"}
            ):
                paths.add(path)
    original_plan = json.loads(
        (
            R / "artifacts/science/current-constrained-author-complete-source/plan.json"
        ).read_bytes()
    )
    aliases = dict(original_plan["runtime_entry_targets"])
    standard = Path(sysconfig.get_path("stdlib"))
    for runtime in [PY.parent.parent, standard]:
        for path in runtime.rglob("*"):
            if runtime == standard and "site-packages" in path.parts:
                continue
            if path.is_symlink():
                assert path.resolve().exists()
                aliases[str(path)] = str(path.resolve())
            if path.is_file() and path.suffix not in {".pyc", ".pyo"}:
                paths.add(path.resolve())
    for path in paths:
        row = regular(path)
        pins[row["path"]] = row
    assert identity() == before
    if args.check_inputs_only:
        print(
            json.dumps(
                {
                    "candidate": args.candidate,
                    "original_inputs": 33336,
                    "complete_work": 900,
                    "current_pins": len(pins),
                    "maintained_source_intake_only": True,
                    "forward_fit_scoring_or_plan_executed": False,
                }
            )
        )
        return
    out.mkdir()
    (out / "scratch").mkdir()
    base = [str(PY), "-B", str(producer)]
    common = ["--inputs", str(inputs), "--predictions", str(predictions)]
    stages = [
        {
            "id": "source-bound-fixed-vegetation-radius-freeze",
            "argv": base + ["freeze"] + common + ["--output", str(out / "frozen")],
            "timeout_seconds": 60,
            "must_succeed": True,
        },
        {
            "id": "source-bound-radius-score-after-freeze",
            "argv": base
            + ["score"]
            + common
            + [
                "--frozen",
                str(out / "frozen/predictions.json"),
                "--output",
                str(out / "scored"),
            ],
            "timeout_seconds": 60,
            "must_succeed": True,
        },
        {
            "id": "independent-complete-radius-science-source-and-refusal-comparison",
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
    ]
    environment = {
        "PYTHONPATH": os.pathsep.join(map(str, roots)),
        "PYTHONDONTWRITEBYTECODE": "1",
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
        "id": "author-radius-comparison-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(out).encode()).hexdigest()[:12],
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
        "input_pins": sorted(pins.values(), key=lambda row: row["path"]),
        "absent_input_paths": [],
        "module_origins": modules,
        "producer": str(producer),
        "inputs": str(inputs),
        "predictions": str(predictions),
        "expected_source": source,
        "historical_outputs": historical,
        "qualified_original_source_projection": original[
            "current_scientific_source_projection"
        ],
        "qualified_original_current_pins": canonical_pins(original["pins"]),
        "stages": stages,
        "environment": environment,
        "resources": {
            "overall_timeout_seconds": 240,
            "declared_memory_bytes": 2147483648,
            "declared_storage_bytes": 134217728,
            "maximum_parallel_workers": 1,
            "numerical_threads_per_worker": 1,
        },
        "scope": "Three-factor forward radius comparison uses genuine source117 complete195/192/3 fit/preparations without refitting. Complete historical numerical values, source-only metadata delta, BECKHAM refusal and prior-exposed English limits are independently checked. The separate paired-comparison owner is not executed/admitted. No new fitting/optimizer/R, Nordic/ecology/rights/human or official release acceptance.",
    }
    path = out / "plan.json"
    path.write_text(json.dumps(plan, indent=2) + "\n")
    print(
        json.dumps(
            {"plan": str(path), "sha256": sha(path), "stages": 3, "pins": len(pins)}
        )
    )


if __name__ == "__main__":
    main()
