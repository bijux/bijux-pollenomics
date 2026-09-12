"""Keep artifact releases bound to their requested tag and package version."""

import json
from pathlib import Path
from typing import Any, cast

import pytest
import yaml

REPOSITORY = Path(__file__).resolve().parents[4]
WORKFLOWS = REPOSITORY / ".github" / "workflows"
ARTIFACT_WORKFLOW = WORKFLOWS / "release-artifacts.yml"
RELEASE_CALLERS = (
    "release-github.yml",
    "release-pypi.yml",
    "release-ghcr.yml",
)
ARTIFACT_PUBLISH_JOBS = {
    "release-github.yml": "release",
    "release-pypi.yml": "publish_artifact",
    "release-ghcr.yml": "publish",
}


def _workflow(path: Path) -> dict[str, Any]:
    loaded = yaml.load(path.read_text(encoding="utf-8"), Loader=yaml.BaseLoader)
    assert isinstance(loaded, dict)
    return cast(dict[str, Any], loaded)


def test_artifact_builder_guards_revision_and_versions_before_upload() -> None:
    workflow = _workflow(ARTIFACT_WORKFLOW)
    workflow_call = workflow["on"]["workflow_call"]
    release_tag = workflow_call["inputs"]["release_tag"]
    assert release_tag == {"required": "true", "type": "string"}

    steps = workflow["jobs"]["build"]["steps"]
    checkout = next(step for step in steps if step["name"] == "Checkout repository")
    assert checkout["with"] == {
        "fetch-depth": "0",
        "fetch-tags": "true",
        "ref": "${{ github.sha }}",
    }

    names = [step["name"] for step in steps]
    guard_index = names.index("Verify release revision and repository artifact policy")
    assert guard_index < names.index("Upload publish artifacts")
    assert guard_index < names.index("Upload release artifacts")

    guard = steps[guard_index]
    assert guard["env"]["RELEASE_TAG"] == "${{ inputs.release_tag }}"
    script = guard["run"]
    assert "refs/tags/${RELEASE_TAG}^{commit}" in script
    assert '"${head_commit}" != "${GITHUB_SHA}"' in script
    assert guard["env"]["DIST_DIR"] == ".github/tmp/${{ inputs.package_slug }}-dist"
    assert (
        guard["env"]["RELEASE_ASSET_DIR"]
        == ".github/tmp/${{ inputs.package_slug }}-release"
    )
    assert 'eval "${verification_command}"' in script
    assert 'cmp -- "${distribution}"' in script
    manifest = json.loads(
        (REPOSITORY / ".github/standards/repo-config.manifest.json").read_text()
    )
    repository = next(
        item for item in manifest["repositories"] if item["name"] == "bijux-pollenomics"
    )
    settings = {item["key"]: item["value"] for item in repository["release_env"]}
    command = settings["BIJUX_RELEASE_ARTIFACT_VERIFICATION_COMMAND"]
    assert "bijux_pollenomics_dev.release.publication_guard" in command
    assert '--dist-dir "${DIST_DIR}"' in command
    assert 'test "${resolved_version}" = "${RELEASE_TAG#v}"' in command
    assert "--allow-prerelease" not in command
    assert "--allow-local-version" not in command


@pytest.mark.parametrize("filename", RELEASE_CALLERS)
def test_artifact_release_callers_pass_resolved_release_tag(filename: str) -> None:
    workflow = _workflow(WORKFLOWS / filename)
    build = workflow["jobs"]["build"]
    assert build["uses"] == "./.github/workflows/release-artifacts.yml"
    assert build["with"]["release_tag"] == "${{ needs.resolve.outputs.release_tag }}"
    publish = workflow["jobs"][ARTIFACT_PUBLISH_JOBS[filename]]
    assert "build" in publish["needs"]
