"""Fixed thirty-two-start temporal LOVE sensitivity with complete frozen outcomes."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
from typing import Any

from bijux_pollenomics.analysis.lra.engine.discovery import (
    load_engine,
    required_capability_for_profile,
)
from bijux_pollenomics.analysis.lra.outputs.identity import (
    capture_code_identity,
    verify_code_identity,
)
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    verify_consumed_sources,
)

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/"
Json = dict[str, Any]
SEARCH = {
    "starts_per_ring": 32,
    "rings": 2,
    "maxiter": 300,
    "max_search_evaluations": 16000,
    "ftol": 1e-8,
    "root_seed": 7,
    "selection": "converged_finite_feasible_minimum_then_start_id",
    "composition": "unrounded_x_divided_by_sum_after_original_1e-6_gate",
}


def supplied(path: Path, checksum: str) -> Json:
    return {
        "path": str(path.absolute()),
        "sha256": checksum,
        "bytes": path.stat().st_size,
    }


def checked(repository: Path, row: Json) -> bytes:
    path = Path(row["path"])
    path = path if path.is_absolute() else repository / path
    if (
        ".." in path.parts
        or not path.is_relative_to(repository)
        or any(p.is_symlink() for p in (path, *path.parents))
        or not path.is_file()
        or path.stat().st_nlink != 1
        or set(row) != {"path", "sha256", "bytes"}
        or type(row["bytes"]) is not int
        or not 0 <= row["bytes"] <= 32 * 1024 * 1024
    ):
        raise ValueError("Bounded confined source pin required")
    raw = path.read_bytes()
    if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("Declared scientific source bytes differ")
    return raw


def temporal_boundary(repository: Path, protocol: Json) -> Json:
    name = PREFIX + "temporal-development/replay.py"
    selected = [row for row in protocol["maintained_sources"] if row["path"] == name]
    if len(selected) != 1:
        raise ValueError("Exact temporal input boundary source required")
    checked(repository, selected[0])
    return runpy.run_path(
        str(repository / name), run_name="bijux_temporal_fixed_input_boundary"
    )


def libraries(
    repository: Path, protocol: Json
) -> tuple[Json, Json, Json, Json, Json, Json]:
    temporal = temporal_boundary(repository, protocol)
    source = Path(__file__).absolute().parent
    if {p.name for p in source.iterdir()} != {
        "replay.py",
        "training.py",
        "regional.py",
    }:
        raise ValueError(
            "Exact three-file temporal fixed-start source namespace required"
        )
    if {row["path"] for row in protocol["source_files"]} != {
        "replay.py",
        "training.py",
        "regional.py",
    }:
        raise ValueError("All three scientific sources must be bound before import")
    for row in protocol["source_files"]:
        temporal["read"](source, row)
    for row in protocol["maintained_sources"]:
        temporal["read"](repository, row)
    if (
        protocol["schema_version"] != "author-love-temporal-fixed-start-protocol.v1"
        or protocol["optimizer"] != SEARCH
    ):
        raise ValueError("Original matched fixed-start scientific protocol required")
    topology, _ = temporal["libraries"](
        repository,
        json.loads(temporal["read"](repository, protocol["temporal_protocol"])),
    )
    regional = runpy.run_path(
        str(source / "regional.py"), run_name="bijux_temporal_saved_regional"
    )
    training = runpy.run_path(
        str(source / "training.py"), run_name="bijux_temporal_fixed_training"
    )
    helper = runpy.run_path(
        str(repository / PREFIX / "optimizer-start-sensitivity/replay.py"),
        run_name="bijux_original_fixed_starts",
    )
    original = runpy.run_path(
        str(repository / PREFIX / "optimizer-gradient/replay.py"),
        run_name="bijux_original_local_objective",
    )
    math = runpy.run_path(
        str(repository / PREFIX / "development-fold/training.py"),
        run_name="bijux_original_start_acceptance",
    )
    return (
        temporal,
        topology,
        regional,
        training,
        helper,
        {"original": original, "math": math},
    )


def journal(path: Path) -> Any:
    stream = path.open("x")

    def emit(row: Json) -> None:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())

    return stream, emit


def score(
    repository: Path,
    prepared: Path,
    output: Path,
    spec: Any,
    temporal: Json,
    topology: Json,
    slots: list[Json],
    request_pin: Json,
    input_rows: list[Json],
) -> tuple[Json, list[Json]]:
    """Complete window freeze precedes post-freeze scoring decode, not other-fold training."""
    write, read = temporal["write"], temporal["read"]
    frozen = write(
        output / "prediction-freeze.json",
        {
            "window": topology["manifest"]["window"],
            "request_manifest": request_pin,
            "slots": slots,
            "ordering": "All window prediction/refusal slots fsynced before post-freeze scoring outcome access; the same sources are training elsewhere.",
        },
    )
    reopened = json.loads(read(repository, frozen))
    existing = runpy.run_path(
        str(repository / PREFIX / "cohort-development/replay.py"),
        run_name="bijux_temporal_scoring_boundary",
    )
    scores = []
    stream, emit = journal(output / "outcome-access.jsonl")
    with stream:
        for site in spec.sites:
            rows = [
                row
                for row in reopened["slots"]
                if row["record_id"] == site.record.record_id
                and row["status"] == "predicted"
            ]
            if not rows:
                continue
            emit(
                {
                    "record_id": site.record.record_id,
                    "prediction_freeze": frozen,
                    "ordering": "complete_window_freeze_reopened_before_outcome_decode",
                }
            )
            counts = existing["outcome_counts"](
                prepared,
                site,
                spec,
                rows[0]["prediction"],
                [{**row, "path": Path(row["path"]).name} for row in input_rows],
            )
            for row in rows:
                scores.append(
                    {
                        "fold_id": row["fold_id"],
                        "record_id": site.record.record_id,
                        "baseline": row["baseline"],
                        **existing["score_pollen"](
                            row["prediction"]["pollen_fraction"], counts
                        ).as_dict(),
                    }
                )
    return frozen, scores


def run(
    repository: Path,
    prepared: Path,
    window: int,
    protocol: Json,
    projected_pin: Json,
    request_pin: Json,
    output: Path,
    mode: str,
    metadata_pin: Json | None,
    candidate: str | None,
) -> Json:
    temporal, topology_library, regional_library, training_library, helper, numeric = (
        libraries(repository, protocol)
    )
    read, write = temporal["read"], temporal["write"]
    if projected_pin["sha256"] != protocol["projected_authority"]["sha256"]:
        raise ValueError("Exact original projected input authority required")
    _, input_rows = temporal["admitted"](repository, prepared, window, projected_pin)
    experiment = json.loads((prepared / "experiment.json").read_bytes())
    spec = SourceExperimentSpec(experiment)
    old_protocol = json.loads(read(repository, protocol["temporal_protocol"]))
    topology = topology_library["build"](
        spec, prepared, window, old_protocol["profile"]
    )
    observed = {
        **topology["manifest"],
        "projected_authority": protocol["original_projected_argument"],
    }
    if request_pin["sha256"] != protocol["request_manifests"][str(window)][
        "sha256"
    ] or topology_library["digest"](
        json.loads(read(repository, request_pin))
    ) != topology_library["digest"](observed):
        raise ValueError("Exact previously admitted temporal request topology required")
    regional, reuse = regional_library["load"](
        repository, temporal, topology, window, protocol["uniform_authority"]
    )
    expected = {4: (13, 143, 23, 1472, 39), 6: (14, 168, 25, 1600, 42)}[window]
    counts = observed["counts"]
    if (
        counts["sites"],
        counts["logical_requests"],
        counts["unique_requests"],
        len(regional) * 64,
        counts["prediction_slots"],
    ) != expected:
        raise ValueError("Actual admitted temporal population changed")
    readiness = {
        "window": window,
        "request_manifest": request_pin,
        "counts": counts,
        "new_attempts": len(regional) * 64,
        "reused_attempts": 0,
        "regional_reuse": reuse,
        "new_REVEALS_calls": 0,
    }
    write(output / "readiness.json", readiness)
    if mode == "inspect":
        return {
            "schema_version": "author-love-temporal-fixed-start-readiness.v1",
            **readiness,
            "model_calls": 0,
            "fits": 0,
            "scores": 0,
        }
    if metadata_pin is None or candidate is None:
        raise ValueError("Actual current source metadata preflight required")
    preflight = json.loads(read(repository, metadata_pin))
    if (
        preflight.get("schema_version")
        != "development-input-isolation-metadata-preflight.v1"
        or preflight.get("approved") is not True
        or preflight.get("source_inputs_before_after_unchanged") is not True
        or preflight.get("candidate") != candidate
        or preflight.get("scientific_api_calls") != 0
        or preflight.get("fits") != 0
    ):
        raise ValueError("Current admitted source discovery preflight required")
    method_profile = spec.template()["method_profile"]
    if not isinstance(method_profile, str):
        raise ValueError("Literal admitted method profile required")
    binding = load_engine(
        required_capability=required_capability_for_profile(method_profile)
    )
    identity = capture_code_identity(binding)
    if (
        identity.payload()["runtime_environment"]["bijux-pollenomics"]
        != preflight["host_version"]
        or binding.version != preflight["lra_version"]
    ):
        raise ValueError("Actual source metadata differs")
    rows, attempts = [], []
    trial_stream, emit = journal(output / "trials.jsonl")
    request_stream, emit_request = journal(output / "request-events.jsonl")
    with trial_stream, request_stream:
        for checksum, item in sorted(topology["numeric"].items()):
            emit_request({"event": "request_started", "request_sha256": checksum})
            try:
                row, new_attempts = training_library["fit"](
                    numeric["original"],
                    helper,
                    numeric["math"],
                    item,
                    prepared,
                    regional[checksum],
                    emit,
                    topology_library["digest"],
                )
            except Exception as error:
                emit_request(
                    {
                        "event": "request_failed",
                        "request_sha256": checksum,
                        "error_type": type(error).__name__,
                        "error": str(error),
                    }
                )
                raise
            rows.append(row)
            attempts.extend(new_attempts)
            emit_request(
                {
                    "event": "request_completed",
                    "request_sha256": checksum,
                    "training_row_sha256": topology_library["digest"](row),
                }
            )
    if len(attempts) != expected[3]:
        raise ValueError("Complete new fixed-start lifecycle required")
    training_pin = write(
        output / "training.json",
        {
            **readiness,
            "training": rows,
            "attempts": attempts,
            "optimizer": SEARCH,
            "candidate": candidate,
        },
    )
    products = {row["request_sha256"]: row for row in rows}
    slots = training_library["predictions"](
        spec, topology, products, prepared, experiment
    )
    if len(slots) != expected[4] or len(
        {(row["fold_id"], row["baseline"]) for row in slots}
    ) != len(slots):
        raise ValueError("Complete per-window prediction/refusal inventory required")
    verify_consumed_sources(
        spec,
        prepared,
        pollen_record_ids=topology["consumed_pollen"],
        geometry_record_ids=topology["consumed_geometry"],
        template_used=True,
    )
    frozen, scores = score(
        repository,
        prepared,
        output,
        spec,
        temporal,
        topology,
        slots,
        request_pin,
        input_rows,
    )
    verify_code_identity(binding, identity)
    for row in [*input_rows, *reuse["read_inputs"], *protocol["maintained_sources"]]:
        read(repository, row)
    return {
        "schema_version": "author-love-temporal-fixed-start-development.v1",
        "window": window,
        "counts": counts,
        "new_attempts": len(attempts),
        "reused_attempts": 0,
        "accepted_attempts": sum(row["accepted"] for row in attempts),
        "refused_attempts": sum(not row["accepted"] for row in attempts),
        "training": training_pin,
        "prediction_freeze": frozen,
        "request_manifest": request_pin,
        "projected_authority": projected_pin,
        "uniform_source_epoch": "d60500153ff589db3b93c38fe3bddde46c2994a9",
        "candidate": candidate,
        "predicted_slots": sum(row["status"] == "predicted" for row in slots),
        "refused_slots": sum(row["status"] == "refused" for row in slots),
        "scores": scores,
        "scientific_acceptance": "not_evaluated",
        "new_REVEALS_calls": 0,
        "exposure": "Previously exposed development only; independently frozen within-window protocols, no cross-window global winner or independent vegetation accuracy. Source-declared calibrated-BP bins; epoch/calibration/age uncertainty unqualified.",
        "code_identity_sha256": topology_library["digest"](identity.payload()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "run"))
    for name in (
        "repository",
        "prepared",
        "protocol",
        "projected-admission",
        "request-manifest",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("protocol", "projected-admission", "request-manifest"):
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--window", choices=(4, 6), type=int, required=True)
    parser.add_argument("--metadata-preflight", type=Path)
    parser.add_argument("--metadata-preflight-sha256")
    parser.add_argument("--candidate")
    args = parser.parse_args()
    repository = args.repository.absolute()
    protocol = json.loads(
        checked(repository, supplied(args.protocol, args.protocol_sha256))
    )
    boundary = temporal_boundary(repository, protocol)
    output = boundary["location"](repository, str(args.output.absolute()))
    if output.exists() or not output.is_relative_to(repository / "artifacts"):
        raise ValueError("Fresh owned scientific output required")
    if args.mode == "run" and (
        args.metadata_preflight is None
        or args.metadata_preflight_sha256 is None
        or args.candidate is None
    ):
        raise ValueError("Actual run metadata and candidate required before execution")
    output.mkdir(parents=True)
    result = run(
        repository,
        args.prepared.absolute(),
        args.window,
        protocol,
        supplied(args.projected_admission, args.projected_admission_sha256),
        supplied(args.request_manifest, args.request_manifest_sha256),
        output,
        args.mode,
        supplied(args.metadata_preflight, args.metadata_preflight_sha256)
        if args.metadata_preflight is not None
        else None,
        args.candidate,
    )
    boundary["write"](output / "report.json", result)


if __name__ == "__main__":
    main()
