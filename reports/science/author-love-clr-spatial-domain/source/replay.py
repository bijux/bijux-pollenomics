"""Record maintained CLR-domain refusals without fitting a numerical model or scoring."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import sys
from typing import Any

SCENARIOS = (("clr-ridge-20km", 20.0), ("clr-ridge-100km", 100.0))
SOURCES = {"replay.py", "inputs.py"}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def attempt(context: dict[str, Any], scenario: str, scale: float) -> dict[str, Any]:
    from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
    from bijux_pollenomics.analysis.lra_validation.spatial import (
        SpatialConfig,
        fit_spatial_model,
    )

    require(
        (scenario, scale) in SCENARIOS
        and any(
            value == 0
            for values in context["compositions"].values()
            for value in values.values()
        ),
        "Expected source-bound zero domain required before API invocation",
    )
    try:
        fit_spatial_model(
            context["fold"],
            context["compositions"],
            context["coordinates"],
            config=SpatialConfig(scale, 1.0, context["support_id"]),
            input_ids=context["input_ids"],
            dependency_graph=context["dependency_graph"],
            admitted_external_ids=context["admitted_external_ids"],
            predictor_group_ids=context["predictor_group_ids"],
        )
    except ValidationRefusal as error:
        if error.reason_code != "spatial_zero_composition_unsupported":
            raise
        return {
            key: context[key]
            for key in (
                "kind",
                "outer_target",
                "target",
                "fold_sha256",
                "request_sha256s",
                "zero_containing_predictors",
            )
        } | {
            "method": scenario,
            "status": "refused",
            "reason_code": error.reason_code,
            "reason": str(error),
            "fit_API_invoked": True,
            "successful_ridge_solve": False,
            "prediction": None,
        }
    raise ValueError("Unexpected successful model for the frozen zero-domain protocol")


def choose(
    contexts: list[dict[str, Any]],
    dispositions: list[dict[str, Any]],
    groups: dict[str, str],
    selector: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lookup = {
        (context["kind"], context["outer_target"], context["target"]): context
        for context in contexts
    }
    expected = {
        (kind, outer, target, name)
        for kind, outer, target in lookup
        for name, _ in SCENARIOS
    }
    observed = {
        (row["kind"], row["outer_target"], row["target"], row["method"])
        for row in dispositions
    }
    require(
        len(dispositions) == len(observed) == 450
        and observed == expected
        and all(
            row["status"] == "refused"
            and row["reason_code"] == "spatial_zero_composition_unsupported"
            for row in dispositions
        ),
        "Exact independent450 expected refusal slots required; never mask successful or foreign outcomes",
    )
    inner = []
    for row in dispositions:
        if row["kind"] != "inner":
            continue
        fold = lookup[(row["kind"], row["outer_target"], row["target"])]["fold"]
        inner.append(
            {
                "method": row["method"],
                "outer_target": row["outer_target"],
                "inner_target": row["target"],
                "inner_train_record_ids": fold.train_record_ids,
                "inner_train_group_ids": fold.train_group_ids,
                "baseline": "clr-wgs84-rbf-ridge-v1",
                "bin_id": "author-TW5",
                "status": "refused",
                "metrics": None,
                "prediction_sha256": None,
            }
        )
    require(
        len(dispositions) == 450 and len(inner) == 420,
        "All450 candidate/420 inner refusals must precede choice",
    )
    selections = []
    for context in contexts:
        if context["kind"] != "outer":
            continue
        selected = selector(
            context["fold"],
            "clr-wgs84-rbf-ridge-v1",
            [row for row in inner if row["outer_target"] == context["target"]],
            tuple(name for name, _ in SCENARIOS),
            groups,
        )
        require(
            selected["selected_method"] is None
            and selected["status"] == "refused"
            and all(
                row["complete_inner_predictions"] == 0
                and row["mean_inner_total_variation"] is None
                for row in selected["ranking"]
            ),
            "No eligible scale or tuning winner exists",
        )
        selections.append(
            selected
            | {
                "reason_code": "no_eligible_spatial_scale",
                "outer_outcome_decoded": False,
                "outer_score": None,
            }
        )
    require(len(selections) == 15, "Fifteen frozen outer refusal dispositions required")
    return inner, selections


def source_guard(protocol: dict[str, Any]) -> dict[str, Any]:
    directory = Path(__file__).absolute().parent
    require(
        {path.name for path in directory.iterdir()} == SOURCES
        and len(protocol["execution_sources"]) == 2
        and {row["path"] for row in protocol["execution_sources"]} == SOURCES,
        "Exact two-source scientific namespace required",
    )
    for row in protocol["execution_sources"]:
        path = directory / row["path"]
        require(
            path.is_file()
            and path.stat().st_nlink == 1
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Independent scientific source required",
        )
        raw = path.read_bytes()
        require(
            len(raw) == row["bytes"]
            and hashlib.sha256(raw).hexdigest() == row["sha256"],
            "Scientific source changed before private helper import",
        )
    return runpy.run_path(str(directory / "inputs.py"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    require(
        all(
            path.is_absolute()
            and ".." not in path.parts
            and not any(p.is_symlink() for p in (path, *path.parents))
            for path in (args.repository, args.prepared, args.protocol, args.output)
        ),
        "Absolute independent scientific paths required",
    )
    require(
        args.protocol.is_file()
        and args.protocol.stat().st_nlink == 1
        and args.protocol.stat().st_size <= 32 * 1024**2,
        "Physical bounded protocol required",
    )
    raw = args.protocol.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == args.protocol_sha256,
        "Exact frozen protocol required",
    )
    protocol = json.loads(raw)
    require(
        protocol["schema_version"] == "author-love-clr-spatial-scale-protocol.v1"
        and protocol["scenarios"]
        == [
            {"id": name, "length_scale_km": scale, "ridge_penalty": 1.0}
            for name, scale in SCENARIOS
        ]
        and re.fullmatch("[a-f0-9]{40}", args.candidate) is not None,
        "Finite prespecified CLR scale/refusal protocol required",
    )
    helper = source_guard(protocol)
    protocol = helper["decode"](raw)
    plan_path = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"])
    plan_raw = plan_path.read_bytes()
    require(
        hashlib.sha256(plan_raw).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Same registered plan buffer required",
    )
    plan = helper["decode"](plan_raw)
    self_pin = next(
        row for row in protocol["execution_sources"] if row["path"] == "replay.py"
    )
    require(
        plan["candidate"] == args.candidate
        and plan["repository"] == str(args.repository)
        and plan["scientific_mode"] == "clr_saved_domain_refusal"
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["scientific_producer"]
        == {**self_pin, "path": str(Path(__file__).absolute())}
        and plan["expected_new_scientific_calls"]
        == protocol["expected_new_scientific_calls"]
        and plan["maximum_new_attempts"] == 0
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(raw),
        }
        and args.output == Path(plan["output"]) / "products"
        and not args.output.exists(),
        "Exact registered current CLR consumer/output required",
    )
    require(
        args.output.is_relative_to(args.repository / "artifacts"),
        "Absent owned product output required",
    )
    contexts, groups, summary, references = helper["load"](
        args.repository, args.prepared, protocol
    )
    selector = runpy.run_path(
        str(args.repository / protocol["borrowed_sources"]["selector"]["path"])
    )["choose"]
    before = helper["digest"](
        [
            {
                key: context[key]
                for key in (
                    "kind",
                    "outer_target",
                    "target",
                    "fold_sha256",
                    "request_sha256s",
                    "zero_containing_predictors",
                )
            }
            for context in contexts
        ]
    )
    dispositions = [
        attempt(context, name, scale)
        for context in contexts
        for name, scale in SCENARIOS
    ]
    require(
        len(dispositions) == 450
        and all(
            row["status"] == "refused"
            and row["reason_code"] == "spatial_zero_composition_unsupported"
            and row["fit_API_invoked"] is True
            and row["successful_ridge_solve"] is False
            for row in dispositions
        ),
        "Complete450 actual maintained API refusals required",
    )
    args.output.mkdir(parents=True)

    def write(name: str, value: Any) -> dict[str, Any]:
        body = (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        with (args.output / name).open("xb") as stream:
            stream.write(body)
        return {
            "path": name,
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        }

    candidates = write(
        "candidate-refusals.json",
        {
            "schema_version": "author-love-clr-candidate-refusals.v1",
            "candidate": args.candidate,
            "protocol_sha256": args.protocol_sha256,
            "dispositions": dispositions,
            "raw_outcome_decodes": 0,
            "score_calls": 0,
        },
    )
    inner, selections = choose(contexts, dispositions, groups, selector)
    selection = write(
        "selection-freeze.json",
        {
            "schema_version": "author-love-clr-selection-freeze.v1",
            "candidate_freeze": candidates,
            "inner_dispositions": inner,
            "selected_outer_dispositions": selections,
            "raw_outcome_decodes": 0,
            "score_calls": 0,
        },
    )
    require(
        before
        == helper["digest"](
            [
                {
                    key: context[key]
                    for key in (
                        "kind",
                        "outer_target",
                        "target",
                        "fold_sha256",
                        "request_sha256s",
                        "zero_containing_predictors",
                    )
                }
                for context in contexts
            ]
        ),
        "Context identities changed during API calls",
    )
    source_guard(protocol)
    for row in protocol["source_pins"]:
        helper["checked"](args.repository, row)
    require(
        plan_path.read_bytes() == plan_raw,
        "Registered plan buffer changed during scientific body",
    )
    report = {
        "schema_version": "author-love-clr-spatial-domain-refusal.v1",
        "candidate": args.candidate,
        "protocol_sha256": args.protocol_sha256,
        "source_base": protocol["source_base"],
        "scenarios": protocol["scenarios"],
        "counts": {
            "saved_nominal_requests": 39,
            "logical_ancestry_rows": 2715,
            "contexts": 225,
            "maintained_fit_API_attempts": 450,
            "actual_expected_domain_refusals": 450,
            "successful_ridge_solves": 0,
            "new_REVEALS_runs": 0,
            "new_LOVE_runs": 0,
            "new_optimizer_attempts": 0,
            "new_kernel_calls": 0,
            "new_forward_calls": 0,
            "new_score_calls": 0,
            "inner_dispositions": 420,
            "outer_candidate_dispositions": 30,
            "selected_outer_dispositions": 15,
            "selected_outer_refusals": 15,
        },
        "saved_domain": summary,
        "candidate_freeze": candidates,
        "selection_freeze": selection,
        "original_nominal": {
            "source_candidate": protocol["nominal_candidate"],
            "native_exit": 1,
            "native_qualification": "refused_post_scientific_body_origin",
            "separate_saved_product_recovery_native_exit": 0,
            "original_full_later_import_origins_and_final_return": "not established",
        },
        "custody": {
            "original_input_namespace": 37,
            "raw_input_bytes_hashed_for_custody": True,
            "raw_outcome_body_decodes": 0,
            "geometry_metadata_decodes": 15,
            "original_nominal_admission_references": references,
        },
        "scientific_acceptance": "not_evaluated",
        "scope": "Dataset-specific incompatibility of these admitted selected zero-containing compositions with the unchanged positive-only CLR model.450 actual API calls are not450 successful fits. No imputation, alternative covariance, tuning winner, new forward/scoring, generic CLR invalidity, untouched/vegetation/rights/human or whole V3-24 acceptance.",
    }
    write("report.json", report)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "maintained_fit_API_attempts": 450,
                "successful_ridge_solves": 0,
                "selected_outer_refusals": 15,
                "scientific_acceptance": "not_evaluated",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
