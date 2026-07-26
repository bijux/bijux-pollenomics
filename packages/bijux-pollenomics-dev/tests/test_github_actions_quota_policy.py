"""GitHub Actions runner-allocation policy contracts."""

from __future__ import annotations

import json
import re
from itertools import product
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPENDABOT_SKIP = "github.event.pull_request.user.login != 'dependabot[bot]'"
MATRIX_REFERENCE = re.compile(r"\$\{\{\s*matrix\.([a-zA-Z0-9_-]+)\s*\}\}")
PULL_REQUEST_EVENTS = {
    "pull_request",
    "pull_request_review",
    "pull_request_target",
}
RULESET_PATH = REPO_ROOT / ".github" / "rulesets" / "main-branch-protection.json"
STATUS_DOCUMENTATION_PATH = REPO_ROOT / ".github" / "required-status-checks.md"


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
    replacements = []
    dimensions = []
    for key in matrix_keys:
        values = matrix.get(key)
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
                names.add(
                    MATRIX_REFERENCE.sub(
                        lambda match: replacements[match.group(1)],
                        check_name,
                    )
                )
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
