"""Contracts for selection-aware scientific verification."""

from __future__ import annotations

from fnmatch import fnmatchcase
import json
from pathlib import Path
import re
from zipfile import ZipFile

import pytest
import yaml

from bijux_pollenomics_dev.ci.path_selection import (
    REQUIRED_SURFACE_IDS,
    ChangeImpactContract,
    load_contract,
    select_changed_paths,
)
from bijux_pollenomics_dev.ci.report_rebuild import configured_owner
from bijux_pollenomics_dev.ci.report_rebuild.qualified_sources import (
    QualifiedReportSources,
)
from bijux_pollenomics_dev.ci.report_rebuild.scheduling import (
    configured_owner_schedule,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
CONTRACT_PATH = REPO_ROOT / "configs" / "ci" / "scientific-change-impact.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "scientific-verification.yml"
ATLAS_WORKFLOW_PATH = (
    REPO_ROOT / ".github" / "workflows" / "atlas-release-verification.yml"
)
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
            "packages/bijux-pollenomics/src/bijux_pollenomics/evidence/classification/neotoma/accounting.py",
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


def test_scientific_evidence_materializer_selects_every_mandatory_gate() -> None:
    result = select_changed_paths(
        _contract(),
        [
            "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/scientific_evidence.py"
        ],
    )

    assert "evidence-contracts-and-manifests" in result.matched_surfaces
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
    assert result.unavailable_gates == ()


def test_manual_full_selection_contains_only_executable_premerge_gates() -> None:
    result = select_changed_paths(_contract(), [], select_all=True)

    assert result.unavailable_gates == ()
    assert set(result.available_gates) == set(_contract().gate_order)
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
        "provenance",
        "map",
    }
    assert workflow["jobs"]["doc-counts"]["name"] == "scientific / doc-counts"
    assert workflow["jobs"]["rebuild-verify"]["name"] == "scientific / rebuild"
    assert set(workflow["jobs"]["doc-counts"]["needs"]) == {
        "impact",
        "doc-count-plan",
        "doc-count-shards",
    }
    assert set(workflow["jobs"]["rebuild-verify"]["needs"]) == {
        "impact",
        "rebuild-plan",
        "rebuild-assemble",
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
        "doc-counts",
        "rebuild-verify",
        "unavailable",
    }
    final_script = workflow["jobs"]["final"]["steps"][0]["run"]
    assert "HAS_UNAVAILABLE" in final_script
    assert "DOC_COUNTS_RESULT" in final_script
    assert "REBUILD_RESULT" in final_script
    assert "exit 1" in final_script


def test_contract_is_canonical_json() -> None:
    document = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))

    assert document["schema_version"] == "scientific-change-impact.v1"
    assert document["unknown_path_policy"] == "all_declared_gates"
    assert "browser" not in document["gates"]
    assert "deployed-smoke" not in document["gates"]


def test_atlas_workflow_separates_premerge_browser_from_postdeployment_smoke() -> None:
    workflow = yaml.load(
        ATLAS_WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    events = workflow["on"]
    jobs = workflow["jobs"]

    assert {"push", "pull_request", "merge_group", "workflow_dispatch"} <= set(events)
    assert events["workflow_run"] == {
        "workflows": ["deploy-docs"],
        "types": ["completed"],
        "branches": ["main"],
    }
    browser_job = jobs["browser"]
    smoke_job = jobs["deployed-smoke"]
    assert "github.event_name != 'workflow_run'" in browser_job["if"]
    assert DEPENDABOT_SKIP in browser_job["if"]
    assert "github.event_name == 'workflow_run'" in smoke_job["if"]
    assert "github.event.workflow_run.conclusion == 'success'" in smoke_job["if"]
    assert "github.event.workflow_run.head_branch == 'main'" in smoke_job["if"]
    assert DEPENDABOT_SKIP in smoke_job["if"]

    browser_script = "\n".join(step.get("run", "") for step in browser_job["steps"])
    assert "repository_head" in browser_script
    assert "repository_tree" in browser_script
    assert "atlas_output_commit" in browser_script
    assert "nordic-source-chronology-v1" in browser_script
    assert "packages/bijux-pollenomics/src" in browser_script
    assert "uv sync --frozen --group dev --python python3" in browser_script
    assert "artifacts/root/check-venv/bin/python" in browser_script
    assert "bijux_pollenomics_dev.ci.atlas_browser.runner" in browser_script

    smoke_script = "\n".join(step.get("run", "") for step in smoke_job["steps"])
    assert "DEPLOYED_CANDIDATE_SHA" in smoke_script
    assert "workflow_run.head_sha" in smoke_job["steps"][0]["with"]["ref"]
    assert "nordic_map.html" in smoke_script
    assert "nordic_map_assets.json" in smoke_script
    assert "publication-manifest.json" in smoke_script
    assert "deployed bytes differ from candidate" in smoke_script

    action_references = [
        step["uses"]
        for job in jobs.values()
        for step in job.get("steps", [])
        if "uses" in step
    ]
    assert action_references
    assert all(PINNED_ACTION.fullmatch(reference) for reference in action_references)


@pytest.fixture
def configured_owner_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> list[dict[str, str]]:
    """Supply synthetic external inputs for CI identity and archive layout only.

    These tests execute no producer and make no source-custody claim. Real
    external authentication and missing-store refusals have separate tests.
    """
    store = tmp_path / "source-store"

    def synthetic_sources(
        repository: Path, source_root: Path, descriptor_path: Path
    ) -> QualifiedReportSources:
        assert repository == REPO_ROOT and source_root == store
        descriptor_file = repository / descriptor_path
        descriptor = json.loads(descriptor_file.read_text())
        identity = descriptor["source_id"]
        directory = store / identity
        directory.mkdir(parents=True, exist_ok=True)
        inputs = {descriptor_path.as_posix(): descriptor_file}
        schema = descriptor["schema_version"]
        if schema in {
            "qualified-report-source-bundle.v1",
            "qualified-publisher-report-tables.v1",
        }:
            packets = [
                (identity, Path(), [descriptor["custody"], *descriptor["files"]])
            ]
        elif schema in {
            "qualified-pangaea-solsoe-age-table.v1",
            "qualified-pangaea-epd-age-table.v1",
        }:
            packets = [(identity, Path(), [descriptor["table"]])]
        elif schema == "qualified-author-snapshot.v1":
            packets = [
                (identity, Path(), [descriptor["manifest"], *descriptor["files"]])
            ]
        elif schema == "qualified-landclim-two-grid-packet.v1":
            author = json.loads(
                (repository / descriptor["author_descriptor"]).read_text()
            )
            packets = [
                (
                    author["source_id"],
                    Path(),
                    [author["manifest"], *author["files"]],
                ),
                (identity, Path(descriptor["run_path"]), descriptor["files"]),
            ]
        elif schema == "qualified-neotoma-publication-link.v1":
            packets = [
                (
                    identity,
                    Path(),
                    [descriptor["capture_manifest"], descriptor["response"]],
                )
            ]
        else:
            raise AssertionError(f"Unreviewed synthetic source schema: {schema}")
        for source_id, prefix, specs in packets:
            for spec in specs:
                path = store / source_id / prefix / spec["path"]
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("synthetic archive-layout fixture\n", encoding="utf-8")
                inputs[f"external/{source_id}/{prefix / spec['path']}"] = path
        if schema in {
            "qualified-pangaea-solsoe-age-table.v1",
            "qualified-pangaea-epd-age-table.v1",
        }:
            assert set(inputs) == {
                descriptor_path.as_posix(),
                f"external/{identity}/{descriptor['table']['path']}",
            }
        if schema == "qualified-landclim-two-grid-packet.v1":
            assert len(inputs) == 265
        if schema == "qualified-neotoma-publication-link.v1":
            assert set(inputs) == {
                descriptor_path.as_posix(),
                f"external/{identity}/capture-manifest.json",
                f"external/{identity}/responses/dataset-4200-publications.json",
            }
        return QualifiedReportSources(directory, inputs, "a" * 64)

    monkeypatch.setattr(
        configured_owner, "validated_external_report_sources", synthetic_sources
    )
    rows = configured_owner_schedule(REPO_ROOT, source_root=store)["owners"]
    assert isinstance(rows, list)
    return rows


def test_report_owner_ci_matrix_matches_configured_execution_contract(
    configured_owner_rows: list[dict[str, str]],
) -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    configured = json.loads(
        (REPO_ROOT / "configs/ci/report-owner-execution.json").read_text()
    )
    owner_job = workflow["jobs"]["rebuild-owners"]
    matrix = owner_job["strategy"]["matrix"]
    assert matrix["owner"] == "${{ fromJSON(needs.rebuild-plan.outputs.owners) }}"
    rows = configured_owner_rows
    assert isinstance(rows, list)
    assert {row["id"] for row in rows} == {
        row["owner_id"] for row in configured["owners"]
    }
    assert set(matrix["lane"]) == {"reference", "replay"}
    assert len({row["id"] for row in rows}) == len(rows)
    assert len({row["artifact"] for row in rows}) == len(rows)
    plan_outputs = workflow["jobs"]["rebuild-plan"]["outputs"]
    assert plan_outputs["owners"] == "${{ steps.plan.outputs.owners }}"
    assert plan_outputs["owner_ids"] == "${{ steps.plan.outputs.owner_ids }}"
    assert set(owner_job["needs"]) == {"impact", "rebuild-plan"}
    assert owner_job["strategy"]["fail-fast"] == "false"
    assert int(owner_job["timeout-minutes"]) == 10
    build = next(
        step
        for step in owner_job["steps"]
        if step.get("run") == "make build-report-rebuild-owner"
    )
    assert build["env"]["REBUILD_OWNER_ID"] == "${{ matrix.owner.id }}"
    assert build["env"]["REBUILD_EVIDENCE_ROOT"].endswith(
        "/${{ matrix.lane }}/${{ matrix.owner.id }}"
    )
    upload = next(
        step
        for step in owner_job["steps"]
        if step.get("name") == "Upload owner output and diagnostics"
    )
    assert upload["with"]["name"].startswith("report-owner-")
    assert upload["if"] == "always()"
    assert upload["with"]["if-no-files-found"] == "error"
    assert upload["with"]["name"] == (
        "report-owner-${{ matrix.lane }}-${{ matrix.owner.artifact }}"
    )
    assert upload["with"]["path"] == (
        "artifacts/execution-control/report-rebuild-owner/${{ matrix.lane }}"
    )


def test_report_owner_ci_downloads_preserve_exact_nested_identities(
    configured_owner_rows: list[dict[str, str]],
) -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    jobs = workflow["jobs"]
    owners = configured_owner_rows
    assert isinstance(owners, list)
    assembly = jobs["rebuild-assemble"]
    assert "rebuild-owners" in assembly["needs"]
    for job, lanes, target in (
        (assembly, ("${{ matrix.lane }}",), "make assemble-report-rebuild"),
        (
            jobs["rebuild-verify"],
            ("reference", "replay"),
            "make verify-partitioned-report-rebuild",
        ),
    ):
        owner_downloads = [
            step
            for step in job["steps"]
            if step.get("uses", "").startswith("actions/download-artifact")
            and step.get("with", {}).get("pattern", "").startswith("report-owner-")
        ]
        assert len(owner_downloads) == len(lanes)
        for lane, download in zip(lanes, owner_downloads, strict=True):
            settings = download["with"]
            assert "name" not in settings
            assert settings["pattern"] == f"report-owner-{lane}-*"
            assert settings["path"] == (
                f"artifacts/execution-control/report-rebuild-owner-input/{lane}"
            )
            assert settings["merge-multiple"] == "true"
            for owner in owners:
                assert fnmatchcase(
                    f"report-owner-{lane}-{owner['artifact']}", settings["pattern"]
                )
            assert not fnmatchcase(
                f"report-rebuild-{lane}-foundation", settings["pattern"]
            )
        run = next(step for step in job["steps"] if step.get("run") == target)
        assert run["env"]["REBUILD_OWNER_IDS"] == (
            "${{ needs.rebuild-plan.outputs.owner_ids }}"
        )
        if len(lanes) == 1:
            assert (
                run["env"]["REBUILD_OWNER_ARTIFACTS_ROOT"]
                == f"artifacts/execution-control/report-rebuild-owner-input/{lanes[0]}"
            )
        else:
            for lane in lanes:
                assert (
                    run["env"][f"REBUILD_{lane.upper()}_OWNERS_ROOT"]
                    == f"artifacts/execution-control/report-rebuild-owner-input/{lane}"
                )
    partitions = next(
        step
        for step in assembly["steps"]
        if step.get("name") == "Download complete partition set"
    )
    assert partitions["with"]["pattern"] == "report-rebuild-${{ matrix.lane }}-*"
    assert not partitions["with"]["pattern"].startswith("report-owner")


def test_owner_lane_root_archives_keep_duplicate_leaf_names_separate(
    tmp_path: Path,
    configured_owner_rows: list[dict[str, str]],
) -> None:
    workflow = yaml.load(
        WORKFLOW_PATH.read_text(encoding="utf-8"), Loader=yaml.BaseLoader
    )
    owner_job = workflow["jobs"]["rebuild-owners"]
    assert owner_job["steps"][-1]["with"]["path"].endswith("/${{ matrix.lane }}")
    owners = configured_owner_rows
    assert isinstance(owners, list)
    same_leaf = [row for row in owners if row["id"].endswith("/report-products")]
    assert len(same_leaf) >= 2
    selected = same_leaf[:2]
    merged = tmp_path / "downloaded-owner-lane"
    merged.mkdir()
    expected: dict[str, str] = {}
    for index, owner in enumerate(selected):
        identity = owner["id"]
        archive = tmp_path / f"owner-{index}.zip"
        with ZipFile(archive, "w") as bundle:
            bundle.writestr(f"{identity}/manifest.json", identity)
            bundle.writestr(f"{identity}/producer.stderr.log", f"diagnostic {index}")
            bundle.writestr(f"{identity}/output/{index}.json", f'{{"owner": {index}}}')
        with ZipFile(archive) as bundle:
            bundle.extractall(merged)
        expected[identity] = f"diagnostic {index}"
    assert {
        path.relative_to(merged).as_posix() for path in merged.rglob("manifest.json")
    } == {f"{identity}/manifest.json" for identity in expected}
    for identity, diagnostic in expected.items():
        assert (merged / identity / "manifest.json").read_text() == identity
        assert (merged / identity / "producer.stderr.log").read_text() == diagnostic


def test_report_plan_preflights_owner_schedule_before_writing_partition_plan() -> None:
    makefile = (REPO_ROOT / "makes/pollenomics-verification.mk").read_text()
    recipe = makefile.split("plan-report-rebuild: root-check-env", 1)[1].split(
        "\nbuild-report-rebuild-partition:", 1
    )[0]
    assert recipe.count("-m bijux_pollenomics_dev.ci.report_rebuild.scheduling") == 2
    assert recipe.index("--check-only") < recipe.index(
        "-m bijux_pollenomics_dev.ci.report_rebuild plan"
    )
    assert recipe.index(
        "-m bijux_pollenomics_dev.ci.report_rebuild plan"
    ) < recipe.rindex("-m bijux_pollenomics_dev.ci.report_rebuild.scheduling")
