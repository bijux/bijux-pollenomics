"""Authenticate the finite original/cohort custody and exact native comparison support."""

from __future__ import annotations

from collections import Counter
import csv
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
from typing import Any

BASELINES = ("training_mean", "nearest_site", "inverse_distance_squared")

ROLES = {
    "original_capture",
    "original_report",
    "original_folds",
    "original_dispositions",
    "original_predictions",
    "original_preparations",
    "original_scores",
    "original_common",
    "original_outer",
    "original_review",
    "cohort_authority",
    "cohort_protocol",
    "cohort_report",
    "cohort_freeze",
}

SUPPORT = (
    "declared_target_forward_rings",
    "declared_target_inversion_rings",
    "deposition_units",
    "distances_km",
    "forward_method_profile",
    "full_k",
    "full_terrestrial_fraction",
    "geometry_profile",
    "local_support_radius_m",
    "outer_fold",
    "predictor_group_ids",
    "preparation_profile",
    "regional_anchor_group_id",
    "regional_anchor_record_id",
    "regional_cover",
    "regional_cutoff_m",
    "regional_identity_policy",
    "regional_identity_source_record_ids",
    "regional_value_source_record_ids",
    "ring_bounds_m",
    "support_profile",
    "target_geometry_sha256",
)

FORWARD = (
    "geometry_input_ids",
    "local_k",
    "method_profile",
    "parameter_input_ids",
    "ppe",
    "regional_deposition",
    "taxa",
    "temporal_support_id",
    "terrestrial_fraction",
)


def require(value: object, reason: str) -> None:
    if not value:
        raise ValueError("Saved method comparison: " + reason)


def decode(raw: bytes) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, item in items:
            require(key not in result, "duplicate metadata key")
            result[key] = item
        return result

    def nonfinite(_token: str) -> None:
        raise ValueError("Nonfinite JSON token")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical(value: object) -> str:
    return digest(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    )


def same_pin(left: dict[str, Any], right: dict[str, Any]) -> bool:
    return (
        left["sha256"] == right["sha256"]
        and type(left["bytes"]) is int
        and left["bytes"] == right["bytes"]
    )


def read(repository: Path, row: dict[str, Any]) -> bytes:
    require(set(row) == {"path", "sha256", "bytes"}, "exact input pin fields required")
    name = PurePosixPath(row["path"])
    require(
        not name.is_absolute()
        and ".." not in name.parts
        and name.as_posix() == row["path"]
        and "\\" not in row["path"],
        "normalized repository input path required",
    )
    path = repository / name
    require(
        not any(p.is_symlink() for p in (path, *path.parents))
        and path.is_file()
        and path.stat().st_nlink == 1,
        "physical independent input required",
    )
    require(
        type(row["bytes"]) is int
        and 0 <= row["bytes"] <= 32 * 1024**2
        and path.stat().st_size == row["bytes"],
        "finite input length required",
    )
    body = path.read_bytes()
    require(
        len(body) == row["bytes"] and digest(body) == row["sha256"],
        "input identity changed",
    )
    return body


def join_support(
    old: dict[str, Any],
    new: dict[str, Any],
    fold: dict[str, Any],
    raw: dict[str, Any],
    geometry: dict[str, Any],
    site: dict[str, Any],
    taxa: list[str],
) -> dict[str, Any]:
    require(
        all(old[key] == new[key] for key in SUPPORT),
        "native geometry/kernel/anchor support differs",
    )
    require(
        all(
            old["forward_inputs"][key] == new["forward_inputs"][key] for key in FORWARD
        ),
        "forward count/parameter/temporal support differs",
    )
    require(
        old["outer_fold"] == fold
        and fold["test_record_ids"] == [site["record_id"]]
        and site["record_id"] not in fold["train_record_ids"],
        "exact fold and own-target exclusion required",
    )
    require(
        raw["taxa"] == taxa and raw["sample"]["site_id"] == site["site_id"],
        "native taxon/site axis differs",
    )
    counts = raw["sample"]["counts"]
    require(
        len(counts) == 30
        and all(type(v) is int and v >= 0 for v in counts)
        and sum(counts) > 0,
        "original positive integer pollen counts required",
    )
    require(
        old["target_geometry_sha256"] == site["geometry"]["sha256"]
        and old["declared_target_forward_rings"] == geometry["forward_rings"]
        and old["declared_target_inversion_rings"] == geometry["inversion_rings"],
        "target geometry identity differs",
    )
    require(list(old["forward_inputs"]["taxa"]) == taxa, "forward taxon order differs")
    sample = raw["sample"]
    require(
        {k: v for k, v in sample.items() if k != "counts"}
        == geometry["sample_metadata"],
        "native sample chronology/geometry metadata differs",
    )
    return {
        "record_id": site["record_id"],
        "site_id": site["site_id"],
        "identity_keys": site["identity_keys"],
        "raw_sha256": site["raw"]["sha256"],
        "geometry_sha256": site["geometry"]["sha256"],
        "sample_id": sample["sample_id"],
        "bin_id": sample["bin_id"],
        "age_support_bp": sample["age_support_bp"],
        "age_type": sample["age_type"],
        "chronology_evidence_id": sample["chronology_evidence_id"],
        "coordinate": sample["coordinate"],
        "observed_total_count": sum(counts),
        "taxon_count": 30,
        "taxon_axis_sha256": canonical(taxa),
        "counts_sha256": canonical(dict(zip(taxa, counts, strict=True))),
        "native_geometry_support_sha256": canonical({k: old[k] for k in SUPPORT}),
        "forward_support_sha256": canonical(
            {k: old["forward_inputs"][k] for k in FORWARD}
        ),
        "original_engine_build_id": old["forward_inputs"]["engine_build_id"],
        "cohort_engine_build_id": new["forward_inputs"]["engine_build_id"],
        "engine_build_ids_equal": old["forward_inputs"]["engine_build_id"]
        == new["forward_inputs"]["engine_build_id"],
    }


def unique(
    rows: list[dict[str, Any]], fields: tuple[str, ...]
) -> dict[tuple[Any, ...], dict[str, Any]]:
    result = {tuple(row[key] for key in fields): row for row in rows}
    require(len(result) == len(rows), "duplicate fold/site/baseline membership")
    return result


def admit(bodies: dict[str, bytes], protocol: dict[str, Any]) -> dict[str, Any]:
    require(
        set(protocol["inputs"]) == ROLES and len(protocol["prepared_inputs"]) == 37,
        "finite fourteen results/authority plus37 input contract required",
    )
    data = {role: decode(bodies[role]) for role in ROLES - {"original_dispositions"}}
    capture, authority = data["original_capture"], data["cohort_authority"]
    common, outer, review = (
        data[name] for name in ("original_common", "original_outer", "original_review")
    )
    require(
        all(
            type(row["actual_exit"]) is int and row["actual_exit"] == 0
            for row in (common, outer)
        )
        and outer["common_actual_exit"] == 0
        and common["before_pin_mismatches"] == []
        and common["after_pin_mismatches"] == [],
        "original actual source execution must remain successful",
    )
    require(
        common["candidate"]
        == outer["candidate"]
        == review["candidate"]
        == protocol["original_execution"]["candidate"]
        and common["plan_sha256"]
        == outer["plan_sha256"]
        == protocol["original_execution"]["plan_sha256"]
        and outer["common_terminal"]["sha256"]
        == protocol["inputs"]["original_common"]["sha256"],
        "original execution authority join differs",
    )
    require(
        review["all_eleven_products_scientific_values_equal"] is True
        and type(review["target_exclusion_and_prediction_chain_verified"]) is int
        and review["target_exclusion_and_prediction_chain_verified"] == 42,
        "original independent scientific preservation required",
    )
    execution = authority["execution"]
    require(
        all(
            type(execution[k]) is int and execution[k] == 0
            for k in ("native_exit", "common_exit", "outer_exit")
        )
        and all(
            execution[k] is True
            for k in (
                "source_before_after_equal",
                "inputs_before_after_equal",
                "runtime_before_after_equal",
            )
        ),
        "successful independently admitted cohort execution required",
    )
    for role, product in (
        ("cohort_report", "report"),
        ("cohort_freeze", "prediction_freeze"),
    ):
        require(
            same_pin(
                protocol["inputs"][role],
                authority["products"][product]["original_reference"],
            ),
            "cohort result authority differs",
        )
    require(
        same_pin(protocol["inputs"]["cohort_protocol"], authority["protocol"]),
        "executed cohort protocol differs",
    )
    old_report, new_report, frozen, selected = (
        data[k]
        for k in (
            "original_report",
            "cohort_report",
            "cohort_freeze",
            "cohort_protocol",
        )
    )
    require(
        old_report["source_experiment_sha256"]
        == protocol["prepared_inputs"]["experiment.json"]["sha256"]
        and old_report["prediction_manifest_sha256"]
        == protocol["original_execution"]["prediction_manifest_sha256"]
        and old_report["score_manifest_sha256"]
        == protocol["original_execution"]["score_manifest_sha256"],
        "original source/prediction/score identity differs",
    )
    original_projection = next(
        row
        for row in capture["report_outputs"]
        if row["path"] == protocol["inputs"]["original_report"]["path"]
    )
    require(
        same_pin(
            original_projection["published"], protocol["inputs"]["original_report"]
        ),
        "original compact publication differs from actual native result",
    )
    original_disposition_projection = next(
        row
        for row in capture["report_outputs"]
        if row["path"] == protocol["inputs"]["original_dispositions"]["path"]
    )
    require(
        same_pin(
            original_disposition_projection["published"],
            protocol["inputs"]["original_dispositions"],
        ),
        "original published fold dispositions differ",
    )
    old_members = {row["path"]: row for row in capture["members"]}
    for role, row in protocol["inputs"].items():
        if role.startswith("original_") and role not in {
            "original_capture",
            "original_report",
            "original_dispositions",
        }:
            name = row["path"].removeprefix(protocol["original_capture_prefix"])
            require(
                name in old_members and same_pin(old_members[name], row),
                "original retained member identity differs",
            )
    for row in protocol["prepared_inputs"].values():
        retained = row["path"].removeprefix(protocol["original_capture_prefix"])
        require(
            retained in old_members and same_pin(old_members[retained], row),
            "original prepared source identity differs",
        )
    require(
        sorted((row["path"], row["sha256"], row["bytes"]) for row in selected["inputs"])
        == sorted(
            (name, row["sha256"], row["bytes"])
            for name, row in protocol["prepared_inputs"].items()
        ),
        "cohort and original source37 identities differ",
    )
    experiment = decode(bodies["prepared:experiment.json"])
    taxa = experiment["request_template"]["taxa"]
    require(
        len(taxa) == len(set(taxa)) == 30
        and tuple(experiment["baselines"]) == BASELINES
        and tuple(selected["baselines"]) == BASELINES,
        "exact30 taxa/three declared baselines required",
    )
    folds = unique(data["original_folds"], ("fold_id",))
    new_folds = unique(frozen["folds"], ("fold_id",))
    require(
        len(folds) == 15 and new_folds == folds,
        "exact fifteen original/cohort fold identities required",
    )
    sites = {site["record_id"]: site for site in experiment["sites"]}
    require(len(sites) == 15, "exact native site population required")
    dispositions = list(
        csv.DictReader(io.StringIO(bodies["original_dispositions"].decode()))
    )
    old_dispositions = unique(dispositions, ("fold_id",))
    require(
        set(old_dispositions) == set(folds)
        and Counter(row["status"] for row in dispositions)
        == {"predicted": 14, "refused": 1},
        "original14 scored/one refused population required",
    )
    require(
        old_report["predicted_folds"] == 14
        and old_report["refused_folds"] == 1
        and new_report["predicted_folds"] == 15
        and new_report["refused_folds"] == 0,
        "published original and cohort fold counts differ",
    )
    old_predictions = unique(
        data["original_predictions"], ("fold_id", "record_id", "baseline")
    )
    old_scores = unique(data["original_scores"], ("fold_id", "record_id", "baseline"))
    new_slots = unique(frozen["slots"], ("fold_id", "record_id", "baseline"))
    new_scores = unique(new_report["scores"], ("fold_id", "record_id", "baseline"))
    preparations = unique(data["original_preparations"], ("fold_id",))
    require(
        len(old_predictions) == 42
        and len(old_scores) == 45
        and len(new_slots) == 45
        and len(new_scores) == 45
        and len(preparations) == 14,
        "complete prediction and refusal inventories required",
    )
    return {
        "folds": folds,
        "sites": sites,
        "old_dispositions": old_dispositions,
        "new_slots": new_slots,
        "new_scores": new_scores,
        "old_predictions": old_predictions,
        "old_scores": old_scores,
        "preparations": preparations,
        "taxa": taxa,
    }
