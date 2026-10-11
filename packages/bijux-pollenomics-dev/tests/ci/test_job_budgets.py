"""Bound authored scientific jobs while preserving canonical source admission."""

from pathlib import Path

import yaml


def test_authored_verification_has_explicit_manual_runner_budgets() -> None:
    repository = Path(__file__).resolve().parents[4]
    expected = {
        "scientific-verification.yml": 10,
        "atlas-release-verification.yml": 10,
        "lra-reference.yml": 90,
    }
    for name, ceiling in expected.items():
        path = repository / ".github/workflows" / name
        workflow = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
        assert "workflow_dispatch" in workflow["on"]
        assert not {"push", "pull_request", "merge_group"}.intersection(workflow["on"])
        runner_jobs = [job for job in workflow["jobs"].values() if "runs-on" in job]
        assert runner_jobs, name
        for job in runner_jobs:
            budget = job.get("timeout-minutes")
            assert isinstance(budget, str) and budget.isdigit(), (name, budget)
            assert 0 < int(budget) <= ceiling, (name, budget)
