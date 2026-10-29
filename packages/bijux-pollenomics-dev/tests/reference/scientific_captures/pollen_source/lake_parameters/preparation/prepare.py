# ruff: noqa: E402
"""Freeze current maintained lakeparameter readers without decoding source pages."""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
from typing import Any


def _verify_entry_namespace(root: Path) -> None:
    expected = {
        ".": [
            "check_controls.py",
            "check_tools.py",
            "common_runner.py",
            "contracts.py",
            "execute_projection.py",
            "execute_reader.py",
            "lake_review.py",
            "observe.py",
            "prepare.py",
            "projection_review.py",
            "run.py",
            "runtime_contracts.py",
            "source_admission.py",
            "source_entry.py",
            "source_inputs.py",
            "source_runtime.py",
        ]
    }
    for domain, names in expected.items():
        directory = root if domain == "." else root / domain
        if directory.is_symlink() or not directory.is_dir():
            raise ValueError("Controller import domain is absent or linked")
        for entry in directory.iterdir():
            if entry.is_symlink() or not (entry.is_file() or entry.is_dir()):
                raise ValueError("Controller import namespace contains alias/special")
            if domain == ".":
                if entry.is_dir() and entry.name not in {
                    "preflight",
                    *set(expected) - {"."},
                }:
                    raise ValueError("Unexpected controller import directory")
                if (
                    entry.suffix in {".py", ".pyc", ".so", ".pyd", ".dylib"}
                    and entry.name not in names
                ):
                    raise ValueError("Unexpected controller import member")
            elif entry.is_dir() or entry.name not in names:
                raise ValueError("Unexpected nested controller import member")
        if domain != "." and {entry.name for entry in directory.iterdir()} != set(
            names
        ):
            raise ValueError("Nested controller import member is missing")


def _verify_reviewed_entry(root: Path) -> None:
    manifest = root / "prepared-source-manifest.json"
    review = root / "independent-source-review.json"
    for path in (manifest, review):
        if not path.is_file() or any(
            parent.is_symlink() for parent in (path, *path.parents)
        ):
            raise ValueError(
                "Reviewed controller entry requires regular source authority"
            )
    raw = manifest.read_bytes()
    document = json.loads(raw)
    admission = json.loads(review.read_bytes())
    if (
        document["source_only"] is not True
        or admission["approved"] is not True
        or admission["source_manifest_sha256"] != hashlib.sha256(raw).hexdigest()
    ):
        raise ValueError(
            "Exact independent source approval required before local imports"
        )
    names = [row["path"] for row in document["files"]]
    if names != sorted(set(names)):
        raise ValueError("Reviewed entry source paths must be sorted and unique")
    for row in document["files"]:
        path = Path(row["path"])
        if (
            not path.is_absolute()
            or ".." in path.parts
            or not path.is_relative_to(root)
            or any(parent.is_symlink() for parent in (path, *path.parents))
        ):
            raise ValueError("Reviewed controller entry leaves physical source")
        if (
            not path.is_file()
            or type(row["bytes"]) is not int
            or path.stat().st_size != row["bytes"]
        ):
            raise ValueError("Reviewed controller entry length changed")
        with path.open("rb") as stream:
            checksum = hashlib.file_digest(stream, "sha256").hexdigest()
        if checksum != row["sha256"]:
            raise ValueError("Reviewed controller source changed before local imports")
    required = {
        entry
        for names in {
            ".": [
                "check_controls.py",
                "check_tools.py",
                "common_runner.py",
                "contracts.py",
                "execute_projection.py",
                "execute_reader.py",
                "lake_review.py",
                "observe.py",
                "prepare.py",
                "projection_review.py",
                "run.py",
                "runtime_contracts.py",
                "source_admission.py",
                "source_entry.py",
                "source_inputs.py",
                "source_runtime.py",
            ]
        }.values()
        for entry in names
    }
    declared = {Path(name).relative_to(root).as_posix() for name in names}
    if not required.issubset(declared):
        raise ValueError("Reviewed controller manifest omits a local import member")


_verify_entry_namespace(Path(__file__).resolve().parent)
_verify_reviewed_entry(Path(__file__).resolve().parent)

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    GIT,
    PACKAGES,
    PYTHON,
    ROOT,
    SOURCE,
    LakeInputs,
    checkpoint,
    identity,
    load,
    output_root,
    require,
    validate_private_namespace,
    write,
)
from source_admission import reviewed_controls
from source_inputs import pin
from source_runtime import authenticate_runtime


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--review-sha256", required=True)
    parser.add_argument("--include-prerequisites", action="store_true")
    args = parser.parse_args()
    _, peer, controlled = reviewed_controls(SOURCE)
    require(
        pin(peer)["sha256"] == args.review_sha256, "Independent peer digest differs"
    )
    scope = LakeInputs(controlled)
    scope.capture([GIT])
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean dynamic candidate required",
    )
    output = output_root(args.output)
    declared = load(SOURCE / "declared-inputs.json")
    proof = declared["physical_custody"]
    require(
        pin(Path(proof["path"])) == proof, "Reviewed physical source custody differs"
    )
    scope.extend([proof])
    scope.extend(declared["private_expected_pins"])
    private = Path(declared["capture_root"])
    scope.namespaces.append(
        validate_private_namespace(private, declared["private_expected_pins"])
    )
    for package in PACKAGES:
        scope.capture_tree(ROOT / "packages" / package / "src")
    lake_reader = ROOT / declared["lake_reader"]
    lake_report = ROOT / declared["lake_report"]
    scope.capture([lake_reader, lake_report, ROOT / "configs/ci/report-ownership.json"])
    optional_inputs: list[str] = []
    if args.include_prerequisites:
        expected = {str(ROOT / name) for name in declared["optional_inputs"]}
        require(
            len(expected) == 30 and all(Path(name).is_file() for name in expected),
            "Optional projection requires every original30 input",
        )
        actual = set(
            scope.capture_tree(
                ROOT / "data/neotoma/raw/neotoma_pollen_dataset_downloads"
            )
        )
        actual.update(scope.capture_tree(ROOT / "data/neotoma/relational"))
        require(
            actual == expected,
            "Optional raw/normalized complete namespaces differ from declared30",
        )
        optional_inputs = sorted(actual)
        scope.capture([ROOT / declared["optional_report"]])
    # Original reviewed/private/current-source identities precede the long runtime census.
    scope.verify()
    authority, runtime = authenticate_runtime()
    scope.extend(runtime)
    checkpoint(authority, scope)
    require(identity() == before, "Candidate/index changed before output creation")
    output_root(output)
    require(
        shutil.disk_usage(output.parent).free >= 1024**3,
        "Need128MiB output budget and physical reserve",
    )
    output.mkdir()
    for name in ("scratch", "cache", "cache/matplotlib"):
        (output / name).mkdir()
    plan_path = output / "plan.json"
    plan: dict[str, Any] = {
        "id": "neotoma-lakeparameter-maintained-source-" + args.candidate[:12],
        "candidate": args.candidate,
        "repository": str(ROOT),
        "output": str(output),
        "canonical_identity": before,
        "input_pins": scope.rows,
        "absent_input_paths": [],
        "qualified_source_runtime": authority,
        "runtime_entry_raw_aliases": scope.aliases,
        "runtime_entry_lexical_paths": scope.entries,
        "input_namespace_snapshots": deepcopy(scope.namespaces),
        "capture_root": str(private),
        "capture_sha256": declared["capture_sha256"],
        "site_evidence_sha256": declared["site_evidence_sha256"],
        "maintained_reader": pin(lake_reader),
        "historical_lake_report": pin(lake_report),
        "include_prerequisites": args.include_prerequisites,
        "optional_inputs": optional_inputs,
        "optional_expected_report": pin(ROOT / declared["optional_report"])
        if args.include_prerequisites
        else None,
        "common_runner": str(SOURCE / "common_runner.py"),
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPATH": "",
            "TMPDIR": str(output / "scratch"),
            "XDG_CACHE_HOME": str(output / "cache"),
            "MPLCONFIGDIR": str(output / "cache/matplotlib"),
            "PATH": "/Library/Developer/CommandLineTools/usr/bin:/usr/bin:/bin",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            **dict.fromkeys(
                (
                    "OMP_NUM_THREADS",
                    "OPENBLAS_NUM_THREADS",
                    "MKL_NUM_THREADS",
                    "NUMEXPR_NUM_THREADS",
                    "VECLIB_MAXIMUM_THREADS",
                ),
                "1",
            ),
        },
        "resources": {
            "overall_timeout_seconds": 720,
            "outer_timeout_seconds": 740,
            "declared_memory_bytes": 4 * 1024**3,
            "declared_storage_bytes": 128 * 1024**2,
        },
        "scope": "Offline maintained lake reader checker plus independent complete source-page/type/site/value/locator reconstruction. Optional genuine current prerequisite projection only with all30 source files; original54 site capture and current projection universes remain distinct. Live pagination is not transactional, absence not certified, basin unreviewed, zero LRA. No HTTP/acquisition/model/R, rights/human/ecological or release admission.",
    }
    selections = [("maintained-lakeparameter-reader-checker", "execute_reader.py", 120)]
    if args.include_prerequisites:
        selections.append(
            ("maintained-current-prerequisite-projection", "execute_projection.py", 240)
        )
    selections.append(
        ("independent-lake-source-and-optional-projection-observer", "observe.py", 120)
    )
    plan["stages"] = [
        {
            "id": name,
            "argv": [
                str(PYTHON),
                "-I",
                "-B",
                str(SOURCE / script),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": wall,
            "must_succeed": True,
        }
        for name, script, wall in selections
    ]
    require(
        sum(row["timeout_seconds"] for row in plan["stages"])
        <= plan["resources"]["overall_timeout_seconds"],
        "Stage budgets exceed aggregate",
    )
    checkpoint(authority, scope)
    require(identity() == before, "Candidate/index changed before final freeze")
    write(plan_path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "stage_count": len(plan["stages"]),
                "include_prerequisites": args.include_prerequisites,
                "actual_native_consumers_launched": 0,
            }
        )
    )


if __name__ == "__main__":
    main()
