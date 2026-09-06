from __future__ import annotations

from pathlib import Path

import pytest
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    AtlasBrowserContractError,
    AtlasCandidate,
    AtlasScope,
    BrowserVerificationPlan,
)

from .fixtures import BUILD_ID, SHA_A, SHA_B, SHA_C, candidate, write_static_atlas


def test_candidate_requires_exact_content_identities() -> None:
    with pytest.raises(AtlasBrowserContractError, match="repository_head"):
        AtlasCandidate("main", SHA_B, SHA_C, BUILD_ID)
    with pytest.raises(AtlasBrowserContractError, match="build_id"):
        AtlasCandidate(SHA_A, SHA_B, SHA_C, "latest")


def test_scope_rejects_escape_and_split_output_directories() -> None:
    with pytest.raises(AtlasBrowserContractError, match="safe .html"):
        AtlasScope("nordic", "../map.html", "docs/map.json")
    with pytest.raises(AtlasBrowserContractError, match="share an output"):
        AtlasScope("nordic", "docs/map.html", "docs/other/map.json")


def test_plan_requires_repository_artifacts_and_existing_browser(
    tmp_path: Path,
) -> None:
    scope = write_static_atlas(tmp_path)
    browser = tmp_path / "brave"
    browser.write_text("binary", encoding="utf-8")
    plan = BrowserVerificationPlan(
        repository_root=tmp_path,
        artifact_root=tmp_path / "artifacts/browser",
        browser_binary=browser,
        candidate=candidate(),
        scopes=(scope,),
    )

    assert plan.as_json()["timeout_seconds"] == 45
    assert BrowserVerificationPlan.from_json(plan.as_json()) == plan

    with pytest.raises(AtlasBrowserContractError, match="under artifacts"):
        BrowserVerificationPlan(
            repository_root=tmp_path,
            artifact_root=tmp_path / "evidence/browser",
            browser_binary=browser,
            candidate=candidate(),
            scopes=(scope,),
        )
