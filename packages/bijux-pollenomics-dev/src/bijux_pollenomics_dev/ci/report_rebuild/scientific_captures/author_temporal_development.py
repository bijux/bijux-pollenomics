"""Admit compact temporal point-pollen results without opening private raw traces."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from bijux_pollenomics_dev.ci.rebuild_reports import InventoryEntry
from bijux_pollenomics_dev.ci.report_rebuild.contracts import (
    JsonObject,
    ReportRebuildError,
)
from bijux_pollenomics_dev.ci.report_rebuild.ownership import _regular_confined_file

PREFIX = (
    "docs/report/pollen-reconstruction/author-lra-constrained/temporal-development/"
)
OWNER = (
    "pollen-reconstruction/author-lra-constrained/temporal-development/report-products"
)
AUTHORITY = "reports/science/source-cohorts/author-love-temporal-development.json"
PRODUCTS = ("report.json", "trace-index.json")
AUTHORITY_SHA256: str | None = (
    "565e7cbb494dab8721913ab6148a14c78fa2aeb3d97b5e6cce497f7533e8569b"
)
SOURCE_EPOCH = "d60500153ff589db3b93c38fe3bddde46c2994a9"
INPUT_EPOCH = "d863e6c939fab8eed3e53c4dc01c52953bc2434a"
PROTOCOL_SHA256 = "deb9c4a592f5dcc974e4624aafeaf50cbaad5f3dd407a8d6ac44f24e47c1aae2"
PROFILE_SHA256 = "036048ee628888b26858bc0fd4f3213294ec4c0ad0507e310aa8f57831085273"
METHODS = ("training_mean", "nearest_site", "inverse_distance_squared")
COUNTS = {4: (13, 143, 23, 39), 6: (14, 168, 25, 42)}
SOURCES = {
    "replay.py": {
        "sha256": "4b3d156408e97300b956df35abfe8b8738e09decdbcc82bbc36802e3c8d49590",
        "bytes": 20626,
    },
    "topology.py": {
        "sha256": "868078de872b1e9d6aa2ee0f7d8f142da90573aed9d2d03a74045bdd98f23820",
        "bytes": 6558,
    },
    "protocol.json": {"sha256": PROTOCOL_SHA256, "bytes": 7170},
}
Json = dict[str, Any]


def require(condition: object, reason: str) -> None:
    """Refuse retained evidence that violates its declared contract."""
    if not condition:
        raise ReportRebuildError("Temporal development: " + reason)


def encoded(value: Any) -> bytes:
    """Encode deterministic retained metadata without nonfinite JSON values."""
    return (
        json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"
    ).encode()


def digest(value: Any) -> str:
    """Return the exact retained-source byte digest."""
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def identity(row: Json) -> tuple[str, int]:
    """Validate the declared retained-source identity."""
    checksum, size = row.get("sha256"), row.get("bytes")
    require(
        isinstance(checksum, str)
        and len(checksum) == 64
        and all(c in "0123456789abcdef" for c in checksum)
        and type(size) is int
        and size >= 0,
        "exact object identity required",
    )
    assert isinstance(checksum, str) and isinstance(size, int)
    return checksum, size


def composition(values: Json, taxa: list[str]) -> None:
    """Read the declared composition under its finite-value and axis constraints."""
    require(
        set(values) == set(taxa)
        and all(
            type(x) in (int, float) and math.isfinite(x) and 0 <= x <= 1
            for x in values.values()
        )
        and abs(math.fsum(values.values()) - 1) <= 1e-9,
        "closed named thirty-taxon fractions required",
    )


def validate_score(
    prediction: Json, counts: Json, score: Json, taxa: list[str]
) -> None:
    """Check declared scoring fields, native types and numerical identities."""
    composition(prediction, taxa)
    require(
        set(counts) == set(taxa)
        and all(type(x) is int and x >= 0 for x in counts.values()),
        "original integer observed counts required",
    )
    total = sum(counts.values())
    require(0 < total <= 2**53, "positive exactly representable count total required")
    errors = {key: prediction[key] - counts[key] / total for key in sorted(taxa)}
    values = list(errors.values())
    expected = {
        "mae_fraction": math.fsum(abs(x) for x in values) / 30,
        "rmse_fraction": math.sqrt(math.fsum(x * x for x in values) / 30),
        "bias_fraction": math.fsum(values) / 30,
        "total_variation": math.fsum(abs(x) for x in values) / 2,
    }
    require(
        score.get("target") == "pollen_composition"
        and score.get("status") == "scored"
        and type(score.get("taxon_count")) is int
        and score["taxon_count"] == score.get("scored_taxon_count") == 30
        and score.get("missing_observed_taxa") == []
        and type(score.get("observed_total_count")) is int
        and score["observed_total_count"] == total,
        "score posture or taxon/count denominator differs",
    )

    def near(actual: Any, target: float, bound: float = 2e-12) -> bool:
        return (
            type(actual) in (int, float)
            and math.isfinite(actual)
            and math.isclose(actual, target, rel_tol=2e-12, abs_tol=bound)
        )

    require(
        all(near(score.get(key), value) for key, value in expected.items()),
        "saved metric differs from vector/count arithmetic",
    )
    signed = score.get("signed_error_by_taxon")
    require(
        isinstance(signed, list)
        and len(signed) == 30
        and all(
            isinstance(row, list)
            and len(row) == 2
            and row[0] == key
            and near(row[1], error)
            for row, (key, error) in zip(signed, errors.items(), strict=True)
        ),
        "signed-error axis or value differs",
    )
    impossible = any(counts[key] > 0 and prediction[key] == 0 for key in taxa)
    require(
        score.get("zero_probability_positive_count") is impossible,
        "impossible-probability flag differs",
    )
    if impossible:
        require(
            score.get("count_conditioned_deviance") is None,
            "impossible deviance must remain null",
        )
    else:
        deviance = max(
            0.0,
            2
            * math.fsum(
                counts[key]
                * (math.log(counts[key]) - math.log(total) - math.log(prediction[key]))
                for key in taxa
                if counts[key]
            ),
        )
        require(
            near(score.get("count_conditioned_deviance"), deviance, 2e-8),
            "count-conditioned deviance differs",
        )


def validate_window(window: Json, summary: Json, taxa: list[str]) -> None:
    """Check a saved temporal window and its exact source-membership bounds."""
    number = window["window"]
    require(
        type(number) is int and number in COUNTS and summary["window"] == number,
        "declared window required",
    )
    n, logical_count, unique_count, slots_count = COUNTS[number]
    require(
        window["summary"] == summary
        and all(
            type(summary[key]) is int and summary[key] == expected
            for key, expected in (
                ("sites", n),
                ("folds", n),
                ("logical_requests", logical_count),
                ("unique_requests", unique_count),
                ("prediction_slots", slots_count),
            )
        ),
        "exact admitted per-window populations required",
    )
    folds = window["folds"]
    by_fold = {row["fold_id"]: row for row in folds}
    require(
        len(folds) == len(by_fold) == n
        and len({row["test_record_ids"][0] for row in folds}) == n,
        "complete unique held-out site folds required",
    )
    requests = {row["request_sha256"]: row for row in window["requests"]}
    require(
        len(requests) == len(window["requests"]) == unique_count
        and all(row["status"] in {"completed", "refused"} for row in requests.values()),
        "complete successful/refused request population required",
    )
    statuses = Counter(row["status"] for row in requests.values())
    require(
        all(
            summary["batch_status_counts"].get(key, 0) == statuses[key]
            for key in ("completed", "refused")
        ),
        "original request dispositions differ",
    )
    logical = window["logical_requests"]
    require(
        len(logical) == logical_count
        and len({(row["fold_id"], row["local_record_id"]) for row in logical})
        == logical_count
        and {row["request_sha256"] for row in logical} == set(requests),
        "complete logical-to-numerical joins required",
    )
    for row in logical:
        fold = by_fold[row["fold_id"]]
        require(
            row["target_record_id"] == fold["test_record_ids"][0]
            and {row["local_record_id"], row["regional_anchor_record_id"]}
            <= set(fold["train_record_ids"])
            and not set(fold["test_record_ids"]) & set(fold["train_record_ids"]),
            "target entered training ancestry",
        )
    slots = window["slots"]
    require(
        len(slots) == slots_count
        and {(row["fold_id"], row["baseline"]) for row in slots}
        == {(fold, method) for fold in by_fold for method in METHODS},
        "complete predicted/refused baseline grid required",
    )
    predicted = {
        (row["fold_id"], row["baseline"]): row
        for row in slots
        if row["status"] == "predicted"
    }
    refused = [row for row in slots if row["status"] == "refused"]
    require(
        len(predicted) + len(refused) == slots_count
        and summary["predicted_slots"] == len(predicted)
        and summary["refused_slots"] == len(refused)
        and dict(Counter(row["reason_code"] for row in refused))
        == summary["refusal_reason_counts"],
        "dropped or promoted scientific refusal",
    )
    for row in slots:
        require(
            row["record_id"] == by_fold[row["fold_id"]]["test_record_ids"][0],
            "slot target differs",
        )
        if row["status"] == "predicted":
            composition(row["pollen_fraction"], taxa)
            composition(row["vegetation_fraction"], taxa)
            identity({"sha256": row["prediction_manifest_sha256"], "bytes": 0})
        else:
            require(
                isinstance(row.get("reason_code"), str)
                and bool(row["reason_code"])
                and isinstance(row.get("detail"), str),
                "scientific refusal cause required",
            )
            for key in row.get("training_refused_requests", []):
                require(
                    key in requests
                    and any(
                        item["fold_id"] == row["fold_id"]
                        and item["request_sha256"] == key
                        for item in logical
                    ),
                    "foreign training refusal",
                )
    scores = {(row["fold_id"], row["baseline"]): row for row in window["scores"]}
    require(
        len(scores) == len(window["scores"]) == summary["scored_rows"]
        and set(scores) == set(predicted),
        "score without complete frozen successful slot",
    )
    observations = window["observations"]
    require(
        set(observations) == {row["record_id"] for row in predicted.values()},
        "scoring outcome population differs",
    )
    for key, score in scores.items():
        row = predicted[key]
        require(score["record_id"] == row["record_id"], "score target differs")
        validate_score(
            row["pollen_fraction"], observations[row["record_id"]], score, taxa
        )
    require(
        summary["zero_probability_positive_count_rows"]
        == sum(row["zero_probability_positive_count"] for row in scores.values())
        and summary["point_pollen_only"] is True,
        "point-score eligibility summary differs",
    )
    require(
        window["freeze_before_post_freeze_scoring_decode"] is True
        and window["scientific_main_return"] == "not observed by unchanged consumer",
        "execution/freeze qualification differs",
    )


def validate_products(report: Json, index: Json, authority: Json) -> JsonObject:
    """Check saved products against pinned source and scientific contracts."""
    require(
        authority["schema_version"]
        == "author-love-temporal-development-public-authority.v1"
        and authority["approved"] is True
        and type(authority["actual_exit"]) is int
        and authority["actual_exit"] == 0
        and authority["scientific_saved_products_admitted"] is True,
        "actual independent public authority required",
    )
    require(
        report["schema_version"] == "author-love-temporal-development-publication.v1"
        and report["source_epoch"] == authority["candidate"] == SOURCE_EPOCH
        and report["input_epoch"] == authority["input_epoch"] == INPUT_EPOCH
        and report["protocol_sha256"] == PROTOCOL_SHA256
        and digest(report["profile"]) == PROFILE_SHA256,
        "original scientific source/input/profile identity differs",
    )
    require(
        all(
            report[key] is False
            for key in (
                "global_temporal_winner",
                "independent_confirmation",
                "vegetation_accuracy_admitted",
                "whole_owner_acceptance",
            )
        )
        and report["scientific_acceptance"] == "not_evaluated",
        "unsupported positive or whole-owner promotion",
    )
    require(
        digest(report["parameters"]) == report["profile"]["parameters_sha256"],
        "actual shared parameter values differ",
    )
    taxa = report["profile"]["taxa"]
    require(len(taxa) == len(set(taxa)) == 30, "exact thirty-taxon axis required")
    require(
        [row["window"] for row in report["windows"]] == [4, 6]
        and [row["window"] for row in authority["summaries"]] == [4, 6],
        "both original window dispositions required",
    )
    for row, summary in zip(report["windows"], authority["summaries"], strict=True):
        validate_window(row, summary, taxa)
    require(
        report["admitted_input_populations"] == authority["admitted_input_populations"]
        and report["source_files"] == SOURCES,
        "native availability/source identity changed",
    )
    for name, value in (("report.json", report), ("trace-index.json", index)):
        require(
            identity(authority["public_products"][name])
            == (hashlib.sha256(encoded(value)).hexdigest(), len(encoded(value))),
            "public product differs from admitted compact projection",
        )
    require(
        index["schema_version"] == "author-love-temporal-development-trace-index.v1"
        and bool(index["objects"]),
        "complete retained trace references required",
    )
    seen = set()
    roles = set()
    for row in index["objects"]:
        checksum, size = identity(row)
        require(
            (checksum, size) not in seen
            and row["retention_key"] == "sha256:" + checksum
            and isinstance(row["roles"], list)
            and row["roles"] == sorted(set(row["roles"]))
            and bool(row["roles"]),
            "duplicate, unretained or ambiguous trace object",
        )
        seen.add((checksum, size))
        roles.update(row["roles"])
    require(
        {
            f"TW{w}:{role}"
            for w in (4, 6)
            for role in (
                "plan",
                "native-terminal",
                "report.json",
                "prediction-freeze.json",
                "batch-result.json",
                "outcome-access.jsonl",
            )
        }
        <= roles,
        "missing original plan/result/freeze/journal trace roles",
    )
    require(
        sum(len(row["roles"]) for row in index["objects"]) == len(roles)
        and len({row["sha256"] for row in index["objects"]}) == len(index["objects"]),
        "conflicting trace identities or roles",
    )
    by_role = {role: row for row in index["objects"] for role in row["roles"]}
    for name in (
        "root_authority",
        "observation",
        "observer_execution",
        "observer_source_review",
    ):
        require(
            "provenance:" + name in by_role
            and identity(by_role["provenance:" + name])
            == identity(authority["proofs"][name]),
            "original admission provenance differs",
        )
    for window in report["windows"]:
        for request in window["requests"]:
            identity({"sha256": request["request_sha256"], "bytes": 0})
            if request["status"] == "completed":
                value = request["result_identity"]
                for key in ("manifest_sha256", "scientific_content_sha256"):
                    identity({"sha256": value[key], "bytes": 0})
                role = (
                    f"TW{window['window']}:request:{request['request_sha256']}:manifest"
                )
                require(
                    role in by_role
                    and by_role[role]["sha256"] == value["manifest_sha256"],
                    "saved cache manifest reference missing or changed",
                )
            else:
                require(
                    isinstance(request.get("error"), dict)
                    and request["error"].get("reason_code")
                    == "optimizer_nonconvergence",
                    "original optimizer refusal cause missing",
                )
    return {
        "windows": 2,
        "unique_requests": 48,
        "logical_requests": 311,
        "baseline_slots": 81,
        "predicted_slots": sum(
            row["summary"]["predicted_slots"] for row in report["windows"]
        ),
        "refused_slots": sum(
            row["summary"]["refused_slots"] for row in report["windows"]
        ),
        "scored_rows": sum(row["summary"]["scored_rows"] for row in report["windows"]),
        "private_trace_payloads_read": 0,
        "models_or_scoring_apis_called": 0,
    }


def validated_author_temporal_capture(
    repository: Path,
    tracked_by_path: dict[str, InventoryEntry],
    owners: list[JsonObject],
) -> tuple[tuple[InventoryEntry, ...], JsonObject]:
    """Authenticate retained temporal-development evidence and original source scope."""
    declared = [row for row in owners if row.get("owner_id") == OWNER]
    if not declared:
        return (), {}
    require(
        len(declared) == 1
        and declared[0].get("role") == "retained_source"
        and declared[0].get("paths") == sorted(PREFIX + name for name in PRODUCTS),
        "one exact sorted two-product owner required",
    )
    require(
        AUTHORITY_SHA256 is not None, "actual publication authority remains unbound"
    )
    path = _regular_confined_file(repository, AUTHORITY, "temporal authority")
    require(
        path.stat().st_nlink == 1 and path.stat().st_size <= 1024**2,
        "bounded unlinked public authority required",
    )
    raw = path.read_bytes()
    require(
        hashlib.sha256(raw).hexdigest() == AUTHORITY_SHA256,
        "actual publication authority changed",
    )
    authority = json.loads(raw)
    bodies = {}
    entries = []
    for name, expected in SOURCES.items():
        source = _regular_confined_file(repository, PREFIX + name, "temporal source")
        require(
            source.stat().st_nlink == 1
            and source.stat().st_size == expected["bytes"]
            and hashlib.sha256(source.read_bytes()).hexdigest() == expected["sha256"],
            "executed source/protocol changed",
        )
    for name in PRODUCTS:
        row = authority["public_products"][name]
        path = _regular_confined_file(repository, PREFIX + name, "temporal product")
        checksum, size = identity(row)
        require(
            path.stat().st_nlink == 1
            and path.stat().st_size == size
            and size <= 4 * 1024**2,
            "bounded unlinked compact product required",
        )
        body = path.read_bytes()
        require(
            hashlib.sha256(body).hexdigest() == checksum, "compact product hash changed"
        )
        entry = tracked_by_path.get(PREFIX + name)
        require(
            entry is not None and entry.sha256 == checksum and entry.size == size,
            "current product inventory changed",
        )
        assert entry is not None
        entries.append(entry)
        bodies[name] = json.loads(body)
    return tuple(entries), validate_products(
        bodies["report.json"], bodies["trace-index.json"], authority
    )
