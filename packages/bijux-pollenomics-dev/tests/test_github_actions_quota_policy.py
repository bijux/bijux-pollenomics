"""GitHub Actions runner-allocation policy contracts."""

from __future__ import annotations

from itertools import product
import json
from pathlib import Path
import re

import yaml

from bijux_pollenomics.config import DEFAULT_PUBLISHED_COUNTRIES
from bijux_pollenomics.reporting.bundles.report_partitions import (
    build_report_partition_plan,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPENDABOT_SKIP = "github.event.pull_request.user.login != 'dependabot[bot]'"
DEPENDABOT_GOVERNANCE_WORKFLOWS = {
    "automerge-pr.yml",
    "github-policy.yml",
    "pr-approval-policy.yml",
}
MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([a-zA-Z0-9_-]+)\s*\}\}")
PULL_REQUEST_EVENTS = {
    "pull_request",
    "pull_request_review",
    "pull_request_target",
}
RULESET_PATH = REPO_ROOT / ".github" / "rulesets" / "main-branch-protection.json"
STATUS_DOCUMENTATION_PATH = REPO_ROOT / ".github" / "required-status-checks.md"


def declared_matrix_values(value: object) -> object:
    """Resolve the report planner's declared dynamic scope dimension exactly."""
    if value != "${{ fromJSON(needs.rebuild-plan.outputs.scope_partitions) }}":
        return value
    policy = json.loads(
        (REPO_ROOT / "configs/ci/reproducible-report-build.json").read_text()
    )
    plan = build_report_partition_plan(
        DEFAULT_PUBLISHED_COUNTRIES,
        country_group_size=policy["partitioning"]["country_group_size"],
    )
    return [part.identity for part in plan.partitions if part.kind != "foundation"]


def workflow_documents() -> list[tuple[Path, dict[str, object]]]:
    workflows = []
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        assert isinstance(document, dict), f"{path.name} must contain a YAML mapping"
        workflows.append((path, document))
    return workflows


def matrix_replacements(
    *,
    matrix: dict[str, object],
    matrix_keys: list[str],
    workflow_name: str,
    job_name: str,
) -> list[dict[str, str]]:
    replacements: list[dict[str, str]] = []
    dimensions: list[list[str]] = []
    for key in matrix_keys:
        values = declared_matrix_values(matrix.get(key))
        if not isinstance(values, list):
            dimensions = []
            break
        assert all(isinstance(value, str) for value in values)
        dimensions.append(values)

    if len(dimensions) == len(matrix_keys):
        for combination in product(*dimensions):
            replacements.append(dict(zip(matrix_keys, combination, strict=True)))

    included = matrix.get("include", [])
    assert isinstance(included, list)
    for entry in included:
        assert isinstance(entry, dict)
        if not all(key in entry for key in matrix_keys):
            continue
        assert all(isinstance(entry[key], str) for key in matrix_keys)
        replacements.append({key: entry[key] for key in matrix_keys})

    assert replacements, (
        f"{workflow_name} job {job_name} matrix must resolve {', '.join(matrix_keys)}"
    )
    return replacements


def test_dynamic_report_matrix_preserves_every_concrete_check_name() -> None:
    replacements = matrix_replacements(
        matrix={
            "lane": ["reference", "replay"],
            "partition": "${{ fromJSON(needs.rebuild-plan.outputs.scope_partitions) }}",
        },
        matrix_keys=["lane", "partition"],
        workflow_name="scientific-verification.yml",
        job_name="rebuild-scopes",
    )
    scopes = declared_matrix_values(
        "${{ fromJSON(needs.rebuild-plan.outputs.scope_partitions) }}"
    )
    assert isinstance(scopes, list) and scopes
    assert {(row["lane"], row["partition"]) for row in replacements} == {
        (lane, scope) for lane in ("reference", "replay") for scope in scopes
    }


def render_check_name(
    check_name: str,
    replacements: dict[str, str],
) -> str:
    return MATRIX_REFERENCE.sub(
        lambda match: replacements[match.group(1)],
        check_name,
    )


def pull_request_check_names() -> set[str]:
    names = set()
    for path, document in workflow_documents():
        events = document.get("on")
        assert isinstance(events, dict), f"{path.name} must define workflow events"
        if not PULL_REQUEST_EVENTS.intersection(events):
            continue

        jobs = document.get("jobs")
        assert isinstance(jobs, dict), f"{path.name} must define workflow jobs"
        for job_name, job in jobs.items():
            assert isinstance(job, dict), (
                f"{path.name} job {job_name} must be a mapping"
            )
            check_name = job.get("name", job_name)
            assert isinstance(check_name, str)
            matrix_keys = sorted(set(MATRIX_REFERENCE.findall(check_name)))
            if not matrix_keys:
                names.add(check_name)
                continue

            strategy = job.get("strategy")
            assert isinstance(strategy, dict), (
                f"{path.name} job {job_name} must define a matrix strategy"
            )
            matrix = strategy.get("matrix")
            assert isinstance(matrix, dict)
            for replacements in matrix_replacements(
                matrix=matrix,
                matrix_keys=matrix_keys,
                workflow_name=path.name,
                job_name=job_name,
            ):
                names.add(render_check_name(check_name, replacements))
    return names


def required_status_check_names() -> set[str]:
    ruleset = json.loads(RULESET_PATH.read_text(encoding="utf-8"))
    required_status_rules = [
        rule for rule in ruleset["rules"] if rule["type"] == "required_status_checks"
    ]
    assert len(required_status_rules) == 1
    return {
        check["context"]
        for check in required_status_rules[0]["parameters"]["required_status_checks"]
    }


def test_dependabot_pull_requests_do_not_allocate_workflow_runners() -> None:
    for path, document in workflow_documents():
        if path.name in DEPENDABOT_GOVERNANCE_WORKFLOWS:
            continue
        events = document.get("on")
        assert isinstance(events, dict), f"{path.name} must define workflow events"
        if not PULL_REQUEST_EVENTS.intersection(events):
            continue

        jobs = document.get("jobs")
        assert isinstance(jobs, dict), f"{path.name} must define workflow jobs"
        for job_name, job in jobs.items():
            assert isinstance(job, dict), (
                f"{path.name} job {job_name} must be a mapping"
            )
            condition = job.get("if", "")
            assert isinstance(condition, str)
            assert DEPENDABOT_SKIP in condition, (
                f"{path.name} job {job_name} must skip Dependabot PRs "
                "before allocating a runner"
            )


def test_required_status_checks_are_emitted_by_pull_request_workflows() -> None:
    required = required_status_check_names()
    missing = required - pull_request_check_names()

    assert not missing, (
        "required status checks must be emitted by pull-request workflows: "
        f"{sorted(missing)}"
    )


def test_required_status_check_documentation_matches_ruleset() -> None:
    documented = set(
        re.findall(
            r"^- `([^`]+)` \(from workflow ",
            STATUS_DOCUMENTATION_PATH.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )

    assert documented == required_status_check_names()
