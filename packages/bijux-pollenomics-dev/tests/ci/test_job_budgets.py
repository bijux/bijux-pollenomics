"""Keep every executable workflow job within the release latency ceiling."""

from pathlib import Path

import yaml


def test_every_runner_job_has_a_ten_minute_or_shorter_budget() -> None:
    repository = Path(__file__).resolve().parents[4]
    failures = []
    runner_jobs = 0
    for path in sorted((repository / ".github" / "workflows").glob("*.yml")):
        workflow = yaml.safe_load(path.read_text(encoding="utf-8"))
        for name, job in workflow["jobs"].items():
            if "runs-on" not in job:
                continue
            runner_jobs += 1
            budget = job.get("timeout-minutes")
            if type(budget) is not int or not 0 < budget <= 10:
                failures.append(f"{path.name}:{name}: {budget!r}")
    assert runner_jobs > 0, "workflow discovery must not silently become empty"
    assert not failures, "jobs exceed the ten-minute ceiling: " + "; ".join(failures)
