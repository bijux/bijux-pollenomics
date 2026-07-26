"""GitHub Actions runner-allocation policy contracts."""

from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
DEPENDABOT_SKIP = "github.event.pull_request.user.login != 'dependabot[bot]'"
PULL_REQUEST_EVENTS = {
    "pull_request",
    "pull_request_review",
    "pull_request_target",
}


def workflow_documents() -> list[tuple[Path, dict[str, object]]]:
    workflows = []
    for path in sorted((REPO_ROOT / ".github" / "workflows").glob("*.yml")):
        document = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        assert isinstance(document, dict), f"{path.name} must contain a YAML mapping"
        workflows.append((path, document))
    return workflows


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
