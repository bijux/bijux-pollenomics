from __future__ import annotations

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    GENERIC_TIME_AWARE_PROFILE,
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
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
    assert plan.as_json()["schema_version"] == "atlas-browser-verification-plan.v2"
    assert plan.as_json()["verification_profile"] == NORDIC_SOURCE_CHRONOLOGY_PROFILE
    assert BrowserVerificationPlan.from_json(plan.as_json()) == plan

    with pytest.raises(AtlasBrowserContractError, match="under artifacts"):
        BrowserVerificationPlan(
            repository_root=tmp_path,
            artifact_root=tmp_path / "evidence/browser",
            browser_binary=browser,
            candidate=candidate(),
            scopes=(scope,),
        )


def test_plan_profiles_cannot_weaken_exact_nordic_verification(tmp_path: Path) -> None:
    nordic = write_static_atlas(tmp_path)
    world = AtlasScope("world", nordic.document, nordic.manifest)
    browser = tmp_path / "brave"
    browser.write_text("binary", encoding="utf-8")

    def plan(*, scope: AtlasScope, profile: str) -> BrowserVerificationPlan:
        return BrowserVerificationPlan(
            repository_root=tmp_path,
            artifact_root=tmp_path / "artifacts/browser",
            browser_binary=browser,
            candidate=candidate(),
            scopes=(scope,),
            verification_profile=profile,
        )

    generic = plan(
        scope=world,
        profile=GENERIC_TIME_AWARE_PROFILE,
    )

    assert BrowserVerificationPlan.from_json(generic.as_json()) == generic
    with pytest.raises(AtlasBrowserContractError, match="cannot replace exact nordic"):
        plan(
            scope=nordic,
            profile=GENERIC_TIME_AWARE_PROFILE,
        )
    with pytest.raises(AtlasBrowserContractError, match="requires only the nordic"):
        plan(
            scope=world,
            profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )
    with pytest.raises(AtlasBrowserContractError, match="unsupported"):
        plan(
            scope=world,
            profile="looks-generic",
        )
