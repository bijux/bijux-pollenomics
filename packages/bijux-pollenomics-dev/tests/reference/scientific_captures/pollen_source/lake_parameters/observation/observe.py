# ruff: noqa: E402
"""Read original source pages independently after genuine maintained consumer stages."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


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
from contracts import ROOT, checkpoint, execution_scope, load, require, write
from lake_review import canonical, decode, reconstruct
from projection_review import qualify_projection
from source_inputs import pin


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = load(args.plan)
    authority, scope = execution_scope(plan)
    output, capture = Path(plan["output"]), Path(plan["capture_root"])
    progress = __import__("json").loads((output / "stage-progress.json").read_bytes())
    expected = plan["stages"][:-1]
    require(
        len(progress) == len(expected),
        "Complete actual maintained consumer stages required",
    )
    for declared, actual in zip(expected, progress, strict=True):
        require(
            actual["id"] == declared["id"]
            and actual["argv"] == declared["argv"]
            and type(actual["actual_exit"]) is int
            and actual["actual_exit"] == 0
            and actual["timed_out"] is False,
            "Maintained native stage did not pass exactly",
        )
        for stream in ("stdout", "stderr"):
            require(
                Path(actual[stream]).parent == output
                and pin(Path(actual[stream]))["sha256"] == actual[stream + "_sha256"],
                "Actual native log differs",
            )
    report, indexed = reconstruct(
        (capture / "capture.json").read_bytes(),
        (capture / "site-evidence.json").read_bytes(),
        lambda name: (capture / "capture-pages" / name).read_bytes(),
        plan["capture_sha256"],
        plan["site_evidence_sha256"],
    )
    historical = Path(plan["historical_lake_report"]["path"])
    expected_raw = historical.read_bytes()
    require(
        pin(historical) == plan["historical_lake_report"],
        "Original public expected report differs",
    )
    rebuilt = canonical(report)
    require(
        canonical(decode(expected_raw)) == rebuilt,
        "Complete independent source report typed values differ",
    )
    require(expected_raw == rebuilt, "Original lake report wire bytes differ")
    checker = load(output / "maintained-reader-checker.json")
    require(
        checker["candidate"] == plan["candidate"]
        and type(checker["actual_exit"]) is int
        and checker["actual_exit"] == 0
        and checker["source"] == plan["maintained_reader"]
        and checker["actual_source_argv"]
        == [plan["maintained_reader"]["path"], "--capture-root", plan["capture_root"]]
        and checker["checker_only"] is True
        and checker["new_maintained_report_written"] is False,
        "Maintained reader role or proof differs",
    )
    text = Path(progress[0]["stdout"]).read_text()
    require(
        text
        == f"verified {report['source_table_rows']} source rows, {report['candidate_sites_with_observed_parameter_rows']} candidate matches and zero LRA admissions\n",
        "Native reader stdout does not match independently derived source counts",
    )
    target = output / "independently-reconstructed-lakeparameter-report.json"
    with target.open("xb") as destination:
        destination.write(rebuilt)
    optional = None
    if plan["include_prerequisites"]:
        path = output / "prerequisite-projection.json"
        execution = load(output / "maintained-projection-execution.json")
        source = (
            ROOT
            / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/taxa_review/lra_prerequisites/__main__.py"
        )
        expected_argv = [
            str(source),
            "--raw-root",
            str(ROOT / "data/neotoma/raw/neotoma_pollen_dataset_downloads"),
            "--normalized-root",
            str(ROOT / "data/neotoma/relational"),
            "--lakeparameter-capture-root",
            plan["capture_root"],
            "--lakeparameter-capture-sha256",
            plan["capture_sha256"],
            "--output",
            str(path),
        ]
        require(
            execution["candidate"] == plan["candidate"]
            and type(execution["actual_exit"]) is int
            and execution["actual_exit"] == 0
            and execution["generated_projection"] == pin(path),
            "Genuine maintained projection output proof differs",
        )
        require(
            execution["actual_module"]
            == "bijux_pollenomics_dev.taxa_review.lra_prerequisites"
            and execution["maintained_source"] == pin(source)
            and execution["actual_source_argv"] == expected_argv,
            "Actual maintained projection source/module/arguments differ",
        )
        before = plan["optional_expected_report"]
        expected_path = Path(before["path"])
        require(pin(expected_path) == before, "Current projection baseline changed")
        optional = qualify_projection(
            expected_path.read_bytes(),
            path.read_bytes(),
            plan["capture_sha256"],
            indexed,
            pin(
                ROOT / "data/neotoma/raw/neotoma_pollen_dataset_downloads/manifest.json"
            )["sha256"],
            pin(ROOT / "data/neotoma/relational/manifest.json")["sha256"],
        )
        require(
            Path(progress[1]["stdout"]).read_text().strip() == pin(path)["sha256"],
            "Actual projection stdout hash differs from generated bytes",
        )
    checkpoint(authority, scope)
    write(
        output / "independent-source-review.json",
        {
            "candidate": plan["candidate"],
            "actual_exit": 0,
            "plan": pin(args.plan),
            "maintained_reader_checker_exit": 0,
            "reconstructed_report": pin(target),
            "complete_lake_report_typed_identical": True,
            "lake_tracked_byte_checker_exit": 0,
            "source_table_rows": report["source_table_rows"],
            "source_type_rows": report["source_type_rows"],
            "original_candidate_source_sites": report["candidate_source_sites"],
            "original_candidate_sites_with_observed_rows": report[
                "candidate_sites_with_observed_parameter_rows"
            ],
            "original_source_locator_joins": len(report["source_rows"]),
            "source_consistency": report["source_consistency"],
            "absence_interpretation": report["absence_interpretation"],
            "basin_admission_status": "not_reviewed",
            "lra_admitted_samples": 0,
            "optional_current_projection": optional,
            "private_source_pages_copied_or_published": False,
            "rights_or_human_authority_qualified": False,
            "HTTP_or_new_acquisition_performed": False,
            "scope": "Native independent complete page reconstruction and exact current report source reconciliation. Original54-site source authority and optional current projection have distinct denominators. No transactional absence, basin, chronology, ecology, LRA execution, rights/human or release admission.",
        },
    )
    print(
        __import__("json").dumps(
            {
                "actual_exit": 0,
                "independent_review": pin(output / "independent-source-review.json"),
            }
        )
    )


if __name__ == "__main__":
    main()
