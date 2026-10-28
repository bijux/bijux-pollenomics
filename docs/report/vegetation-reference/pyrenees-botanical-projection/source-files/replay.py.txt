"""Run source guards, conditional panel projection and independent saved-output audit."""

from pathlib import Path
import argparse
import shutil
import hashlib
import importlib.util
import json
import sys
import time

DOMAIN = Path(__file__).resolve().parent
JOB = DOMAIN


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write("\n")


def load(name):
    p = DOMAIN / (name + ".py")
    spec = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


def authority(terminal, plan, result, census_receipt, join_receipt):
    inputs = JOB / "inputs"
    if (
        type(terminal["native_exit_code"]) is not int
        or terminal["native_exit_code"] != 0
        or not terminal["status"].startswith("PASS")
        or terminal["custody_after_checked"] is not True
        or terminal["custody_after_unchanged"] is not True
        or terminal["custody_errors"]
        or terminal["owned_survivors"]
        or terminal["resource_failure"] is not None
    ):
        raise ValueError("Original lineage native authority refused")
    if (
        terminal["plan_sha256"] != sha(inputs / "lineage-plan.json")
        or terminal["candidate"] != plan["candidate"]
    ):
        raise ValueError("Lineage source candidate/plan binding differs")
    if result["passed_for_botanical_source_account"] is not True or (
        result["source_population"],
        result["nonzero_code_population"],
        result["zero_code_population"],
    ) != (208, 183, 25):
        raise ValueError("Actual lineage population differs")
    pairs = [
        ("botanical-lineage-3.00.json", "lineage-three-zero.json"),
        ("botanical-lineage-3.01.json", "lineage-three-one.json"),
        ("archive-schema-version-license.json", "archive-metadata.json"),
    ]
    for native, copied in pairs:
        if terminal["native_files"][native]["sha256"] != sha(inputs / copied):
            raise ValueError("Original lineage product binding differs")
    if terminal["comparison_files"]["consumer-result.json"]["sha256"] != sha(
        inputs / "lineage-result.json"
    ):
        raise ValueError("Lineage result binding differs")
    for receipt in (census_receipt, join_receipt):
        if type(receipt["exit"]) is not int or receipt["exit"] != 0:
            raise ValueError("Original source census/join exit refused")
    if census_receipt["products"]["all-sheet-stored-cells.json"]["sha256"] != sha(
        inputs / "stored-source-cells.json"
    ):
        raise ValueError("Original stored-cell custody differs")
    if join_receipt["products"]["literal-name-join.json"] != sha(
        inputs / "literal-source-join.json"
    ) or join_receipt["products"]["literal-plot-classes-and-taxa.json"] != sha(
        inputs / "original-taxa-classes.json"
    ):
        raise ValueError("Original literal source join custody differs")


def consume():
    inputs = JOB / "inputs"
    pins = json.loads((DOMAIN / "input-custody.json").read_text())
    for name, pin in pins.items():
        p = inputs / name
        if (
            p.is_symlink()
            or sha(p) != pin["sha256"]
            or p.stat().st_size != pin["bytes"]
        ):
            raise ValueError("Pinned immutable scientific input differs")

    def read(name):
        return json.loads((inputs / name).read_text())

    terminal = read("lineage-terminal.json")
    plan = read("lineage-plan.json")
    result = read("lineage-result.json")
    cr = read("stored-source-receipt.json")
    jr = read("literal-source-join-receipt.json")
    authority(terminal, plan, result, cr, jr)
    for name in ("native", "comparison"):
        p = JOB / name
        if p.exists() or p.is_symlink():
            raise ValueError("Owned writer root must be absent")
    (JOB / "native").mkdir()
    (JOB / "comparison").mkdir()
    domain = load("botanical_projection")
    guards = load("guards")
    stages = []
    try:
        begin = time.monotonic()
        passed = guards.check(domain, sys.modules[__name__])
        write(JOB / "comparison/source-guards.json", passed)
        stages.append(
            {
                "stage": "source-assumption-guards",
                "native_exit": 0,
                "wall_seconds": time.monotonic() - begin,
                "guard_count": len(passed),
            }
        )
        source = read("original-taxa-classes.json")
        census = read("stored-source-cells.json")
        plots, matrix, observations = domain.observed_matrix(census, source["taxa"])
        metadata = domain.plot_metadata(source)
        del census
        write(JOB / "native/original-positive-cover-observations.json", observations)
        version_records = []
        contexts = []
        summaries = []
        begin = time.monotonic()
        for version, archive, savedname in [
            ("3.00", "bdtfx-three-zero.zip", "lineage-three-zero.json"),
            ("3.01", "bdtfx-three-one.zip", "lineage-three-one.json"),
        ]:
            saved = read(savedname)
            index, byname = domain.reference_lookup(inputs / archive, version)
            for mode in domain.MODES:
                records = domain.associate(
                    saved, index, byname, mode, saved["native_anchors"]
                )
                version_records.append(
                    {"version": version, "association_mode": mode, "records": records}
                )
                for parent in domain.PARENTS:
                    for blank in domain.BLANKS:
                        case_id = "/".join([version, mode, parent, blank])
                        projection = domain.project(
                            records, plots, matrix, parent, blank
                        )
                        contexts.append(
                            {
                                "case_id": case_id,
                                "version": version,
                                "association_mode": mode,
                                "parent_assumption": parent,
                                "blank_assumption": blank,
                                **projection,
                            }
                        )
                        summaries.append(
                            {
                                "case_id": case_id,
                                "source_class_comparisons": domain.class_summaries(
                                    projection, metadata
                                ),
                            }
                        )
            del index, byname
        write(JOB / "native/botanical-association-ledger.json", version_records)
        write(JOB / "native/conditional-panel-contexts.json", contexts)
        write(JOB / "native/source-class-comparisons.json", summaries)
        write(JOB / "native/source-plot-metadata.json", metadata)
        statuses = {case["case_id"]: case["status_counts"] for case in contexts}
        summary = {
            "declared_cases": 16,
            "plot_contexts": 2000,
            "axes_per_context": 17,
            "scalar_axis_contexts": 34000,
            "source_taxa": 208,
            "source_nonzero_codes": 183,
            "source_zero_codes": 25,
            "source_positive_observations": 1757,
            "positive_observation_accounts": 28112,
            "primary_association": "source-code-authority",
            "primary_taxonomy_version": "3.01 conditional alternate, not authenticated originalauthor version",
            "case_status_counts": statuses,
            "missing_original_axis": "Comp. SF. Cichorioideae",
            "full18_axis_publication_reproduction_admitted": False,
            "no_independent_vegetation_accuracy_or_pollen_pairing": True,
            "Potentilla_is_botanical_genus_proxy": True,
            "Calluna_excluded_from_Ericaceae": True,
            "original_source_version_and_116_selection_not_recovered": True,
            "conditional_normalisation": "Closure of positive known17axis subset cover, not mutually exclusive raw percentage/author denominator",
            "source_lineage_plan_sha256": sha(inputs / "lineage-plan.json"),
            "source_lineage_terminal_sha256": sha(inputs / "lineage-terminal.json"),
            "protocol_sha256": sha(DOMAIN / "protocol.json"),
            "independent_qualification_pending": True,
        }
        assert (
            len(contexts) == 16
            and sum(len(c["outcomes"]) for c in contexts) == 2000
            and sum(len(c["positive_observation_loss_ledger"]) for c in contexts)
            == 28112
        )
        write(JOB / "native/projection-summary.json", summary)
        stages.append(
            {
                "stage": "conditional-botanical-projection",
                "native_exit": 0,
                "wall_seconds": time.monotonic() - begin,
                "cases": 16,
                "contexts": 2000,
            }
        )
        oracle = load("independent")
        begin = time.monotonic()
        review = oracle.verify(JOB)
        write(JOB / "comparison/independent-output-review.json", review)
        stages.append(
            {
                "stage": "independent-saved-output-audit",
                "native_exit": 0,
                "wall_seconds": time.monotonic() - begin,
            }
        )
        write(
            JOB / "comparison/consumer-result.json",
            {
                "passed_for_conditional_botanical_projection": True,
                "all_native_stages": stages,
                "projection_sha256": sha(
                    JOB / "native/conditional-panel-contexts.json"
                ),
                "association_sha256": sha(
                    JOB / "native/botanical-association-ledger.json"
                ),
                "independent_review_sha256": sha(
                    JOB / "comparison/independent-output-review.json"
                ),
                "scientific_scope": "Conditional17-axis botanical grouping only; source names/code/nomenclature/blank/generic-row assumptions retained. No model/pollen pairing/historical116/full18/empirical vegetation accuracy admitted.",
            },
        )
        print(
            json.dumps(
                {
                    "cases": 16,
                    "contexts": 2000,
                    "all_stages_native_exit": 0,
                    "independent_verified": True,
                }
            )
        )
        return 0
    except Exception:
        stages.append(
            {"stage": "failed-stage-after-retained-predecessors", "native_exit": 1}
        )
        raise
    finally:
        write(JOB / "comparison/native-stage-results.json", stages)


def main():
    global JOB
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_root.resolve(strict=True)
    output = args.output.absolute()
    if output.exists() or output.is_symlink():
        raise ValueError("Owned output root must be absent")
    pins = json.loads((DOMAIN / "input-custody.json").read_text())
    for name, pin in pins.items():
        path = source / name
        if (
            path.is_symlink()
            or not path.is_file()
            or (sha(path) != pin["sha256"] or path.stat().st_size != pin["bytes"])
        ):
            raise ValueError("Pinned immutable scientific input differs: " + name)
    output.mkdir(parents=True)
    (output / "inputs").mkdir()
    for name in pins:
        shutil.copyfile(source / name, output / "inputs" / name)
    JOB = output
    return consume()


if __name__ == "__main__":
    raise SystemExit(main())
