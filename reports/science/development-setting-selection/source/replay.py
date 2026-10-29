"""Freeze joint TW5 setting choices before decoding any saved outer outcome."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
import sys
from typing import Any

Json = dict[str, Any]
CALLS = {
    "optimizer_calls": 0,
    "kernel_calls": 0,
    "forward_calls": 0,
    "scoring_calls": 0,
}


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def source_guard(protocol: Json, directory: Path) -> tuple[Json, Json]:
    names = {"replay.py", "sources.py", "choice.py"}
    require(
        {p.name for p in directory.iterdir()} == names
        and len(protocol["execution_sources"]) == 3
        and {r["path"] for r in protocol["execution_sources"]} == names,
        "Exact three-source selection namespace required",
    )
    for row in protocol["execution_sources"]:
        path = directory / row["path"]
        require(
            path.is_file()
            and path.stat().st_nlink == 1
            and not any(p.is_symlink() for p in (path, *path.parents)),
            "Independent scientific source required",
        )
        body = path.read_bytes()
        require(
            len(body) == row["bytes"]
            and hashlib.sha256(body).hexdigest() == row["sha256"],
            "Source changed before helper import",
        )
    return runpy.run_path(str(directory / "sources.py")), runpy.run_path(
        str(directory / "choice.py")
    )


def run(root: Path, protocol: Json, output: Path, sources: Json, choice: Json) -> Json:
    """Use persisted admitted metrics only; selection never receives outer labels."""
    data = sources["load"](root, protocol)
    predicate_ref = protocol["eligible_metric_source"]
    predicate_path = root / predicate_ref["path"]
    sources["checked"](root, predicate_ref)
    eligible = runpy.run_path(str(predicate_path))["eligible_metric"]
    choices = [
        choice["choose"](
            target,
            data["records"],
            data["groups"],
            protocol["catalogue"],
            data["inner_rows"],
            eligible,
        )
        for target in sorted(data["records"])
    ]
    selected = choice["freeze_choices"](choices, data["outer_slots"], sources["digest"])
    output.mkdir(parents=True)

    def write(name: str, value: Any) -> Json:
        body = (
            json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n"
        ).encode()
        path = output / name
        with path.open("xb") as stream:
            stream.write(body)
            stream.flush()
            os.fsync(stream.fileno())
        return {
            "path": str(path),
            "sha256": hashlib.sha256(body).hexdigest(),
            "bytes": len(body),
        }

    evidence = write(
        "selection-evidence.json",
        {
            "schema_version": "development-setting-inner-evidence.v1",
            "catalogue": protocol["catalogue"],
            "physical_inner_rows": data["inner_evidence"],
            "source_equivalent_aliases": [
                p
                for p in protocol["catalogue"]
                if p["eligibility"] == "source_equivalent_alias"
            ],
            "setting_dispositions": protocol["setting_dispositions"],
            "raw_metric_errors_and_deviance_retained": True,
        },
    )
    frozen = write(
        "selected-prediction-freeze.json",
        {
            "schema_version": "development-setting-choice-freeze.v1",
            "choices": choices,
            "slots": selected,
            "inner_evidence": evidence,
            "ordering": "All fifteen setting/spatial choices and original selected prediction/refusal identities persisted before any saved outer outcome JSON decoding.",
        },
    )
    reopened = sources["decode"](sources["checked"](root, frozen))
    require(
        reopened["choices"] == choices and reopened["slots"] == selected,
        "Persisted choice/prediction freeze changed",
    )
    with (output / "outcome-access.jsonl").open("x") as access:

        def before_decode(reference: Json) -> None:
            access.write(
                json.dumps(
                    {
                        "event": "saved_outer_outcome_decode",
                        "choice_freeze": frozen,
                        "report": reference,
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            access.flush()
            os.fsync(access.fileno())

        outcomes = sources["outcomes"](
            root, protocol, reopened["slots"], eligible, before_decode
        )
    reused = write(
        "outer-outcome-reuse.json",
        {
            "schema_version": "development-setting-saved-outcomes.v1",
            "choice_freeze": frozen,
            **outcomes,
        },
    )
    for axis in protocol["axes"]:
        for key in ("authority", "inner_scores", "candidate_freeze", "report"):
            sources["checked"](root, axis[key])
    sources["qualify_auxiliary"](root, protocol)
    summary = {
        "declared_settings": 16,
        "same_TW5_declared_pairs": 32,
        "unique_physical_candidate_profiles": 7,
        "unique_physical_scored_pairs": 21,
        "source_equivalent_alias_pairs": 3,
        "prerequisite_refused_pairs": 8,
        "planned_inner_pair_dispositions": 6720,
        "retained_physical_inner_rows": 4410,
        "nominal_inner_rows_deduplicated": 630,
        "planned_outer_pair_dispositions": 480,
        "physical_outer_slots": 315,
        "pair_choices": 15,
        "selected_predictions": sum(s["status"] == "predicted" for s in selected),
        "selected_refusals": sum(s["status"] != "predicted" for s in selected),
        "new_calls": CALLS,
    }
    write(
        "report.json",
        {
            "schema_version": "development-setting-selection.v1",
            "summary": summary,
            "choice_freeze": frozen,
            "inner_evidence": evidence,
            "outcomes": reused,
            "setting_dispositions": protocol["setting_dispositions"],
            "nominal_execution_scope": "Original nominal70dd native1 and separately admitted saved recovery0 stay distinct. Aliases reuse original prediction IDs and metrics, never new model execution.",
            "scope": "Original common-TW5 equal-inner meanTV candidate/spatial selection on prior-exposed development records only. Complete fourteen-inner coverage required. TW4/TW6 remain separate estimands; legacy/circular remain nonranked. No new fitting, scoring, forward calculation, independent vegetation accuracy or uncertainty calibration.",
        },
    )
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    args = parser.parse_args()
    require(
        all(
            p.is_absolute()
            and ".." not in p.parts
            and not any(q.is_symlink() for q in (p, *p.parents))
            for p in (args.repository, args.protocol, args.output)
        ),
        "Normalized independent scientific paths required",
    )
    require(
        args.protocol.stat().st_nlink == 1 and args.protocol.stat().st_size <= 1024**2,
        "Bounded independent scientific protocol required",
    )
    body = args.protocol.read_bytes()
    require(
        hashlib.sha256(body).hexdigest() == args.protocol_sha256,
        "Exact scientific protocol required",
    )
    protocol = json.loads(body)
    sources, choice = source_guard(protocol, Path(__file__).absolute().parent)
    protocol = sources["decode"](body)
    require(
        protocol["schema_version"] == "development-setting-selection-protocol.v1"
        and protocol["expected_new_scientific_calls"] == CALLS
        and len(protocol["catalogue"]) == 32,
        "Finite original selection protocol required",
    )
    plan_body = Path(os.environ["BIJUX_ATLAS_REGISTERED_PLAN"]).read_bytes()
    require(
        hashlib.sha256(plan_body).hexdigest()
        == os.environ["BIJUX_ATLAS_REGISTERED_SHA256"],
        "Same registered plan buffer required",
    )
    plan = sources["decode"](plan_body)
    producer = next(
        r for r in protocol["execution_sources"] if r["path"] == "replay.py"
    )
    require(
        plan["candidate"] == args.candidate
        and plan["repository"] == str(args.repository)
        and plan["scientific_arguments"] == sys.argv[1:]
        and plan["scientific_mode"] == "saved_development_setting_selection"
        and plan["scientific_producer"]
        == {**producer, "path": str(Path(__file__).absolute())}
        and plan["scientific_protocol"]
        == {
            "path": str(args.protocol),
            "sha256": args.protocol_sha256,
            "bytes": len(body),
        }
        and plan["maximum_new_attempts"] == 0
        and plan["expected_new_scientific_calls"] == CALLS
        and args.output == Path(plan["output"]) / "products"
        and args.output.is_relative_to(args.repository / "artifacts")
        and not args.output.exists(),
        "Exact registered saved-selection route/fresh output required",
    )
    print(
        json.dumps(
            run(args.repository, protocol, args.output, sources, choice), sort_keys=True
        )
    )


if __name__ == "__main__":
    main()
