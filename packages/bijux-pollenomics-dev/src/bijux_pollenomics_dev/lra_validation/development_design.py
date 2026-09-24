"""Canonical prospective design for development-fold LRA model selection.

The design enumerates what may be tried before a child process can start.  It
does not admit a cohort, authenticate a reviewer, set final-test acceptance
thresholds, or authorize outcome access.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_IDENTITY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/@+-]{0,127}\Z")
_CONFIGURATION_FIELDS = {
    "method",
    "transport",
    "taxon_profile",
    "ppe_profile",
    "basin_scenario",
    "spatial_support",
    "temporal_support",
    "uncertainty",
}
_DESIGN_FIELDS = {
    "schema_version",
    "status",
    "cohort_admission_sha256",
    "scope_sha256",
    "split_manifest_sha256",
    "experiment_targets",
    "fold_ids",
    "candidates",
    "seeds",
    "metric_ids",
    "selection_rule",
    "resource_budget",
}
_EXPERIMENT_TARGETS = {
    ("local_pollen_available", "vegetation_cover"),
    ("all_target_pollen_withheld", "vegetation_cover"),
    ("all_target_pollen_withheld", "pollen_composition"),
}


class DevelopmentDesignError(ValueError):
    """A stable refusal for a malformed or out-of-design development trial."""

    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def canonical_json(value: object) -> str:
    """Serialize finite JSON with one stable byte representation."""
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise DevelopmentDesignError("non_json_or_nonfinite_design") from exc


def _identity(value: object, field: str) -> str:
    if not isinstance(value, str) or not _IDENTITY.fullmatch(value):
        raise DevelopmentDesignError(f"invalid_{field}")
    return value


def _sha256(value: object, field: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise DevelopmentDesignError(f"invalid_{field}")
    return value


def _positive_int(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise DevelopmentDesignError(f"invalid_{field}")
    return value


def _finite_mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(
        isinstance(key, str) and key for key in value
    ):
        raise DevelopmentDesignError(f"invalid_{field}")
    canonical_json(value)
    return value


@dataclass(frozen=True)
class FrozenDevelopmentDesign:
    """Validated canonical bytes and the exact prospective design payload."""

    canonical_design_json: str
    design_sha256: str
    payload: dict[str, Any]


def validate_development_design(
    canonical_design_json: object, design_sha256: object
) -> FrozenDevelopmentDesign:
    """Validate a frozen design without supplying any scientific defaults."""
    if not isinstance(canonical_design_json, str):
        raise DevelopmentDesignError("invalid_canonical_design")
    digest = _sha256(design_sha256, "design_sha256")
    try:
        payload = json.loads(canonical_design_json)
    except (TypeError, ValueError) as exc:
        raise DevelopmentDesignError("invalid_canonical_design") from exc
    if not isinstance(payload, dict) or set(payload) != _DESIGN_FIELDS:
        raise DevelopmentDesignError("invalid_design_fields")
    if canonical_json(payload) != canonical_design_json:
        raise DevelopmentDesignError("noncanonical_design")
    if hashlib.sha256(canonical_design_json.encode()).hexdigest() != digest:
        raise DevelopmentDesignError("design_digest_mismatch")
    if (
        payload["schema_version"] != "lra-development-design.v1"
        or payload["status"] != "frozen"
    ):
        raise DevelopmentDesignError("design_not_frozen")
    for field in (
        "cohort_admission_sha256",
        "scope_sha256",
        "split_manifest_sha256",
    ):
        _sha256(payload[field], field)

    raw_targets = payload["experiment_targets"]
    if not isinstance(raw_targets, list) or not raw_targets:
        raise DevelopmentDesignError("invalid_experiment_targets")
    targets: list[tuple[str, str]] = []
    for row in raw_targets:
        if not isinstance(row, dict) or set(row) != {"experiment", "target"}:
            raise DevelopmentDesignError("invalid_experiment_targets")
        pair = (row["experiment"], row["target"])
        if pair not in _EXPERIMENT_TARGETS:
            raise DevelopmentDesignError("invalid_experiment_targets")
        targets.append(pair)
    if len(set(targets)) != len(targets):
        raise DevelopmentDesignError("duplicate_experiment_target")

    fold_ids = payload["fold_ids"]
    if not isinstance(fold_ids, list) or not fold_ids:
        raise DevelopmentDesignError("invalid_fold_ids")
    checked_folds = [_identity(value, "fold_id") for value in fold_ids]
    if len(set(checked_folds)) != len(checked_folds):
        raise DevelopmentDesignError("duplicate_fold_id")

    seeds = payload["seeds"]
    if (
        not isinstance(seeds, list)
        or not seeds
        or any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0
            for value in seeds
        )
        or len(set(seeds)) != len(seeds)
    ):
        raise DevelopmentDesignError("invalid_seeds")

    candidates = payload["candidates"]
    if not isinstance(candidates, list) or not candidates:
        raise DevelopmentDesignError("invalid_candidates")
    candidate_ids: list[str] = []
    for row in candidates:
        if not isinstance(row, dict) or set(row) != {
            "candidate_id",
            "model",
            "configuration",
            "hyperparameters",
            "backend",
            "invocation",
        }:
            raise DevelopmentDesignError("invalid_candidate")
        candidate_ids.append(_identity(row["candidate_id"], "candidate_id"))
        _identity(row["model"], "model")
        _identity(row["backend"], "backend")
        configuration = _finite_mapping(row["configuration"], "configuration")
        if set(configuration) != _CONFIGURATION_FIELDS or not all(
            isinstance(value, str) and value.strip() for value in configuration.values()
        ):
            raise DevelopmentDesignError("invalid_configuration")
        _finite_mapping(row["hyperparameters"], "hyperparameters")
        invocation = row["invocation"]
        if not isinstance(invocation, dict) or set(invocation) != {
            "argv",
            "cwd",
            "environment",
            "executable_sha256",
        }:
            raise DevelopmentDesignError("invalid_candidate_invocation")
        argv = invocation["argv"]
        cwd = invocation["cwd"]
        if (
            not isinstance(argv, list)
            or not argv
            or not all(
                isinstance(value, str) and value and "\0" not in value for value in argv
            )
            or not Path(argv[0]).is_absolute()
            or not isinstance(cwd, str)
            or not Path(cwd).is_absolute()
        ):
            raise DevelopmentDesignError("invalid_candidate_invocation")
        environment = invocation["environment"]
        if not isinstance(environment, dict) or not all(
            isinstance(key, str)
            and key
            and "\0" not in key
            and isinstance(value, str)
            and "\0" not in value
            for key, value in environment.items()
        ):
            raise DevelopmentDesignError("invalid_candidate_invocation")
        _sha256(invocation["executable_sha256"], "candidate_executable_sha256")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise DevelopmentDesignError("duplicate_candidate_id")

    metrics = payload["metric_ids"]
    if not isinstance(metrics, dict) or set(metrics) != {
        target for _, target in targets
    }:
        raise DevelopmentDesignError("invalid_metric_ids")
    for values in metrics.values():
        if not isinstance(values, list) or not values:
            raise DevelopmentDesignError("invalid_metric_ids")
        checked = [_identity(value, "metric_id") for value in values]
        if len(set(checked)) != len(checked):
            raise DevelopmentDesignError("duplicate_metric_id")

    selection = payload["selection_rule"]
    if not isinstance(selection, dict) or set(selection) != {
        "primary_metric_by_target",
        "direction_by_metric",
        "tie_breakers",
        "minimum_completed_folds",
    }:
        raise DevelopmentDesignError("invalid_selection_rule")
    primary = selection["primary_metric_by_target"]
    directions = selection["direction_by_metric"]
    tie_breakers = selection["tie_breakers"]
    if (
        not isinstance(primary, dict)
        or set(primary) != set(metrics)
        or any(primary[target] not in metrics[target] for target in metrics)
        or not isinstance(directions, dict)
        or set(directions) != {item for values in metrics.values() for item in values}
        or any(
            not isinstance(value, str) or value not in {"minimize", "maximize"}
            for value in directions.values()
        )
        or not isinstance(tie_breakers, list)
        or not tie_breakers
    ):
        raise DevelopmentDesignError("invalid_selection_rule")
    checked_ties = [_identity(value, "tie_breaker") for value in tie_breakers]
    if len(set(checked_ties)) != len(checked_ties):
        raise DevelopmentDesignError("duplicate_tie_breaker")
    if _positive_int(
        selection["minimum_completed_folds"], "minimum_completed_folds"
    ) > len(checked_folds):
        raise DevelopmentDesignError("minimum_completed_folds_exceeds_design")

    budget = payload["resource_budget"]
    if not isinstance(budget, dict) or set(budget) != {
        "maximum_trials",
        "maximum_seconds_per_trial",
        "maximum_declared_threads_per_trial",
        "maximum_total_declared_cpu_seconds",
    }:
        raise DevelopmentDesignError("invalid_resource_budget")
    maximum_trials = _positive_int(budget["maximum_trials"], "maximum_trials")
    seconds = _positive_int(
        budget["maximum_seconds_per_trial"], "maximum_seconds_per_trial"
    )
    threads = _positive_int(
        budget["maximum_declared_threads_per_trial"],
        "maximum_declared_threads_per_trial",
    )
    total = budget["maximum_total_declared_cpu_seconds"]
    if (
        isinstance(total, bool)
        or not isinstance(total, (int, float))
        or not math.isfinite(total)
        or total < seconds * threads
        or maximum_trials < 1
    ):
        raise DevelopmentDesignError("invalid_maximum_total_declared_cpu_seconds")
    return FrozenDevelopmentDesign(canonical_design_json, digest, payload)


def validate_attempt_against_design(
    design: FrozenDevelopmentDesign,
    attempt: dict[str, object],
    *,
    verify_executable_bytes: bool = True,
    executable_descriptor: int | None = None,
) -> tuple[str, ...]:
    """Refuse any trial choice not enumerated by the frozen design."""
    payload = design.payload
    binding = attempt["evaluation_binding"]
    if not isinstance(binding, dict):
        raise DevelopmentDesignError("invalid_evaluation_binding")
    for design_field, binding_field in (
        ("cohort_admission_sha256", "cohort_admission_sha256"),
        ("scope_sha256", "scope_sha256"),
        ("split_manifest_sha256", "split_manifest_sha256"),
    ):
        if payload[design_field] != binding.get(binding_field):
            raise DevelopmentDesignError("design_evaluation_binding_mismatch")
    pair = (binding.get("experiment"), binding.get("target"))
    if pair not in {
        (row["experiment"], row["target"]) for row in payload["experiment_targets"]
    }:
        raise DevelopmentDesignError("trial_experiment_target_not_declared")
    if attempt["fold_id"] not in payload["fold_ids"]:
        raise DevelopmentDesignError("trial_fold_not_declared")
    if attempt["seed"] not in payload["seeds"]:
        raise DevelopmentDesignError("trial_seed_not_declared")
    candidates = {row["candidate_id"]: row for row in payload["candidates"]}
    candidate = candidates.get(attempt["candidate_id"])
    if candidate is None:
        raise DevelopmentDesignError("trial_candidate_not_declared")
    for field in ("model", "configuration", "hyperparameters", "backend"):
        if attempt[field] != candidate[field]:
            raise DevelopmentDesignError("trial_candidate_content_mismatch")
    invocation = attempt.get("invocation")
    if invocation is not None:
        if not isinstance(invocation, dict):
            raise DevelopmentDesignError("invalid_trial_invocation")
        declared = candidate["invocation"]
        if (
            invocation.get("argv") != declared["argv"]
            or invocation.get("cwd") != declared["cwd"]
            or invocation.get("environment") != declared["environment"]
        ):
            raise DevelopmentDesignError("trial_invocation_not_declared")
        if verify_executable_bytes:
            executable = Path(declared["argv"][0])
            digest = hashlib.sha256()
            try:
                if executable_descriptor is None:
                    with executable.open("rb") as stream:
                        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                            raise DevelopmentDesignError(
                                "declared_executable_not_regular_file"
                            )
                        for block in iter(lambda: stream.read(1024 * 1024), b""):
                            digest.update(block)
                else:
                    descriptor_stat = os.fstat(executable_descriptor)
                    path_stat = executable.stat()
                    if not stat.S_ISREG(descriptor_stat.st_mode) or (
                        descriptor_stat.st_dev,
                        descriptor_stat.st_ino,
                    ) != (path_stat.st_dev, path_stat.st_ino):
                        raise DevelopmentDesignError(
                            "declared_executable_not_regular_file"
                        )
                    os.lseek(executable_descriptor, 0, os.SEEK_SET)
                    while block := os.read(executable_descriptor, 1024 * 1024):
                        digest.update(block)
                    os.lseek(executable_descriptor, 0, os.SEEK_SET)
            except OSError as exc:
                raise DevelopmentDesignError("declared_executable_unreadable") from exc
            if digest.hexdigest() != declared["executable_sha256"]:
                raise DevelopmentDesignError("declared_executable_digest_mismatch")
    budget = attempt["budget"]
    if not isinstance(budget, dict) or set(budget) != {"seconds", "threads"}:
        raise DevelopmentDesignError("invalid_trial_budget")
    seconds = budget["seconds"]
    threads = budget["threads"]
    if (
        isinstance(seconds, bool)
        or not isinstance(seconds, (int, float))
        or not math.isfinite(seconds)
        or seconds <= 0
        or isinstance(threads, bool)
        or not isinstance(threads, int)
        or threads < 1
        or seconds > payload["resource_budget"]["maximum_seconds_per_trial"]
        or threads > payload["resource_budget"]["maximum_declared_threads_per_trial"]
    ):
        raise DevelopmentDesignError("trial_budget_exceeds_design")
    target = binding["target"]
    return tuple(payload["metric_ids"][target])
