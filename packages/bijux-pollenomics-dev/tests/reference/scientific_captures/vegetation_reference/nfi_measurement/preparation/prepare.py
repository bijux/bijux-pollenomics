"""Freeze exact private original NFI selected-field metadata replay, without opening outcomes."""

from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import sysconfig

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import SOURCE, SOURCE_SHA, GUIDE_SHA, dump, pin, read, require, sha
from runtime_custody import stdlib_alias_contract, tree

A = Path(__file__).resolve().parent
R = A.parents[2]
PY = R / "artifacts/science/runtime/environment/bin/python"
MODULE = (
    "bijux_pollenomics_dev.source_completion.empd2_nfi_reference.measurement_schema"
)
PRODUCER = (
    R
    / "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/empd2_nfi_reference/measurement_schema.py"
)


def identity() -> dict[str, str]:
    def git(*args: str) -> bytes:
        return subprocess.check_output(["git", *args], cwd=R, timeout=60)

    require(git("branch", "--show-current").strip() == b"main", "Local main required")
    return {
        "candidate": git("rev-parse", "HEAD").decode().strip(),
        "status": git("status", "--porcelain").decode(),
        "tracked_inventory_sha256": hashlib.sha256(
            git("ls-files", "-s", "-z")
        ).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--private-source-store", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(
        Path(sys.executable).absolute() == PY
        and Path(sys.prefix) == PY.parent.parent
        and sys.version_info[:2] == (3, 11),
        "Qualified lexical Python3.11 required",
    )
    before = identity()
    require(
        before["candidate"] == args.candidate and before["status"] == "",
        "Exact clean candidate required",
    )
    source_manifest = A / "prepared-source-manifest.json"
    for row in read(source_manifest)["files"]:
        require(
            pin(A / row["path"]) == {**row, "path": str(A / row["path"])},
            "Held source changed",
        )
    peer = A / "independent-source-review.json"
    require(
        read(peer)["approved"] is True
        and read(peer)["source_manifest_sha256"] == sha(source_manifest),
        "Independent held source review required",
    )
    store = args.private_source_store.absolute()
    require(
        store.resolve() == store
        and store.is_dir()
        and not any(p.is_symlink() for p in (store, *store.parents)),
        "Exact governed private store required",
    )
    source = store / SOURCE
    require(
        not any(p.is_symlink() for p in (source, *source.parents))
        and sha(source) == SOURCE_SHA,
        "Exact private original workbook required",
    )
    output = args.output.absolute()
    require(
        output.resolve() == output
        and output.is_relative_to(R / "artifacts")
        and not output.exists()
        and not any(p.is_symlink() for p in (output, *output.parents)),
        "Fresh nonsymlink owned output required",
    )
    family = R / "docs/report/validation/empd2-nfi-pairing"
    guide = family / "inputs/slu-calibration-guide.pdf"
    require(sha(guide) == GUIDE_SHA, "Historical calibration guide bytes changed")
    source_use_review = (
        R
        / "artifacts/science/slu-calibration-guide-source-review/retained-source-review.json"
    )
    require(
        sha(source_use_review)
        == "8be8d30b38ab3f6848f809edb8d7881c490a1dc0022365d71809957a3c630350",
        "Exact retained PDF source-use review differs",
    )
    use_evidence = read(source_use_review)
    require(
        use_evidence["guide"] == pin(guide)
        and use_evidence["literal_source_use_statements"][
            "publication_use_statement_present_in_exact_PDF"
        ]
        is True
        and use_evidence["original_provider_receipt_or_literal_href_qualified"]
        is False,
        "Retained source-use facts differ from guide identity/retrieval limits",
    )
    literal_text = Path(use_evidence["literal_text"]["path"])
    require(
        pin(literal_text) == use_evidence["literal_text"],
        "Exact guide literal text changed",
    )
    files = {
        source_use_review,
        literal_text,
        source_manifest,
        peer,
        PRODUCER,
        source,
        guide,
        family / "nfi-measurement-schema.json",
        family / "README.md",
        R / "configs/ci/report-ownership.json",
        R / "reports/source-lock.json",
        PY.resolve(),
        PY.parent.parent / "pyvenv.cfg",
        R / "artifacts/science/runtime/receipt.json",
        R / "artifacts/science/current-report-custody/run_account_qualification.py",
        store / "reference-sources/empd2-nfi/nfi/swedish-eligibility.json",
        store / "reference-sources/empd2-nfi/nfi/nordic-access.json",
    }
    files.update(A / r["path"] for r in read(source_manifest)["files"])
    roots = [
        R / "packages" / name / "src"
        for name in (
            "bijux-pollenomics",
            "bijux-pollenomics-dev",
            "bijux-pollenomics-lra",
            "pollenomics",
        )
    ]
    stdlib = Path(sysconfig.get_path("stdlib")).resolve()
    external, unused, authority = stdlib_alias_contract(
        stdlib, PY.parent.parent, list(sys.path)
    )
    aliases = {str(PY): str(PY.resolve())}
    for root in [*roots, stdlib, PY.parent.parent / "lib/python3.11/site-packages"]:
        paths, links = tree(
            root,
            external_files=external if root == stdlib else None,
            unused_directory_aliases=unused if root == stdlib else None,
        )
        files.update(paths)
        aliases.update(links)
    owner = next(
        row
        for row in read(R / "configs/ci/report-ownership.json")["owners"]
        if row["owner_id"] == "validation/empd2-nfi-pairing/measurement-schema"
    )
    require(
        owner["paths"]
        == ["docs/report/validation/empd2-nfi-pairing/nfi-measurement-schema.json"]
        and owner["producer_paths"] == [PRODUCER.relative_to(R).as_posix()]
        and owner["role"] == "unresolved",
        "Exact unresolved metadata owner differs",
    )
    output.mkdir()
    (output / "scratch").mkdir()
    plan_path = output / "plan.json"
    metadata_output = output / "nfi-measurement-schema.json"
    stages = [
        {
            "id": "maintained-original-NFI-selected-metadata",
            "argv": [str(PY), "-B", str(A / "invoke.py"), "--plan", str(plan_path)],
            "timeout_seconds": 45,
            "must_succeed": True,
        },
        {
            "id": "independent-dictionary-header-area-time-and-owner",
            "argv": [
                str(PY),
                "-I",
                "-B",
                str(A / "observe.py"),
                "--plan",
                str(plan_path),
            ],
            "timeout_seconds": 45,
            "must_succeed": True,
        },
    ]
    plan = {
        "id": "nfi-measurement-metadata-"
        + args.candidate[:12]
        + "-"
        + hashlib.sha256(str(output).encode()).hexdigest()[:12],
        "candidate": args.candidate,
        "repository": str(R),
        "output": str(output),
        "canonical_identity": before,
        "qualified_python": str(PY),
        "common_runner": str(
            R / "artifacts/science/current-report-custody/run_account_qualification.py"
        ),
        "private_source_store": str(store),
        "private_original": pin(source),
        "maintained_module": MODULE,
        "maintained_producer": pin(PRODUCER),
        "metadata_output": str(metadata_output),
        "source_roots": [str(p) for p in roots],
        "metadata_owner": owner,
        "runtime_entry_targets": {str(PY): str(PY.resolve())},
        "runtime_aliases": aliases,
        "runtime_alias_links": {p: os.readlink(p) for p in aliases},
        "stdlib_alias_authority": authority,
        "input_pins": [pin(p) for p in sorted(files)],
        "absent_input_paths": [],
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONPYCACHEPREFIX": str(output / "pycache"),
            "PYTHONPATH": os.pathsep.join(str(p) for p in roots),
            "TMPDIR": str(output / "scratch"),
        },
        "stages": stages,
        "resources": {
            "overall_timeout_seconds": 110,
            "declared_memory_bytes": 1073741824,
            "declared_storage_bytes": 134217728,
        },
        "calibration_guide": {
            "physical": pin(guide),
            "retained_owner_admitted": False,
            "missing_evidence": [
                "Original provider retrieval/copy receipt bound to exact guide SHA",
                "Authenticated retained official-page body with literal PDF href",
            ],
            "source_use_statements_verified": True,
            "source_use_evidence": pin(source_use_review),
            "source_use_literal_text": pin(literal_text),
            "source_use_scope": "Exact retained PDF states CC0 1.0 and temporary forest plot use for remote-sensing calibration/validation, with no geographic area totals/means. This does not authenticate original provider retrieval/copy or literal href.",
            "source_history_limit": "Original provider retrieval/copy chain and authenticated retained official-page literal PDF href remain unqualified; source-use wording is directly verified from exact PDF.",
        },
        "scope": "Genuine original workbook selected-field metadata replay only. Full worksheet XML streams include unselected cells, semantic decoders only dictionary/header and D-G-H; no tree measurement outcomes decoded/displayed/scored, benchmark/admission/target mapping/model choice remain absent. No private workbook redistribution, original retrieval identity invented or calibration guide ownership closure. Memory/storage are completed postchecks, no OS quota/full descendant RSS claim.",
    }
    require(identity() == before, "Canonical candidate changed during preparation")
    dump(plan_path, plan)
    print(
        __import__("json").dumps(
            {
                "plan": pin(plan_path),
                "stages": 2,
                "pins": len(files),
                "actual_launch_argv": [
                    str(PY),
                    "-B",
                    str(A / "run.py"),
                    "--plan",
                    str(plan_path),
                    "--registered-plan-sha256",
                    sha(plan_path),
                ],
            }
        )
    )


if __name__ == "__main__":
    main()
