"""Fit bounded transport shards or evaluate frozen nested development predictions."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import runpy
from typing import Any


def load_shards(
    common: dict[str, Any], repository: Path, reference: dict[str, Any]
) -> dict[str, dict[str, Any]]:
    descriptor = common["decode"](common["checked"](repository, reference))
    if (
        descriptor["schema_version"] != "author-love-transport-shards.v1"
        or len(descriptor["shards"]) != 5
    ):
        raise ValueError("Five actual separately completed transport shards required")
    result = {}
    for row in descriptor["shards"]:
        method = row["method"]
        if method not in common["METHODS"] or method in result:
            raise ValueError("Exact unique transport shard membership required")
        terminal = common["decode"](
            common["checked"](repository, row["native_terminal"])
        )
        if (
            type(terminal["actual_exit"]) is not int
            or terminal["actual_exit"] != 0
            or terminal["plan_sha256"] != row["plan_sha256"]
            or any(
                stage["actual_exit"] != 0 or stage["timed_out"] is not False
                for stage in terminal["stages"]
            )
        ):
            raise ValueError("Actual source-bound shard native zero required")
        if (
            terminal["source_pins_before_mismatches"]
            or terminal["source_pins_after_mismatches"]
        ):
            raise ValueError("Shard source/input custody failed")
        report = common["decode"](common["checked"](repository, row["training"]))
        events = [
            common["decode"](raw)
            for raw in common["checked"](repository, row["trials"]).splitlines()
        ]
        attempts = report["new_attempts"]
        if (
            report["method"] != method
            or report["schema_version"] != "author-love-transport-training.v1"
            or report["planned_new_start_slots"]
            != (768 if method == "gpm neutral" else 2496)
            or len(attempts) != report["planned_new_start_slots"]
            or report["reused_attempts"] != (1728 if method == "gpm neutral" else 0)
            or report["request_refusals"]
            or len(report["numerical_requests"]) != 39
            or len(events) != 2 * len(attempts)
            or report["actual_new_attempts"] != len(attempts)
        ):
            raise ValueError("Complete shard request/attempt ledger required")
        for index, attempt in enumerate(attempts):
            started, finished = events[2 * index : 2 * index + 2]
            if (
                started.pop("event") != "attempt_started"
                or finished.pop("event") != "attempt_completed"
                or finished != attempt
                or any(
                    started[k] != attempt[k]
                    for k in (
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
                raise ValueError("Shard lifecycle disagreement")
        result[method] = {
            "training": report,
            "reference": row["training"],
            "terminal": row["native_terminal"],
        }
    return result


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
        any(p.is_symlink() for p in (common_path, *common_path.parents))
        or hashlib.sha256(common_path.read_bytes()).hexdigest() != common_row["sha256"]
    ):
        raise ValueError("Declared finite source helper differs before import")
    common = runpy.run_path(str(common_path))
    protocol = common["decode"](raw)
    repository = args.repository.absolute()
    prepared = args.prepared.absolute()
    output = args.output.absolute()
    if (
        ".." in output.parts
        or not output.is_relative_to(repository / "artifacts")
        or output.exists()
        or any(p.is_symlink() for p in (output, *output.parents))
    ):
        raise ValueError("Absent owned artifact output required")
    if len(args.candidate) != 40 or any(
        x not in "0123456789abcdef" for x in args.candidate
    ):
        raise ValueError("Actual registered candidate identity required")
    common["guard"](repository, prepared, directory, protocol)
    libraries = common["libraries"](repository)
    request_math = common["module"](directory, protocol, "requests.py")
    train_math = common["module"](directory, protocol, "training.py")
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
        if args.method not in common["METHODS"] or args.shards is not None:
            raise ValueError("One exact transport shard required")
        weighted = request_math["weighted_experiment"](experiment, args.method)
        weighted_spec = libraries["original"]["SourceExperimentSpec"](weighted)
        numeric, logical = request_math["requests"](
            libraries["original"], weighted_spec, prepared, contexts
        )
        reused, previous = train_math["previous"](
            common, repository, protocol, libraries
        )
        record = train_math["fit"](
            common, libraries, numeric, prepared, output, args.method, reused, previous
        )
        record.update(
            candidate=args.candidate,
            schema_version="author-love-transport-training.v1",
            logical_requests=logical,
            profile=protocol["profile"],
            protocol_sha256=args.protocol_sha256,
        )
        common["write"](output / "training.json", record)
    else:
        if args.method is not None or args.shards is None or args.shards_sha256 is None:
            raise ValueError("Exact completed five-shard descriptor required")
        shards = load_shards(
            common,
            repository,
            {
                "path": str(args.shards.absolute()),
                "sha256": args.shards_sha256,
                "bytes": args.shards.stat().st_size,
            },
        )
        all_slots = []
        for method in common["METHODS"]:
            weighted = request_math["weighted_experiment"](experiment, method)
            weighted_spec = libraries["original"]["SourceExperimentSpec"](weighted)
            numeric, logical = request_math["requests"](
                libraries["original"], weighted_spec, prepared, contexts
            )
            trained = shards[method]["training"]
            if (
                trained["protocol_sha256"] != args.protocol_sha256
                or trained["candidate"] != args.candidate
                or trained["logical_requests"] != logical
                or set(trained["numerical_requests"]) != set(numeric)
            ):
                raise ValueError(
                    "Saved shard differs from exact current request/ancestry identities"
                )
            all_slots.extend(
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
                "slots": all_slots,
                "shard_authorities": {
                    method: {
                        "training": row["reference"],
                        "native_terminal": row["terminal"],
                    }
                    for method, row in shards.items()
                },
                "ordering": "All3150inner and225outer candidate prediction/refusal dispositions before new label scoring. Numeric training legitimately uses a site in other folds; no global-unread claim.",
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
        result.update(
            candidate=args.candidate,
            schema_version="author-love-nested-transport-development.v1",
            protocol_sha256=args.protocol_sha256,
            methods=list(common["METHODS"]),
            prior_attempts_reused=1728,
            max_new_start_slots=10752,
            actual_new_attempts=sum(
                row["training"]["actual_new_attempts"] for row in shards.values()
            ),
            new_attempts_accepted=sum(
                attempt["accepted"] is True
                for row in shards.values()
                for attempt in row["training"]["new_attempts"]
            ),
            new_attempts_refused=sum(
                attempt["accepted"] is False
                for row in shards.values()
                for attempt in row["training"]["new_attempts"]
            ),
            total_unique_attempts=12480,
        )
        common["write"](output / "report.json", result)
    common["guard"](repository, prepared, directory, protocol)


if __name__ == "__main__":
    main()
