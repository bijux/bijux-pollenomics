"""Check real scalar objectives, paired masks and same-process R provenance."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from contracts import (
    FAMILIES,
    PRODUCTS,
    R_SHA,
    check_optimizer,
    check_paired,
    dump,
    pin,
    read,
    require,
    rows,
    sha,
)
from runtime_custody import aliases_unchanged


def differences(a: Any, b: Any, path: str = "$") -> list[dict[str, Any]]:
    if type(a) is type(b) and a == b:
        return []
    if isinstance(a, dict) and isinstance(b, dict):
        result = []
        for k in sorted(a.keys() | b.keys()):
            if k not in a or k not in b:
                result.append(
                    {
                        "path": path + "." + k,
                        "before": a.get(k),
                        "after": b.get(k),
                        "kind": "membership",
                    }
                )
            else:
                result.extend(differences(a[k], b[k], path + "." + k))
        return result
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [
            x
            for i, (v, w) in enumerate(zip(a, b, strict=True))
            for x in differences(v, w, f"{path}[{i}]")
        ]
    return [
        {
            "path": path,
            "before": a,
            "after": b,
            "before_type": type(a).__name__,
            "after_type": type(b).__name__,
        }
    ]


def namespace_records(
    meta: dict[str, Any], plan: dict[str, Any], family: str
) -> dict[str, int]:
    require(
        meta["schema_version"] == "controlled-lra-R-process.v1"
        and type(meta["numerical_exit"]) is int
        and meta["numerical_exit"] == 0
        and meta["numerical_error"] is None
        and type(meta["metadata_exit"]) is int
        and meta["metadata_exit"] == 0
        and meta["metadata_error"] is None,
        "Actual numerical/metadata R status differs",
    )
    original = plan["maintained_replays"][family]
    require(
        meta["original_script"] == original["canonical_R"]["path"],
        "Original numerical R source differs",
    )
    record = next(
        s for s in plan["stages"] if s["id"] == family + "-current-native-replay"
    )
    output = Path(plan["output"]) / family
    if family == "paired-love-draws":
        expected = [
            str(output / "draws.json"),
            str(output / "setup.json"),
            str(
                Path(plan["repository"])
                / "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/r_support.R"
            ),
            str(output / "r-values.csv"),
            str(output / "r-session.txt"),
        ]
    else:
        expected = [
            str(Path(original["owned_python"]["path"]).parent / "cases.json"),
            str(output / "python-fits.csv"),
            str(output / "r-fits.csv"),
            str(output / "r-session.txt"),
        ]
    require(
        meta["actual_trailing_arguments"] == expected
        and record["argv"][7:9] == ["--rscript", plan["native_Rscript"]["path"]],
        "Actual unchanged R arguments differ",
    )
    pinned = {x["path"] for x in plan["input_pins"]}
    counts = {}
    for label in ["before", "after"]:
        snapshot = meta[label]
        require(snapshot["R_home"] == plan["current_R_home"], "R runtime home differs")
        namespaces = snapshot["namespaces"]
        require(
            len({x["name"] for x in namespaces}) == len(namespaces),
            "Duplicate namespace",
        )
        by = {x["name"]: x for x in namespaces}
        for name, version in [
            ("base", "4.6.0"),
            ("jsonlite", "2.0.0"),
            ("RcppDE", "0.1.9"),
            ("disqover", "0.9.14"),
        ]:
            require(
                name in by and by[name]["version"] == version,
                "Required actual namespace version differs",
            )
        for namespace in namespaces:
            path = Path(namespace["path"])
            require(
                str(path / "DESCRIPTION") in pinned,
                "Namespace was outside complete pinned trees",
            )
            require(
                path.is_dir() and path.resolve() == path,
                "Namespace path is not physical",
            )
        for dll in snapshot["DLLs"]:
            if dll["built_in"] is True:
                require(
                    dll["name"] == dll["path"] == "base",
                    "Unknown built-in DLL sentinel",
                )
            else:
                require(
                    dll["built_in"] is False
                    and dll["path"] in pinned
                    and dll["path"] in plan["native_dependency_files"],
                    "Loaded DLL was outside pinned physical inputs",
                )
        require(
            bool(snapshot["session_info"]), "Same-process session information missing"
        )
        counts[label + "_namespaces"] = len(namespaces)
        counts[label + "_DLLs"] = len(snapshot["DLLs"])
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    args = parser.parse_args()
    plan = read(args.plan)
    out = Path(plan["output"])
    repository = Path(plan["repository"])
    require(
        aliases_unchanged(
            plan["runtime_aliases"], link_text=plan["runtime_alias_links"]
        ),
        "Runtime lexical aliases changed",
    )
    for row in plan["input_pins"]:
        require(pin(Path(row["path"])) == row, "Original frozen input changed")
    progress = read(out / "stage-progress.json")
    require(len(progress) == 2, "Both actual numerical stages required")
    for i, row in enumerate(progress):
        require(
            row["id"] == plan["stages"][i]["id"]
            and row["argv"] == plan["stages"][i]["argv"]
            and row["actual_exit"] == 0
            and row["timed_out"] is False,
            "Actual producer stage binding differs",
        )
    findings = {}
    comparisons = []
    for family in FAMILIES:
        here = out / family
        report = read(here / "report.json")
        original = plan["maintained_replays"][family]
        require(
            report["status"] == "passed"
            and report["rscript_sha256"] == R_SHA
            and report["source_package"] == "disqover 0.9.14",
            "Native source report differs",
        )
        old = read(
            repository / "docs/report/method-certification" / family / "report.json"
        )
        expected = set(old["input_sha256"]) - {
            original["canonical_python"]["path"].removeprefix(str(repository) + "/"),
            original["canonical_R"]["path"].removeprefix(str(repository) + "/"),
        } | {
            str(Path(original["owned_python"]["path"]).relative_to(repository)),
            str(Path(original["R_wrapper"]["path"]).relative_to(repository)),
        }
        if family == "optimizer-solution-quality":
            canonical_cases = str(
                Path(original["canonical_python"]["path"])
                .parent.joinpath("cases.json")
                .relative_to(repository)
            )
            owned_cases = str(
                Path(original["owned_python"]["path"])
                .parent.joinpath("cases.json")
                .relative_to(repository)
            )
            expected.remove(canonical_cases)
            expected.add(owned_cases)
        require(
            set(report["input_sha256"]) == expected,
            "Actual wrapper/canonical source membership differs",
        )
        for name, digest in report["input_sha256"].items():
            require(
                sha(repository / name) == digest, "Actual report source hash differs"
            )
        require(
            set(report["output_sha256"]) == set(PRODUCTS[family]) - {"report.json"},
            "Native output membership differs",
        )
        for name, digest in report["output_sha256"].items():
            require(sha(here / name) == digest, "Actual output digest differs")
        require(
            {p.name for p in here.iterdir() if p.is_file()}
            == set(PRODUCTS[family])
            | {"r-stdout.log", "r-stderr.log", "same-process-runtime.json"},
            "Complete native output/log/metadata membership differs",
        )
        process = read(here / "same-process-runtime.json")
        namespaces = namespace_records(process, plan, family)
        if family == "optimizer-solution-quality":
            config = read(Path(original["owned_python"]["path"]).parent / "cases.json")
            result = check_optimizer(
                config,
                rows(here / "python-fits.csv"),
                rows(here / "r-fits.csv"),
                rows(here / "summary.csv"),
            )
            require(
                report["case_count"] == 3
                and report["maximum_optimum_gap"] == 1e-4
                and report["maximum_cross_evaluation_gap"] == 1e-10,
                "Optimizer prospective thresholds differ",
            )
        else:
            result = check_paired(
                rows(here / "python-values.csv"),
                rows(here / "r-values.csv"),
                read(here / "draws.json"),
                read(here / "setup.json"),
            )
            require(
                report["paired_finite_values"] == 120
                and report["paired_missing_values"] == 280
                and report["tolerance_absolute"] == 3e-10
                and report["maximum_absolute_difference"]
                == result["maximum_absolute_difference"],
                "Paired report arithmetic differs",
            )
        findings[family] = {
            "scientific_checks": result,
            "same_process_runtime": pin(here / "same-process-runtime.json"),
            "namespace_counts": namespaces,
            "report": pin(here / "report.json"),
            "all_current_products": [pin(here / name) for name in PRODUCTS[family]],
        }
        for name in PRODUCTS[family]:
            current = here / name
            retained = repository / "docs/report/method-certification" / family / name
            item = {
                "family": family,
                "path": name,
                "current": pin(current),
                "retained": pin(retained),
                "exact_bytes": current.read_bytes() == retained.read_bytes(),
            }
            if not item["exact_bytes"]:
                if name.endswith(".json"):
                    item["all_typed_differences"] = differences(
                        read(retained), read(current)
                    )
                elif name.endswith(".csv"):
                    item["all_ordered_wire_differences"] = differences(
                        rows(retained), rows(current)
                    )
                else:
                    item["original_and_current_text_retained_separately"] = True
            comparisons.append(item)
    dump(
        out / "independent-numerical-review.json",
        {
            "native_exit": 0,
            "candidate": plan["candidate"],
            "plan_sha256": sha(args.plan),
            "actual_two_producers": [
                {
                    "id": x["id"],
                    "actual_exit": x["actual_exit"],
                    "stdout_sha256": x["stdout_sha256"],
                    "stderr_sha256": x["stderr_sha256"],
                }
                for x in progress
            ],
            "findings": findings,
            "eleven_complete_public_product_comparisons": comparisons,
            "historical_execution_proofs_recovered": False,
            "fresh_source_R_executed": True,
            "source_functions_and_tolerances_unchanged": True,
            "fresh_scientific_acceptance": "not_evaluated",
            "scope": "Independent scalar objective calculation and complete ordered pair/missing-mask review; new current execution only, original source/runtime limits remain historical. No optimizer trajectory, calibrated uncertainty, ecological/human or release acceptance.",
        },
    )


if __name__ == "__main__":
    main()
