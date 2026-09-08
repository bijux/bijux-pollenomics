"""Keep generated workflow wrappers synchronized with their manifest authority."""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, cast

import yaml

REPOSITORY = Path(__file__).resolve().parents[4]
MANIFEST = REPOSITORY / ".github/standards/repo-config.manifest.json"
RENDERER = REPOSITORY / ".github/scripts/render_repo_configs.py"
WORKFLOWS = REPOSITORY / ".github/workflows"


def _renderer() -> ModuleType:
    spec = importlib.util.spec_from_file_location("bijux_workflow_renderer", RENDERER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_workflow(document: str) -> dict[str, Any]:
    loaded = yaml.load(document, Loader=yaml.BaseLoader)
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def test_manifest_renders_exact_bounded_workflow_wrappers() -> None:
    renderer = _renderer()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    repository = renderer.find_repo_config(manifest, "bijux-pollenomics")
    rendered_workflows: dict[str, dict[str, Any]] = {}

    for name in ("ci", "verify"):
        definition = copy.deepcopy(repository["workflow_wrappers"][name])
        definition = renderer.inject_dependabot_pull_request_skip(name, definition)
        definition = renderer.normalize_workflow_wrapper(name, definition)
        rendered = renderer.render_yaml_document(definition)
        assert rendered.encode() == (WORKFLOWS / f"{name}.yml").read_bytes()
        rendered_workflows[name] = _load_workflow(rendered)

    ci = rendered_workflows["ci"]
    verify = rendered_workflows["verify"]
    assert set(ci["on"]) == {"workflow_call"}
    assert set(verify["on"]) == {
        "push",
        "pull_request",
        "workflow_dispatch",
        "merge_group",
    }

    package_rows = verify["jobs"]["package"]["strategy"]["matrix"]["include"]
    pollenomics = next(
        row for row in package_rows if row["package_slug"] == "bijux-pollenomics"
    )
    assert json.loads(pollenomics["test_shards"]) == list(range(8))
    assert int(pollenomics["test_shard_count"]) == 8

    runner_jobs = {
        f"{workflow_name}:{job_name}": job
        for workflow_name, workflow in rendered_workflows.items()
        for job_name, job in workflow["jobs"].items()
        if "runs-on" in job
    }
    assert runner_jobs
    assert all(int(job["timeout-minutes"]) == 10 for job in runner_jobs.values())
