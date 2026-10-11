"""Keep canonical source admission complete and fail closed for every package."""

from __future__ import annotations

import importlib.util
from itertools import product
import json
import os
from pathlib import Path
import subprocess
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


def test_manifest_renders_exact_source_admission_wrappers() -> None:
    renderer = _renderer()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    prepared = renderer.prepare_repo_files("bijux-pollenomics", manifest)
    workflows: dict[str, dict[str, Any]] = {}
    for name in ("ci", "verify"):
        relative = f".github/workflows/{name}.yml"
        content = prepared[relative]
        assert isinstance(content, bytes)
        assert content == (REPOSITORY / relative).read_bytes()
        workflows[name] = _load_workflow(content.decode())

    ci, verify = workflows["ci"], workflows["verify"]
    assert set(ci["on"]) == {"workflow_call"}
    assert set(ci["jobs"]) == {"checks"}
    inputs = ci["on"]["workflow_call"]["inputs"]
    assert json.loads(inputs["check_targets"]["default"]) == ["lint", "security"]
    assert json.loads(inputs["api_toolchain_targets"]["default"]) == []
    assert "test_python_versions" not in inputs and "post_test_targets" not in inputs
    assert ci["jobs"]["checks"]["strategy"]["matrix"] == {
        "target": "${{ fromJson(inputs.check_targets) }}"
    }
    assert set(verify["on"]) == {
        "push",
        "pull_request",
        "workflow_dispatch",
        "merge_group",
    }
    assert set(verify["jobs"]) == {"repository", "package", "verification_ready"}
    package = verify["jobs"]["package"]
    assert package["needs"] == "repository"
    assert package["uses"] == "./.github/workflows/ci.yml"
    rows = package["strategy"]["matrix"]["include"]
    assert {row["package_slug"] for row in rows} == {
        "bijux-pollenomics",
        "pollenomics",
        "bijux-pollenomics-dev",
        "bijux-pollenomics-lra",
    }
    assert len(rows) == 4
    for row in rows:
        assert json.loads(row["check_targets"]) == ["lint", "security"]
        assert json.loads(row["api_toolchain_targets"]) == []
        assert (REPOSITORY / row["package_dir"] / "pyproject.toml").is_file()
        assert "test_shards" not in row
    ready = verify["jobs"]["verification_ready"]
    assert ready["if"] == "${{ always() }}"
    assert ready["needs"] == ["repository", "package"]
    assert all(
        "dependabot[bot]" not in job.get("if", "") for job in verify["jobs"].values()
    )


def test_source_aggregate_rejects_every_incomplete_dependency_result() -> None:
    workflow = _load_workflow((WORKFLOWS / "verify.yml").read_text())
    steps = workflow["jobs"]["verification_ready"]["steps"]
    assert len(steps) == 1
    step = steps[0]
    assert step["env"] == {
        "REPOSITORY_RESULT": "${{ needs.repository.result }}",
        "PACKAGE_RESULT": "${{ needs.package.result }}",
    }
    for repository, package in product(
        ("success", "failure", "cancelled", "skipped", ""), repeat=2
    ):
        environment = dict(
            os.environ, REPOSITORY_RESULT=repository, PACKAGE_RESULT=package
        )
        result = subprocess.run(
            ["bash", "-c", step["run"]],
            env=environment,
            check=False,
            capture_output=True,
            text=True,
        )
        assert (result.returncode == 0) == (
            repository == "success" and package == "success"
        ), (repository, package, result.stderr)
