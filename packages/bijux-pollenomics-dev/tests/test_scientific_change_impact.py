"""Contracts for selection-aware scientific verification."""

from __future__ import annotations

import json
from pathlib import Path
import re

import pytest
import yaml

from bijux_pollenomics_dev.ci.path_selection import (
    REQUIRED_SURFACE_IDS,
    ChangeImpactContract,
    load_contract,
    select_changed_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / "configs" / "ci" / "scientific-change-impact.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "scientific-verification.yml"
DEPENDABOT_SKIP = "github.event.pull_request.user.login != 'dependabot[bot]'"
PINNED_ACTION = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+@[0-9a-f]{40}$")
DATA_GATES = {
    "science",
    "data",
    "rebuild",
    "provenance",
    "doc-counts",
    "map",
}


def _contract() -> ChangeImpactContract:
    return load_contract(CONTRACT_PATH)


@pytest.mark.parametrize(
    ("surface_id", "changed_path"),
    [
        ("raw-data-and-receipts", "data/sead/raw/receipts/sites.json"),
        (
            "normalized-derived-and-review-data",
            "data/neotoma/normalized/sites.json",
        ),
        ("governed-data", "data/collection_summary.json"),
        (
            "source-adapters-and-normalizers",
            "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/neotoma/collection.py",
        ),
        (
            "temporal-and-spatial-core",
            "packages/bijux-pollenomics/src/bijux_pollenomics/core/temporal_semantics.py",
        ),
        (
            "taxon-group-role-classification",
            "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma.py",
        ),
        (
            "scientific-scenarios-and-configuration",
            "configs/science/propagation-scenario.json",
        ),
        ("country-boundaries-and-scope", "data/boundaries/raw/sweden.geojson"),
        (
            "map-payload-template-and-provider",
            "packages/bijux-pollenomics/src/bijux_pollenomics/reporting/map_document/template.py",
        ),
        (
            "evidence-contracts-and-manifests",
            "configs/release_evidence_policy.json",
        ),
        ("documentation-counts-and-claims", "docs/public/pollenomics/index.md"),
        (
            "ci-change-impact-contract",
            ".github/workflows/scientific-verification.yml",
        ),
    ],
)
def test_every_governed_surface_selects_its_declared_gates(
    surface_id: str, changed_path: str
) -> None:
    contract = _contract()
    result = select_changed_paths(contract, [changed_path])
    surface = next(item for item in contract.surfaces if item.surface_id == surface_id)

    assert surface_id in result.matched_surfaces
    assert set(surface.gates) <= set(result.selected_gates)


def test_contract_contains_every_required_repository_surface() -> None:
    contract = _contract()

    assert {surface.surface_id for surface in contract.surfaces} >= REQUIRED_SURFACE_IDS


@pytest.mark.parametrize(
    "changed_path",
    [
        "data/collection_summary.json",
        "data/sead/raw/receipts/sites.json",
        "data/neotoma/normalized/sites.json",
    ],
)
def test_data_only_change_selects_every_mandatory_gate(changed_path: str) -> None:
    result = select_changed_paths(_contract(), [changed_path])

    assert set(result.selected_gates) >= DATA_GATES
    assert result.unavailable_gates == ()
    assert not result.fail_closed


@pytest.mark.parametrize(
    "changed_paths",
    [
        [],
        ["unclassified/product-surface.txt"],
        ["/absolute/path.json"],
        ["../outside.json"],
        ["data/../outside.json"],
        ["data\\sead\\raw\\sites.json"],
        [" data/sead/raw/sites.json"],
    ],
)
def test_unknown_or_malformed_paths_fail_closed_to_all_declared_gates(
    changed_paths: list[str],
) -> None:
    contract = _contract()
    result = select_changed_paths(contract, changed_paths)

    assert result.fail_closed
    assert result.available_gates == contract.available_gate_ids
    assert result.unavailable_gates == ("browser", "deployed-smoke")


def test_manual_full_selection_includes_unavailable_release_requirements() -> None:
    result = select_changed_paths(_contract(), [], select_all=True)

    assert set(result.unavailable_gates) == {"browser", "deployed-smoke"}
    assert not result.fail_closed


def test_result_is_deterministic_and_binds_contract_digest() -> None:
    first = select_changed_paths(
        _contract(), ["data/sead/raw/sites.json", "docs/public/pollenomics/index.md"]
    )
    second = select_changed_paths(
        _contract(), ["docs/public/pollenomics/index.md", "data/sead/raw/sites.json"]
    )

    assert first.as_dict() == second.as_dict()
    assert re.fullmatch(r"[0-9a-f]{64}", first.contract_digest)


def test_workflow_has_no_path_filter_and_uses_selector_as_authority() -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    events = workflow["on"]

    assert "paths" not in events["push"]
    assert "paths-ignore" not in events["push"]
    assert "paths" not in events["pull_request"]
    assert "paths-ignore" not in events["pull_request"]
    select_step = next(
        step
        for step in workflow["jobs"]["impact"]["steps"]
        if step.get("id") == "select"
    )
    assert "bijux_pollenomics_dev.ci.path_selection" in select_step["run"]
    assert "scientific-change-impact.json" in select_step["run"]
    assert set(workflow["jobs"]["gates"]["strategy"]["matrix"]["gate"]) == {
        "path-selection",
        "science",
        "data",
        "rebuild",
        "provenance",
        "doc-counts",
        "map",
    }
    assert "max-parallel" not in workflow["jobs"]["gates"]["strategy"]
    run_step = next(
        step
        for step in workflow["jobs"]["gates"]["steps"]
        if step.get("name") == "Run selected gate"
    )
    assert "needs.impact.outputs.available_gates" in run_step["if"]


def test_workflow_preserves_both_rename_endpoints_and_push_endpoint_diffs() -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    resolve_step = next(
        step
        for step in workflow["jobs"]["impact"]["steps"]
        if step.get("id") == "changes"
    )
    script = resolve_step["run"]

    assert script.count("--no-renames") == 4
    assert '"${PUSH_BEFORE_SHA}" "${CANDIDATE_SHA}"' in script
    assert '"${PUSH_BEFORE_SHA}...${CANDIDATE_SHA}"' not in script


def test_workflow_pr_jobs_skip_dependabot_before_runner_allocation() -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )

    for job in workflow["jobs"].values():
        assert DEPENDABOT_SKIP in job.get("if", "")


def test_workflow_actions_are_immutable_and_final_signal_depends_on_all_postures() -> (
    None
):
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    action_references = [
        step["uses"]
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if "uses" in step and not step["uses"].startswith("./")
    ]

    assert action_references
    assert all(PINNED_ACTION.fullmatch(reference) for reference in action_references)
    assert set(workflow["jobs"]["final"]["needs"]) == {
        "impact",
        "gates",
        "unavailable",
    }
    final_script = workflow["jobs"]["final"]["steps"][0]["run"]
    assert "HAS_UNAVAILABLE" in final_script
    assert "exit 1" in final_script


def test_contract_is_canonical_json() -> None:
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert document["schema_version"] == "scientific-change-impact.v1"
    assert document["unknown_path_policy"] == "all_declared_gates"
