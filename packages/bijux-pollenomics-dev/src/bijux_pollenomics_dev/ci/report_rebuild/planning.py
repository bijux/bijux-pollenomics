"""Repository-bound planning for partitioned report rebuilds."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from bijux_pollenomics_dev.ci.rebuild_reports import (
    InventoryEntry,
    inventory_inputs,
    load_policy,
    repository_identity,
)

from .contracts import (
    JsonObject,
    RebuildBinding,
    ReportRebuildError,
    atomic_write_json,
    canonical_json_sha256,
    load_json,
    parse_binding,
    require_exact_binding,
    require_mapping,
    require_string,
    require_string_sequence,
    sha256_bytes,
)
from .runtime_process import run_runtime_command

PLAN_SCHEMA = "partitioned-report-rebuild-plan.v1"
_CANONICAL_GENERATOR_ARGUMENTS = (
    "publish-reports",
    "--aadr-root",
    "{repo_root}/data/aadr",
    "--version",
    "v66",
    "--output-root",
    "{output_root}",
    "--published-output-root",
    "docs/report",
    "--context-root",
    "{repo_root}/data",
)


def _require_canonical_generator(policy: JsonObject) -> None:
    """Refuse a partition plan that diverges from the supported full build."""
    generator = require_mapping(policy.get("generator"), "generator policy")
    if (
        generator.get("module") != "bijux_pollenomics"
        or tuple(
            require_string_sequence(generator.get("arguments"), "generator arguments")
        )
        != _CANONICAL_GENERATOR_ARGUMENTS
    ):
        raise ReportRebuildError(
            "partitioned rebuild requires the canonical report generator contract"
        )


def _partition_group_size(policy: JsonObject) -> int:
    raw = require_mapping(policy.get("partitioning"), "partitioning policy")
    if set(raw) != {"country_group_size", "schema_version"}:
        raise ReportRebuildError("partitioning policy fields are not exact")
    if raw["schema_version"] != "published-report-partition-policy.v1":
        raise ReportRebuildError("unsupported partitioning policy schema")
    group_size = raw["country_group_size"]
    if type(group_size) is not int or int(group_size) < 1:
        raise ReportRebuildError("country_group_size must be a positive integer")
    return int(group_size)


def current_binding(
    repo_root: Path, policy_path: Path, policy: JsonObject
) -> tuple[RebuildBinding, tuple[InventoryEntry, ...]]:
    """Build the exact policy, repository, and input-tree identity."""
    inputs = inventory_inputs(repo_root, policy)
    input_payload = [entry.as_json() for entry in inputs]
    return (
        RebuildBinding(
            policy_sha256=sha256_bytes(policy_path.read_bytes()),
            repository=repository_identity(
                repo_root, required=cast(bool, policy["require_clean_repository"])
            ),
            inputs_sha256=canonical_json_sha256(input_payload),
        ),
        inputs,
    )


def _canonical_plan(binding: RebuildBinding, group_size: int) -> JsonObject:
    """Derive the only plan accepted for the current runtime and policy."""
    runtime_plan = run_runtime_command(
        {
            "schema_version": "published-report-partition-command.v1",
            "operation": "plan",
            "country_group_size": group_size,
        }
    )
    expected = {
        "countries",
        "dependent_partition_ids",
        "partition_ids",
        "scope_partition_ids",
        "slug",
        "title",
        "version",
    }
    if set(runtime_plan) != expected:
        raise ReportRebuildError("runtime plan fields are not exact")
    countries = require_string_sequence(runtime_plan["countries"], "runtime countries")
    partition_ids = require_string_sequence(
        runtime_plan["partition_ids"], "runtime partition_ids"
    )
    dependent_ids = require_string_sequence(
        runtime_plan["dependent_partition_ids"], "runtime dependent_partition_ids"
    )
    scope_ids = require_string_sequence(
        runtime_plan["scope_partition_ids"], "runtime scope_partition_ids"
    )
    if dependent_ids != ("foundation",):
        raise ReportRebuildError("runtime plan must contain one foundation partition")
    if (*scope_ids, *dependent_ids) != partition_ids:
        raise ReportRebuildError("runtime partition identities are invalid")
    return {
        "schema_version": PLAN_SCHEMA,
        "binding": binding.as_json(),
        "parameters": {
            "countries": list(countries),
            "country_group_size": group_size,
            "published_output_root": "docs/report",
            "slug": require_string(runtime_plan["slug"], "runtime slug"),
            "title": require_string(runtime_plan["title"], "runtime title"),
            "version": require_string(runtime_plan["version"], "runtime version"),
        },
        "partition_ids": list(partition_ids),
        "scope_partition_ids": list(scope_ids),
        "dependent_partition_ids": list(dependent_ids),
        "assembly_id": "assemble",
    }


def build_partition_plan(
    *, repo_root: Path, policy_path: Path, output_path: Path
) -> JsonObject:
    """Bind the runtime partition plan to exact repository inputs."""
    repo_root = repo_root.resolve()
    if output_path.exists() or output_path.is_symlink():
        raise ReportRebuildError(f"partition plan already exists: {output_path}")
    policy = load_policy(policy_path)
    _require_canonical_generator(policy)
    group_size = _partition_group_size(policy)
    binding, _ = current_binding(repo_root, policy_path, policy)
    report = _canonical_plan(binding, group_size)
    atomic_write_json(output_path, report)
    return report


def parse_plan(path: Path) -> JsonObject:
    """Load and validate an exact partition rebuild plan."""
    plan = load_json(path, "partition rebuild plan")
    expected = {
        "assembly_id",
        "binding",
        "dependent_partition_ids",
        "parameters",
        "partition_ids",
        "schema_version",
        "scope_partition_ids",
    }
    if set(plan) != expected or plan.get("schema_version") != PLAN_SCHEMA:
        raise ReportRebuildError("partition rebuild plan fields or schema are invalid")
    parse_binding(plan["binding"], "plan binding")
    partition_ids = require_string_sequence(plan["partition_ids"], "partition_ids")
    scope_ids = require_string_sequence(
        plan["scope_partition_ids"], "scope_partition_ids"
    )
    dependent_ids = require_string_sequence(
        plan["dependent_partition_ids"], "dependent_partition_ids"
    )
    if (*scope_ids, *dependent_ids) != partition_ids:
        raise ReportRebuildError("partition plan ordering or coverage is invalid")
    if require_string(plan["assembly_id"], "assembly_id") in partition_ids:
        raise ReportRebuildError("assembly identity overlaps executable partitions")
    parameters = require_mapping(plan["parameters"], "plan parameters")
    required_parameters = {
        "countries",
        "country_group_size",
        "published_output_root",
        "slug",
        "title",
        "version",
    }
    if set(parameters) != required_parameters:
        raise ReportRebuildError("plan parameter fields are not exact")
    require_string_sequence(parameters["countries"], "plan countries")
    for field in ("published_output_root", "slug", "title", "version"):
        require_string(parameters[field], f"plan {field}")
    if type(parameters["country_group_size"]) is not int:
        raise ReportRebuildError("plan country_group_size must be an integer")
    return plan


def require_current_binding(
    *, repo_root: Path, policy_path: Path, plan: JsonObject
) -> tuple[JsonObject, RebuildBinding, tuple[InventoryEntry, ...]]:
    """Load policy and reject a plan not bound to the current repository state."""
    policy = load_policy(policy_path)
    _require_canonical_generator(policy)
    group_size = _partition_group_size(policy)
    current, inputs = current_binding(repo_root, policy_path, policy)
    require_exact_binding(
        current, parse_binding(plan["binding"], "plan binding"), "current"
    )
    if plan != _canonical_plan(current, group_size):
        raise ReportRebuildError(
            "partition rebuild plan does not match the canonical bound plan"
        )
    return policy, current, inputs
