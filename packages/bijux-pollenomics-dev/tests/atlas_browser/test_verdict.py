from __future__ import annotations

from typing import cast

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    GENERIC_TIME_AWARE_PROFILE,
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    AtlasBrowserContractError,
)
from bijux_pollenomics_dev.ci.atlas_browser.verdict import (
    GENERIC_TIME_AWARE_REQUIRED_ASSERTIONS,
    PROFILE_REQUIRED_ASSERTIONS,
    evaluate_browser_report,
)

from .fixtures import candidate


def _report(
    *,
    profile: str = NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    failed: str | None = None,
) -> dict[str, object]:
    assertions = {name: name != failed for name in PROFILE_REQUIRED_ASSERTIONS[profile]}
    return {
        "schema_version": "atlas-browser-runtime-report.v2",
        "verification_profile": profile,
        "candidate": candidate().as_json(),
        "browser": {
            "product": "Chrome/140.0.0.0",
            "revision": "@0123456789abcdef",
            "user_agent": "Mozilla/5.0 HeadlessChrome/140.0.0.0",
            "javascript_version": "14.0.0",
            "protocol_version": "1.3",
            "binary": "/usr/bin/google-chrome",
        },
        "assertions": assertions,
        "scenarios": [{"name": "synthetic"}],
        "receipts": ["synthetic.json"],
    }


def test_complete_true_evidence_passes() -> None:
    summary = evaluate_browser_report(
        _report(),
        candidate=candidate(),
        verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    )

    assert summary["status"] == "PASS"
    assert summary["failed_assertions"] == []


def test_one_false_assertion_fails() -> None:
    summary = evaluate_browser_report(
        _report(failed="provider_failure_evidence_unchanged"),
        candidate=candidate(),
        verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    )

    assert summary["status"] == "FAIL"
    assert summary["failed_assertions"] == ["provider_failure_evidence_unchanged"]


def test_false_capture_clarity_assertion_fails_closed() -> None:
    summary = evaluate_browser_report(
        _report(failed="capture_frames_uncluttered"),
        candidate=candidate(),
        verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    )

    assert summary["status"] == "FAIL"
    assert summary["failed_assertions"] == ["capture_frames_uncluttered"]


@pytest.mark.parametrize(
    "failed",
    (
        "capture_null_inputs_refused",
        "chronology_buttons_navigate",
        "chronology_controls_persistent",
        "chronology_status_action",
        "basemap_discoverability",
        "source_slider_changes_visibility",
    ),
)
def test_chronology_and_null_assertions_fail_closed(failed: str) -> None:
    summary = evaluate_browser_report(
        _report(failed=failed),
        candidate=candidate(),
        verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    )

    assert summary["status"] == "FAIL"
    assert summary["failed_assertions"] == [failed]


def test_missing_or_extra_assertions_are_refused() -> None:
    report = _report()
    assertions = report["assertions"]
    assert isinstance(assertions, dict)
    assertions.pop("comparison_refusal")
    assertions["looks_reasonable"] = True

    with pytest.raises(AtlasBrowserContractError, match="not exact"):
        evaluate_browser_report(
            report,
            candidate=candidate(),
            verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )


def test_candidate_substitution_is_refused() -> None:
    report = _report()
    report_candidate = report["candidate"]
    assert isinstance(report_candidate, dict)
    report_candidate["repository_head"] = "f" * 64

    with pytest.raises(AtlasBrowserContractError, match="identity differs"):
        evaluate_browser_report(
            report,
            candidate=candidate(),
            verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )


@pytest.mark.parametrize("field", ["product", "revision", "binary"])
def test_incomplete_browser_identity_is_refused(field: str) -> None:
    report = _report()
    browser = report["browser"]
    assert isinstance(browser, dict)
    browser[field] = ""

    with pytest.raises(AtlasBrowserContractError, match="identity is incomplete"):
        evaluate_browser_report(
            report,
            candidate=candidate(),
            verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )


def test_generic_profile_has_an_exact_independent_verdict() -> None:
    report = _report(profile=GENERIC_TIME_AWARE_PROFILE)

    summary = evaluate_browser_report(
        report,
        candidate=candidate(),
        verification_profile=GENERIC_TIME_AWARE_PROFILE,
    )

    assert summary["status"] == "PASS"
    assertions = cast(list[str], summary["assertions"])
    assert set(assertions) == GENERIC_TIME_AWARE_REQUIRED_ASSERTIONS
    assert "capture_frames_uncluttered" not in GENERIC_TIME_AWARE_REQUIRED_ASSERTIONS
    with pytest.raises(AtlasBrowserContractError, match="profile differs"):
        evaluate_browser_report(
            report,
            candidate=candidate(),
            verification_profile=NORDIC_SOURCE_CHRONOLOGY_PROFILE,
        )
