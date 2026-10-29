"""Within-window physical comparisons using unchanged deterministic uniform LOVE."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import runpy
from typing import Any

from bijux_pollenomics.analysis.lra.api import LRABatchLimits, run_lra_batch
from bijux_pollenomics.analysis.lra.engine.discovery import (
    load_engine,
    required_capability_for_profile,
)
from bijux_pollenomics.analysis.lra.outputs.identity import (
    capture_code_identity,
    verify_code_identity,
)
from bijux_pollenomics.analysis.lra_validation.contracts import ValidationRefusal
from bijux_pollenomics.analysis.lra_validation.experiments.configuration import (
    SourceExperimentSpec,
)
from bijux_pollenomics.analysis.lra_validation.experiments.inputs import (
    verify_consumed_sources,
)
from bijux_pollenomics.analysis.lra_validation.experiments.prediction import (
    predict_fold,
)
from bijux_pollenomics.analysis.lra_validation.experiments.reconstruction import (
    FoldFits,
    extract_reconstruction,
)

PREFIX = "docs/report/pollen-reconstruction/author-lra-constrained/"
PROFILE_SHA = "036048ee628888b26858bc0fd4f3213294ec4c0ad0507e310aa8f57831085273"
Json = dict[str, Any]


def location(root: Path, name: str) -> Path:
    path = Path(name)
    if not name or path.as_posix() != name or ".." in path.parts:
        raise ValueError("Normalized scientific reference required")
    result = path if path.is_absolute() else root / path
    if not result.is_relative_to(root) or any(
        p.is_symlink() for p in (result, *result.parents)
    ):
        raise ValueError("Unlinked owned scientific reference required")
    return result


def read(root: Path, row: Json) -> bytes:
    path = location(root, row["path"])
    if (
        set(row) != {"path", "sha256", "bytes"}
        or not path.is_file()
        or path.stat().st_nlink != 1
        or type(row["bytes"]) is not int
        or not 0 <= row["bytes"] <= 32 * 1024 * 1024
    ):
        raise ValueError("Bounded exact scientific pin required")
    raw = path.read_bytes()
    if len(raw) != row["bytes"] or hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError("Scientific input bytes changed")
    return raw


def write(path: Path, value: Any) -> Json:
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n").encode()
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {
        "path": str(path),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }


def libraries(repository: Path, protocol: Json) -> tuple[Any, Any]:
    source = Path(__file__).absolute().parent
    declared = protocol["source_files"]
    present = {p.name for p in source.iterdir()}
    allowed = {
        "replay.py",
        "topology.py",
        "protocol.json",
        "README.md",
        "report.json",
        "trace-index.json",
    }
    if (
        {row["path"] for row in declared} != {"replay.py", "topology.py"}
        or not {"replay.py", "topology.py"}.issubset(present)
        or not present.issubset(allowed)
        or any(
            p.is_symlink() or not p.is_file() or p.stat().st_nlink != 1
            for p in source.iterdir()
        )
    ):
        raise ValueError(
            "Exact temporal sources and bounded scientific companions required"
        )
    for row in declared:
        read(source, row)
    for row in protocol["maintained_sources"]:
        read(repository, row)
    topology = runpy.run_path(
        str(source / "topology.py"), run_name="bijux_temporal_topology"
    )
    existing = runpy.run_path(
        str(repository / PREFIX / "cohort-development/replay.py"),
        run_name="bijux_temporal_outcome_boundary",
    )
    if (
        protocol["schema_version"] != "author-love-temporal-development-protocol.v1"
        or topology["digest"](protocol["profile"]) != PROFILE_SHA
    ):
        raise ValueError("Frozen uniform physical protocol required")
    return topology, existing


def admitted(
    repository: Path, prepared: Path, window: int, authority_row: Json
) -> tuple[Json, list[Json]]:
    authority = json.loads(read(repository, authority_row))
    if (
        authority.get("schema_version")
        != "author-love-temporal-projected-output-authority.v1"
        or authority.get("candidate") != "d863e6c939fab8eed3e53c4dc01c52953bc2434a"
        or authority.get("approved") is not True
        or type(authority.get("actual_exit")) is not int
        or authority["actual_exit"] != 0
        or authority.get("scientific_saved_products_admitted") is not True
    ):
        raise ValueError("Actual admitted constrained30 inputs required")
    for key in ("observation", "observer_execution", "observer_source_review"):
        proof = json.loads(read(repository, authority[key]))
        if key == "observation" and (
            proof.get("approved") is not True
            or any(
                proof.get(k) != authority.get(k)
                for k in ("jobs", "summaries", "products")
            )
        ):
            raise ValueError("Projected authority differs from raw admission")
        if key == "observer_execution" and proof.get("actual_exit") != 0:
            raise ValueError("Actual projected observer execution zero required")
        if key == "observer_source_review" and proof.get("approved") is not True:
            raise ValueError("Approved projected observer source required")
    if (
        window not in (4, 6)
        or prepared
        != repository
        / f"artifacts/science/author-love-temporal-constrained-execution/TW{window}/native/products"
    ):
        raise ValueError("Declared native window input location required")
    products = authority["products"][str(window)]
    rows = list(products.values())
    if (
        len(rows) != {4: 33, 6: 35}[window]
        or {p.name for p in prepared.iterdir()} != set(products)
        or any(
            location(repository, row["path"]) != prepared / name
            for name, row in products.items()
        )
    ):
        raise ValueError("Complete constrained scientific namespace required")
    for row in rows:
        read(repository, row)
    return authority, rows


def predictions(
    spec: SourceExperimentSpec, topology: Json, products: dict[str, Any], prepared: Path
) -> list[Json]:
    """Keep baseline-specific typed refusals; unknown source failures propagate."""
    slots: list[Json] = []
    groups = topology["groups"]
    for context in topology["contexts"]:
        fold, anchor, predictors = (
            context["fold"],
            context["anchor"],
            context["predictors"],
        )
        records, refused = [], []
        for site, checksum in zip(predictors, context["requests"], strict=True):
            item = products[checksum]
            if item.item_status == "refused":
                refused.append(item.as_dict())
                continue
            try:
                composition, regional, evidence = extract_reconstruction(
                    item.product, topology["numeric"][checksum].payload(), spec
                )
            except ValidationRefusal as exc:
                if exc.reason_code not in {
                    "invalid_composition",
                    "unclosed_composition",
                }:
                    raise
                refused.append(
                    {
                        "request_sha256": checksum,
                        "reason_code": exc.reason_code,
                        "detail": str(exc),
                    }
                )
                continue
            records.append(
                (
                    site,
                    composition,
                    regional,
                    {
                        "record_id": site.record.record_id,
                        "group_id": groups[site.record.record_id],
                        "request_sha256": checksum,
                        **evidence,
                    },
                )
            )
        if refused:
            slots.extend(
                {
                    "fold_id": fold.fold_id,
                    "record_id": fold.test_record_ids[0],
                    "baseline": baseline,
                    "status": "refused",
                    "reason_code": "training_request_or_composition_refused",
                    "training_refusals": refused,
                }
                for baseline in spec.baselines
            )
            continue
        regional = records[0][2]
        if any(row[2] != regional for row in records):
            raise ValueError("Shared deterministic regional background changed")
        fits = FoldFits(
            anchor,
            predictors,
            {groups[row[0].record.record_id]: row[1] for row in records},
            regional,
            tuple(row[3] for row in records),
            {"profile": "source-declared-uniform-slsqp", "host_products": True},
        )
        target = next(
            site
            for site in spec.sites
            if site.record.record_id == fold.test_record_ids[0]
        )
        experiment: Json = json.loads((prepared / "experiment.json").read_bytes())
        for baseline in spec.baselines:
            one = SourceExperimentSpec({**experiment, "baselines": [baseline]})
            try:
                rows, geometry = predict_fold(
                    one,
                    fold,
                    target,
                    fits,
                    groups,
                    input_root=prepared,
                    consumed_geometry=topology["consumed_geometry"],
                )
            except ValidationRefusal as exc:
                if not (
                    (
                        exc.reason_code == "forward_model_refused"
                        and str(exc)
                        == "Forward deposition has nonfinite or zero total mass"
                    )
                    or exc.reason_code
                    in {"invalid_composition", "unclosed_composition"}
                ):
                    raise
                slots.append(
                    {
                        "fold_id": fold.fold_id,
                        "record_id": target.record.record_id,
                        "baseline": baseline,
                        "status": "refused",
                        "reason_code": exc.reason_code,
                        "detail": str(exc),
                    }
                )
                continue
            if len(rows) != 1 or rows[0]["baseline"] != baseline:
                raise ValueError("Exact singleton maintained baseline result required")
            slots.append(
                {
                    "fold_id": fold.fold_id,
                    "record_id": target.record.record_id,
                    "baseline": baseline,
                    "status": "predicted",
                    "prediction": rows[0],
                    "geometry": geometry,
                }
            )
    return slots


def run(
    repository: Path,
    prepared: Path,
    window: int,
    protocol: Json,
    authority_pin: Json,
    request_pin: Json,
    output: Path,
    inspect_only: bool = False,
    metadata_pin: Json | None = None,
    candidate: str | None = None,
) -> Json:
    topology_library, existing = libraries(repository, protocol)
    authority, input_rows = admitted(repository, prepared, window, authority_pin)
    spec = SourceExperimentSpec(json.loads((prepared / "experiment.json").read_bytes()))
    topology = topology_library["build"](spec, prepared, window, protocol["profile"])
    observed = {**topology["manifest"], "projected_authority": authority_pin}
    if inspect_only:
        return {
            "actual_exit": 0,
            "request_manifest": write(output / "requests.json", observed),
            "actual_counts": observed["counts"],
            "forecast_matches_actual": observed["forecast_matches_actual"],
            "model_calls": 0,
        }
    if topology_library["digest"](
        json.loads(read(repository, request_pin))
    ) != topology_library["digest"](observed):
        raise ValueError("Actual frozen request topology changed before models")
    if metadata_pin is None or candidate is None:
        raise ValueError("Actual current metadata preflight required in run mode")
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
        raise ValueError(
            "Actual source-metadata/discovery provenance preflight required"
        )
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
        raise ValueError("Actual host/LRA source metadata differs")
    items = [item for _, item in sorted(topology["numeric"].items())]
    batch = run_lra_batch(
        items,
        input_root=prepared,
        cache_root=output / "cache",
        report_root=output / "batch",
        limits=LRABatchLimits(max_workers=1, max_items=len(items)),
    )
    batch_pin = write(output / "batch-result.json", batch.as_dict())
    if (
        batch.interrupted
        or any(row.item_status not in {"completed", "refused"} for row in batch.items)
        or {row.request_sha256 for row in batch.items} != set(topology["numeric"])
    ):
        raise RuntimeError(
            "Batch incomplete or source worker failed; durable batch retained"
        )
    for batch_item in batch.items:
        error = batch_item.as_dict().get("error")
        if batch_item.item_status == "refused" and (
            not isinstance(error, dict)
            or error.get("reason_code") != "optimizer_nonconvergence"
        ):
            raise RuntimeError(
                "Unexpected host refusal; durable original batch retained"
            )
    pool = {row.request_sha256: row for row in batch.items}
    slots = predictions(spec, topology, pool, prepared)
    if len(slots) != observed["counts"]["prediction_slots"] or len(
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
    frozen = write(
        output / "prediction-freeze.json",
        {
            "window": window,
            "request_manifest": request_pin,
            "slots": slots,
            "ordering": "All window prediction/refusal slots fsynced before outcome access; source is training elsewhere.",
        },
    )
    reopened = json.loads(read(repository, frozen))
    scores = []
    with (output / "outcome-access.jsonl").open("x") as journal:
        for site in spec.sites:
            rows = [
                row
                for row in reopened["slots"]
                if row["record_id"] == site.record.record_id
                and row["status"] == "predicted"
            ]
            if not rows:
                continue
            journal.write(
                json.dumps(
                    {
                        "record_id": site.record.record_id,
                        "prediction_freeze": frozen,
                        "ordering": "complete_window_freeze_reopened_before_outcome_decode",
                    },
                    sort_keys=True,
                )
                + "\n"
            )
            journal.flush()
            os.fsync(journal.fileno())
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
    verify_code_identity(binding, identity)
    for row in input_rows:
        read(repository, row)
    for row in protocol["maintained_sources"]:
        read(repository, row)
    return {
        "schema_version": "author-love-temporal-development.v1",
        "window": window,
        "counts": observed["counts"],
        "request_manifest": request_pin,
        "projected_authority": authority_pin,
        "batch": batch_pin,
        "prediction_freeze": frozen,
        "predicted_slots": sum(row["status"] == "predicted" for row in slots),
        "refused_slots": sum(row["status"] == "refused" for row in slots),
        "scores": scores,
        "scientific_acceptance": "not_evaluated",
        "exposure": "Prior-exposed source development; within-window estimands only, no global temporal winner or independent vegetation accuracy.",
        "code_identity_sha256": topology_library["digest"](identity.payload()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("inspect", "run"))
    for name in ("repository", "prepared", "protocol", "projected-admission", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--window", type=int, choices=(4, 6), required=True)
    parser.add_argument("--protocol-sha256", required=True)
    parser.add_argument("--projected-admission-sha256", required=True)
    parser.add_argument("--request-manifest", type=Path)
    parser.add_argument("--request-manifest-sha256")
    parser.add_argument("--metadata-preflight", type=Path)
    parser.add_argument("--metadata-preflight-sha256")
    parser.add_argument("--candidate")
    args = parser.parse_args()
    repository = args.repository.absolute()
    output = location(repository, str(args.output.absolute()))
    if (
        not output.is_relative_to(repository / "artifacts")
        or output.exists()
        or (
            args.mode == "run"
            and (
                args.request_manifest is None
                or args.request_manifest_sha256 is None
                or args.metadata_preflight is None
                or args.metadata_preflight_sha256 is None
                or args.candidate is None
            )
        )
    ):
        raise ValueError(
            "Fresh owned output and run-mode actual request proof required"
        )

    def supplied(path: Path, checksum: str) -> Json:
        return {
            "path": str(path.absolute()),
            "sha256": checksum,
            "bytes": path.stat().st_size,
        }

    protocol = json.loads(
        read(repository, supplied(args.protocol, args.protocol_sha256))
    )
    authority = supplied(args.projected_admission, args.projected_admission_sha256)
    request = (
        supplied(args.request_manifest, args.request_manifest_sha256)
        if args.request_manifest is not None
        else {}
    )
    output.mkdir(parents=True)
    result = run(
        repository,
        args.prepared.absolute(),
        args.window,
        protocol,
        authority,
        request,
        output,
        inspect_only=args.mode == "inspect",
        metadata_pin=supplied(args.metadata_preflight, args.metadata_preflight_sha256)
        if args.metadata_preflight is not None
        else None,
        candidate=args.candidate,
    )
    write(output / "report.json", result)


if __name__ == "__main__":
    main()
