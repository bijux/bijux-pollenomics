"""Fit two prespecified PPE vectors or evaluate their training-only nested choice."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import runpy
from typing import Any


def admit_shard(
    common: dict[str, Any],
    repository: Path,
    row: dict[str, Any],
    candidate: str,
    protocol_sha256: str,
    protocol: dict[str, Any],
) -> dict[str, Any]:
    """Authenticate exact historical nominal or fresh PPE native authority, without relabelling."""
    source = protocol["nominal_admission_source"]
    if (
        source["sha256"]
        != "e60bc275372655b400e1ae0a92e97abb05cb36824ff64c935493a72f1b4f862a"
    ):
        raise ValueError("Exact maintained nominal admission implementation required")
    common["checked"](repository, source)
    nominal_reader = runpy.run_path(str(repository / source["path"]))
    method = row["method"]
    nominal = method == "gpm neutral"
    required = {"method", "native_terminal", "plan_sha256", "training", "trials"}
    if method not in common["METHODS"] or set(row) != (
        required | {"saved_product_admission"} if nominal else required | {"plan"}
    ):
        raise ValueError("Exact unique scenario shard namespace required")
    expected_candidate = protocol["nominal_source_candidate"] if nominal else candidate
    expected_protocol = (
        protocol["nominal_training_protocol_sha256"] if nominal else protocol_sha256
    )
    if nominal:
        admission = nominal_reader["admit_shard"](
            common, repository, row, expected_candidate, expected_protocol
        )
    else:
        admission = common["admit_new_shard"](
            repository, row, candidate, protocol_sha256, protocol
        )
    admission.setdefault("references", [row["native_terminal"]])
    admission["references"].append(source)
    return dict(admission)


def load_shards(
    common: dict[str, Any],
    repository: Path,
    reference: dict[str, Any],
    candidate: str,
    protocol: dict[str, Any],
    protocol_sha256: str,
) -> dict[str, dict[str, Any]]:
    """Preserve nominal historical identity and require fresh native zero for changed PPE."""
    descriptor = common["decode"](common["checked"](repository, reference))
    if (
        descriptor["schema_version"] != "author-love-ppe-shards.v1"
        or len(descriptor["shards"]) != 3
    ):
        raise ValueError("Exact nominal and two new PPE shard authorities required")
    result = {}
    for row in descriptor["shards"]:
        method = row["method"]
        if method in result:
            raise ValueError("Duplicate PPE scenario authority")
        nominal = method == "gpm neutral"
        expected_candidate = (
            protocol["nominal_source_candidate"] if nominal else candidate
        )
        expected_protocol = (
            protocol["nominal_training_protocol_sha256"] if nominal else protocol_sha256
        )
        admission = admit_shard(
            common, repository, row, candidate, protocol_sha256, protocol
        )
        report = common["decode"](common["checked"](repository, row["training"]))
        events = [
            common["decode"](line)
            for line in common["checked"](repository, row["trials"]).splitlines()
        ]
        attempts = report["new_attempts"]
        budget = 768 if nominal else 2496
        if (
            report["method"] != method
            or report["candidate"] != expected_candidate
            or report["protocol_sha256"] != expected_protocol
            or report["schema_version"]
            != (
                "author-love-transport-training.v1"
                if nominal
                else "author-love-ppe-training.v1"
            )
            or report["planned_new_start_slots"] != budget
            or len(attempts) != budget
            or report["actual_new_attempts"] != budget
            or report["reused_attempts"] != (1728 if nominal else 0)
            or report["request_refusals"]
            or len(report["numerical_requests"]) != 39
            or len(events) != 2 * budget
        ):
            raise ValueError(
                "Complete scenario-specific source identity and start ledger required"
            )
        for index, attempt in enumerate(attempts):
            start, finish = events[2 * index : 2 * index + 2]
            if (
                start.pop("event") != "attempt_started"
                or finish.pop("event") != "attempt_completed"
                or finish != attempt
                or any(
                    start[key] != attempt[key]
                    for key in (
                        "item_id",
                        "request_sha256",
                        "ring_index",
                        "outer_m",
                        "start_id",
                        "start",
                        "execution",
                    )
                )
            ):
                raise ValueError("PPE shard lifecycle differs")
        result[method] = {
            "training": report,
            "reference": row["training"],
            "terminal": row["native_terminal"],
            "admission": {
                key: value for key, value in admission.items() if key != "references"
            },
        }
    return result


def nominal_predictions(
    common: dict[str, Any],
    repository: Path,
    protocol: dict[str, Any],
    contexts: list[dict[str, Any]],
    baselines: tuple[str, ...],
    training_ref: dict[str, Any],
) -> list[dict[str, Any]]:
    """Reuse exact already-admitted nominal slots after current request and ancestry joins."""
    authority_ref = protocol["nominal_public_authority"]
    if (
        authority_ref["sha256"]
        != "f82f7c83447d52981bafdb63546b45840e26f60c1ade47627ea4c79e358306e8"
    ):
        raise ValueError(
            "Exact independently admitted nominal public authority required"
        )
    authority = common["decode"](common["checked"](repository, authority_ref))
    reference = protocol["nominal_prediction_freeze"]
    trace = authority["raw_trace_products"][
        "evaluation:candidate-prediction-freeze.json"
    ]
    if (
        authority["source_candidate"] != protocol["nominal_source_candidate"]
        or authority["execution"]["native_exit"] != 0
        or authority["independent_semantics"]["approved"] is not True
        or authority["independent_semantics"]["scientific_saved_products_admitted"]
        is not True
        or {key: reference[key] for key in ("sha256", "bytes")} != trace
    ):
        raise ValueError("Source-bound previously admitted nominal freeze required")
    frozen = common["decode"](common["checked"](repository, reference))
    if frozen["shard_authorities"]["gpm neutral"]["training"] != training_ref:
        raise ValueError(
            "Nominal saved training differs from admitted prediction freeze"
        )
    slots = [row for row in frozen["slots"] if row["method"] == "gpm neutral"]
    expected = {
        (
            context["kind"],
            context["outer"].test_record_ids[0],
            context["target"],
            baseline,
        ): context
        for context in contexts
        for baseline in baselines
    }
    seen = set()
    for slot in slots:
        key = (slot["kind"], slot["outer_target"], slot["target"], slot["baseline"])
        if (
            key not in expected
            or key in seen
            or common["digest"](slot["fold"])
            != common["digest"](expected[key]["fold"].as_dict())
            or slot["status"] not in {"predicted", "refused"}
        ):
            raise ValueError("Reused nominal slot support or physical ancestry changed")
        seen.add(key)
    if len(slots) != 675 or len(expected) != 675 or seen != set(expected):
        raise ValueError(
            "Complete admitted675 nominal prediction/refusal slots required"
        )
    return slots


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "prepared", "protocol", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--mode", choices=("fit", "evaluate"), required=True)
    parser.add_argument("--method")
    parser.add_argument("--shards", type=Path)
    parser.add_argument("--shards-sha256")
    args = parser.parse_args()
    directory = Path(__file__).absolute().parent
    raw = args.protocol.read_bytes()
    if hashlib.sha256(raw).hexdigest() != args.protocol_sha256:
        raise ValueError("Exact frozen scientific protocol required")
    import json

    preliminary = json.loads(raw)
    common_row = next(
        row for row in preliminary["execution_sources"] if row["path"] == "common.py"
    )
    common_path = directory / "common.py"
    if (
        any(path.is_symlink() for path in (common_path, *common_path.parents))
        or hashlib.sha256(common_path.read_bytes()).hexdigest() != common_row["sha256"]
        or common_path.stat().st_size != common_row["bytes"]
    ):
        raise ValueError("Declared scientific helper differs before import")
    common = runpy.run_path(str(common_path))
    protocol = common["decode"](raw)
    repository, prepared, output = (
        args.repository.absolute(),
        args.prepared.absolute(),
        args.output.absolute(),
    )
    if (
        ".." in output.parts
        or not output.is_relative_to(repository / "artifacts")
        or output.exists()
        or any(path.is_symlink() for path in (output, *output.parents))
    ):
        raise ValueError("Absent owned artifact output required")
    if len(args.candidate) != 40 or any(
        char not in "0123456789abcdef" for char in args.candidate
    ):
        raise ValueError("Actual registered candidate required")
    common["guard"](repository, prepared, directory, protocol)
    libraries = common["libraries"](repository)
    request_math = common["module"](directory, protocol, "requests.py")
    training = common["module"](directory, protocol, "training.py")
    selection = common["module"](directory, protocol, "selection.py")
    experiment = common["decode"](
        common["checked"](
            prepared,
            next(row for row in protocol["inputs"] if row["path"] == "experiment.json"),
        )
    )
    spec = libraries["original"]["SourceExperimentSpec"](experiment)
    contexts, groups = request_math["contexts"](libraries["original"], spec)
    output.mkdir(parents=True)
    if args.mode == "fit":
        if args.method not in common["METHODS"][1:] or args.shards is not None:
            raise ValueError("Only the two declared PPE scenarios may fit")
        weighted = request_math["weighted_experiment"](
            experiment, args.method, protocol
        )
        weighted_spec = libraries["original"]["SourceExperimentSpec"](weighted)
        numeric, logical = request_math["requests"](
            libraries["original"], weighted_spec, prepared, contexts
        )
        record = training["fit"](
            common, libraries, numeric, prepared, output, args.method, {}, {}
        )
        record.update(
            candidate=args.candidate,
            schema_version="author-love-ppe-training.v1",
            logical_requests=logical,
            profile=protocol["profile"],
            protocol_sha256=args.protocol_sha256,
            scenario_parameter_sha256=common["digest"](
                weighted["request_template"]["parameters"]
            ),
            source_input_parameters_mutated=False,
        )
        common["write"](output / "training.json", record)
    else:
        if args.method is not None or args.shards is None or args.shards_sha256 is None:
            raise ValueError("Exact nominal plus two new PPE shard descriptor required")
        shards = load_shards(
            common,
            repository,
            {
                "path": str(args.shards.absolute()),
                "sha256": args.shards_sha256,
                "bytes": args.shards.stat().st_size,
            },
            args.candidate,
            protocol,
            args.protocol_sha256,
        )
        slots = []
        for method in common["METHODS"]:
            weighted = request_math["weighted_experiment"](experiment, method, protocol)
            weighted_spec = libraries["original"]["SourceExperimentSpec"](weighted)
            numeric, logical = request_math["requests"](
                libraries["original"], weighted_spec, prepared, contexts
            )
            trained = shards[method]["training"]
            if (
                common["digest"](trained["logical_requests"])
                != common["digest"](logical)
                or set(trained["numerical_requests"]) != set(numeric)
                or (
                    method != "gpm neutral"
                    and trained["scenario_parameter_sha256"]
                    != common["digest"](weighted["request_template"]["parameters"])
                )
            ):
                raise ValueError(
                    "Saved scenario differs from current parameter/request/ancestry identities"
                )
            if method == "gpm neutral":
                slots.extend(
                    nominal_predictions(
                        common,
                        repository,
                        protocol,
                        contexts,
                        spec.baselines,
                        shards[method]["reference"],
                    )
                )
                continue
            slots.extend(
                selection["predictions"](
                    common,
                    libraries["original"],
                    weighted_spec,
                    weighted,
                    contexts,
                    groups,
                    numeric,
                    trained["numerical_requests"],
                    prepared,
                    method,
                    shards[method]["reference"],
                )
            )
        frozen = common["write"](
            output / "candidate-prediction-freeze.json",
            {
                "profile": protocol["profile"],
                "slots": slots,
                "shard_authorities": {
                    method: {
                        "training": row["reference"],
                        "native_terminal": row["terminal"],
                        "saved_product_authority": row["admission"],
                    }
                    for method, row in shards.items()
                },
                "ordering": "All1890inner and135outer PPE dispositions frozen before new inner label scoring; every site is previously exposed development data.",
            },
        )
        reopened = common["decode"](
            common["checked"](
                output,
                {
                    "path": "candidate-prediction-freeze.json",
                    "sha256": frozen["sha256"],
                    "bytes": frozen["bytes"],
                },
            )
        )
        result = selection["evaluate"](
            common,
            libraries,
            experiment,
            contexts,
            groups,
            reopened["slots"],
            prepared,
            protocol["inputs"],
            output,
            frozen,
        )
        changed = [shards[method]["training"] for method in common["METHODS"][1:]]
        result.update(
            candidate=args.candidate,
            schema_version="author-love-nested-ppe-development.v1",
            protocol_sha256=args.protocol_sha256,
            methods=list(common["METHODS"]),
            prior_attempts_reused=2496,
            max_new_start_slots=4992,
            actual_new_attempts=sum(row["actual_new_attempts"] for row in changed),
            new_attempts_accepted=sum(
                attempt["accepted"] is True
                for row in changed
                for attempt in row["new_attempts"]
            ),
            new_attempts_refused=sum(
                attempt["accepted"] is False
                for row in changed
                for attempt in row["new_attempts"]
            ),
            total_unique_attempts=7488,
            nominal_source_candidate=protocol["nominal_source_candidate"],
            nominal_training_protocol_sha256=protocol[
                "nominal_training_protocol_sha256"
            ],
            parameter_sensitivity_scope=protocol["evidence_scope"],
        )
        common["write"](output / "report.json", result)
    common["guard"](repository, prepared, directory, protocol)


if __name__ == "__main__":
    main()
