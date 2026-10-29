"""Fit bounded transport shards or evaluate frozen nested development predictions."""

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
    training_protocol_sha256: str,
) -> dict[str, Any]:
    """Admit ordinary zero or separately certified saved products without relabelling exit1."""
    required = {"method", "native_terminal", "plan_sha256", "training", "trials"}
    if set(row) not in (required, required | {"saved_product_admission"}):
        raise ValueError("Exact ordinary or recovered shard descriptor required")
    if (
        training_protocol_sha256
        != "7953aec717a0bf440eca6d26e5c4d9bca03e3d783a005ab311f09d3d9b4db4dd"
    ):
        raise ValueError("Exact original training protocol required")
    references = []

    def buffer(reference: dict[str, Any]) -> bytes:
        if (
            set(reference) != {"path", "sha256", "bytes"}
            or type(reference["bytes"]) is not int
            or reference["bytes"] < 0
            or not isinstance(reference["sha256"], str)
            or len(reference["sha256"]) != 64
            or any(char not in "0123456789abcdef" for char in reference["sha256"])
        ):
            raise ValueError("Exact physical shard authority pin required")
        references.append(reference)
        raw = common["checked"](repository, reference)
        if not isinstance(raw, bytes):
            raise ValueError("Scientific checked buffer must be bytes")
        return raw

    def read(reference: dict[str, Any]) -> Any:
        return common["decode"](buffer(reference))

    terminal = read(row["native_terminal"])
    stages = terminal["stages"]
    if (
        terminal["candidate"] != candidate
        or terminal["plan_sha256"] != row["plan_sha256"]
        or len(stages) != 1
        or stages[0]["timed_out"] is not False
        or terminal["source_pins_before_mismatches"]
        or terminal["source_pins_after_mismatches"]
    ):
        raise ValueError("Exact completed source-bound shard boundary required")
    if "saved_product_admission" not in row:
        if (
            type(terminal["actual_exit"]) is not int
            or terminal["actual_exit"] != 0
            or type(stages[0]["actual_exit"]) is not int
            or stages[0]["actual_exit"] != 0
        ):
            raise ValueError("Ordinary shard native zero required")
        return {"references": references, "native_terminal": row["native_terminal"]}
    certificate = read(row["saved_product_admission"])
    identities = {
        "scientific_manifest_sha256": "32330c14ee199401c96e2a9aa25269e8d13b1f17e63b7144abab65c357760930",
        "execution_manifest_sha256": "33d649879688e53d1cf1ad5bf779a56b2c33e15d549286a3b3010c92bcab520f",
    }
    if (
        certificate["schema_version"]
        != "author-love-transport-saved-product-admission.v1"
        or certificate["approved"] is not True
        or certificate["scientific_saved_products_admitted"] is not True
        or certificate["candidate"] != candidate
        or certificate["method"] != row["method"]
        or certificate["training_protocol_sha256"] != training_protocol_sha256
        or certificate["original_plan_sha256"] != row["plan_sha256"]
        or certificate["original_terminal"] != row["native_terminal"]
        or certificate["training"] != row["training"]
        or certificate["trials"] != row["trials"]
        or certificate["source_identity"] != identities
        or certificate["original_native_qualification"]
        != "refused_post_scientific_body_origin"
        or type(certificate["original_native_exit"]) is not int
        or certificate["original_native_exit"] != 1
        or type(terminal["actual_exit"]) is not int
        or terminal["actual_exit"] != 1
        or type(stages[0]["actual_exit"]) is not int
        or stages[0]["actual_exit"] != 1
    ):
        raise ValueError("Explicit independently recovered saved products required")
    original = read(certificate["original_plan"])
    if (
        certificate["original_plan"]["sha256"] != row["plan_sha256"]
        or original["candidate"] != candidate
        or original["scientific_mode"] != "fit"
        or original["transport_method"] != row["method"]
        or original["scientific_protocol"]["sha256"] != training_protocol_sha256
        or original["scientific_producer"]["sha256"]
        != "c84ec49c97fc4e66495f9dab0b83cc8bc93f4645a788bfd838a06f0c64618f05"
        or not set(identities.values())
        <= {pin["sha256"] for pin in original["input_pins"]}
    ):
        raise ValueError("Original fit source/protocol projection differs")

    def resources_and_stage(plan: dict[str, Any], observed: dict[str, Any]) -> None:
        if (
            len(plan["stages"]) != 1
            or len(observed["stages"]) != 1
            or any(
                observed["stages"][0].get(key) != value
                for key, value in plan["stages"][0].items()
            )
            or observed["resources"] != plan["resources"]
        ):
            raise ValueError("Terminal stage/resources differ from registered plan")
        values = [
            observed["output_bytes"],
            observed["completed_child_peak_rss_bytes_macos"],
            plan["resources"]["declared_storage_bytes"],
            plan["resources"]["declared_memory_bytes"],
        ]
        if (
            any(type(value) is not int or value < 0 for value in values)
            or values[0] > values[2]
            or values[1] > values[3]
        ):
            raise ValueError("Exact nonnegative bounded resource observations required")

    resources_and_stage(original, terminal)
    stderr = buffer(certificate["original_stderr"])
    stdout = buffer(certificate["original_stdout"])
    executor = original["source_runtime_executor"]["path"]
    producer = original["scientific_producer"]["path"]
    expected = (
        f'Traceback (most recent call last):\n  File "{executor}", line 55, in <module>\n'
        "    raise ValueError('Source-check imported an undeclared module: '+str(physical))\n"
        f"ValueError: Source-check imported an undeclared module: {producer}\n"
    ).encode()
    if (
        stderr != expected
        or stdout != b""
        or certificate["original_stderr"]["sha256"] != stages[0]["stderr_sha256"]
        or certificate["original_stdout"]["sha256"] != stages[0]["stdout_sha256"]
        or terminal["resources"] != original["resources"]
        or terminal["output_bytes"] > original["resources"]["declared_storage_bytes"]
        or terminal["completed_child_peak_rss_bytes_macos"]
        > original["resources"]["declared_memory_bytes"]
    ):
        raise ValueError("Only exact post-body origin refusal is recoverable")
    recovered = read(certificate["recovery_native_terminal"])
    if (
        recovered["candidate"] != candidate
        or type(recovered["actual_exit"]) is not int
        or recovered["actual_exit"] != 0
        or len(recovered["stages"]) != 1
        or any(
            type(stage["actual_exit"]) is not int
            or stage["actual_exit"] != 0
            or stage["timed_out"] is not False
            for stage in recovered["stages"]
        )
        or recovered["source_pins_before_mismatches"]
        or recovered["source_pins_after_mismatches"]
    ):
        raise ValueError("Actual new no-fit recovery native zero required")
    recovery_plan = read(certificate["recovery_plan"])
    if (
        certificate["recovery_plan"]["sha256"] != recovered["plan_sha256"]
        or recovery_plan["candidate"] != candidate
        or recovery_plan["scientific_mode"] != "saved_products_no_fit"
    ):
        raise ValueError("Registered saved-products no-fit recovery plan required")
    resources_and_stage(recovery_plan, recovered)
    review = read(certificate["independent_output_review"])
    expected_review = {
        "candidate": candidate,
        "method": row["method"],
        "training_protocol_sha256": training_protocol_sha256,
        "original_plan_sha256": row["plan_sha256"],
        "original_terminal_sha256": row["native_terminal"]["sha256"],
        "training_sha256": row["training"]["sha256"],
        "trials_sha256": row["trials"]["sha256"],
        "recovery_plan_sha256": recovered["plan_sha256"],
        "recovery_native_terminal_sha256": certificate["recovery_native_terminal"][
            "sha256"
        ],
        "source_identity": identities,
    }
    if (
        review["approved"] is not True
        or review["scientific_saved_products_admitted"] is not True
        or any(review[key] != value for key, value in expected_review.items())
    ):
        raise ValueError(
            "Independent recovery review must bind exact original and new evidence"
        )
    return {
        "references": references,
        "native_terminal": row["native_terminal"],
        "saved_product_admission": row["saved_product_admission"],
    }


def load_shards(
    common: dict[str, Any],
    repository: Path,
    reference: dict[str, Any],
    candidate: str,
    training_protocol_sha256: str,
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
        authority = admit_shard(
            common, repository, row, candidate, training_protocol_sha256
        )
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
            "admission": {
                key: value for key, value in authority.items() if key != "references"
            },
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
    if args.mode != "evaluate":
        raise ValueError("This source is a saved-training evaluation reader only")
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
    for name in (
        "training_protocol",
        "training_source_manifest",
        "training_source_projection",
    ):
        common["checked"](repository, protocol[name])
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
            args.candidate,
            protocol["training_protocol_sha256"],
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
                trained["protocol_sha256"] != protocol["training_protocol_sha256"]
                or trained["candidate"] != args.candidate
                or common["digest"](trained["logical_requests"])
                != common["digest"](logical)
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
                        "saved_product_authority": row["admission"],
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
