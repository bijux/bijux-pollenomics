"""Independent verdict calculation over browser-produced evidence."""

from __future__ import annotations

from typing import cast

from .contracts import (
    GENERIC_TIME_AWARE_PROFILE,
    NORDIC_SOURCE_CHRONOLOGY_PROFILE,
    AtlasBrowserContractError,
    AtlasCandidate,
    JsonObject,
)

NORDIC_SOURCE_CHRONOLOGY_REQUIRED_ASSERTIONS = frozenset(
    {
        "capture_api_ready",
        "candidate_identity",
        "keyless_provider_policy",
        "default_sample_window",
        "default_denominators",
        "trsh_exact_state",
        "uphe_exact_state",
        "aqvp_exact_state",
        "secale_exact_state",
        "cereal_finder_exact_state",
        "chronology_buttons_navigate",
        "chronology_controls_persistent",
        "chronology_status_action",
        "basemap_discoverability",
        "comparison_refusal",
        "capture_null_inputs_refused",
        "responsive_1440",
        "responsive_1024",
        "responsive_768",
        "responsive_390",
        "reduced_motion_manual_navigation",
        "no_basemap_zero_tile_requests",
        "provider_failure_osm_terrain_none",
        "provider_failure_evidence_unchanged",
        "runtime_console_clean",
        "source_slider_changes_visibility",
        "receipt_inventory_complete",
    }
)
GENERIC_TIME_AWARE_REQUIRED_ASSERTIONS = frozenset(
    {
        "capture_api_ready",
        "candidate_identity",
        "keyless_provider_policy",
        "default_time_domain_matches_manifest",
        "time_controls_persistent",
        "time_status_action",
        "time_slider_changes_visibility",
        "time_buttons_navigate",
        "basemap_discoverability",
        "scientific_posture_matches_manifest",
        "capture_invalid_inputs_refused",
        "responsive_1440",
        "responsive_1024",
        "responsive_768",
        "responsive_390",
        "reduced_motion_manual_navigation",
        "no_basemap_zero_tile_requests",
        "provider_failure_osm_terrain_none",
        "provider_failure_evidence_unchanged",
        "runtime_console_clean",
        "receipt_inventory_complete",
    }
)
PROFILE_REQUIRED_ASSERTIONS = {
    NORDIC_SOURCE_CHRONOLOGY_PROFILE: NORDIC_SOURCE_CHRONOLOGY_REQUIRED_ASSERTIONS,
    GENERIC_TIME_AWARE_PROFILE: GENERIC_TIME_AWARE_REQUIRED_ASSERTIONS,
}
REQUIRED_ASSERTIONS = NORDIC_SOURCE_CHRONOLOGY_REQUIRED_ASSERTIONS


def _mapping(value: object, *, label: str) -> JsonObject:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise AtlasBrowserContractError(f"{label} must be an object")
    return cast(JsonObject, value)


def evaluate_browser_report(
    report: object, *, candidate: AtlasCandidate, verification_profile: str
) -> JsonObject:
    """Return PASS only when the report has every exact, true assertion."""
    document = _mapping(report, label="browser report")
    if document.get("schema_version") != "atlas-browser-runtime-report.v2":
        raise AtlasBrowserContractError("browser report schema_version is unsupported")
    if document.get("verification_profile") != verification_profile:
        raise AtlasBrowserContractError("browser report verification profile differs")
    required_assertions = PROFILE_REQUIRED_ASSERTIONS.get(verification_profile)
    if required_assertions is None:
        raise AtlasBrowserContractError("browser verification profile is unsupported")
    report_candidate = _mapping(document.get("candidate"), label="report.candidate")
    if report_candidate != candidate.as_json():
        raise AtlasBrowserContractError("browser report candidate identity differs")
    assertions = _mapping(document.get("assertions"), label="report.assertions")
    if set(assertions) != required_assertions:
        missing = sorted(required_assertions - set(assertions))
        additional = sorted(set(assertions) - required_assertions)
        raise AtlasBrowserContractError(
            f"browser assertions are not exact; missing={missing}, additional={additional}"
        )
    invalid_types = sorted(
        name for name, passed in assertions.items() if not isinstance(passed, bool)
    )
    if invalid_types:
        raise AtlasBrowserContractError(
            f"browser assertions are not booleans: {invalid_types}"
        )
    failed = sorted(name for name, passed in assertions.items() if passed is False)
    scenarios = document.get("scenarios")
    receipts = document.get("receipts")
    if not isinstance(scenarios, list) or not scenarios:
        raise AtlasBrowserContractError("browser scenarios must be non-empty")
    if not isinstance(receipts, list) or not receipts:
        raise AtlasBrowserContractError("browser receipts must be non-empty")
    return {
        "schema_version": "atlas-browser-verification-summary.v2",
        "status": "PASS" if not failed else "FAIL",
        "verification_profile": verification_profile,
        "failed_assertions": failed,
        "candidate": candidate.as_json(),
        "assertions": assertions,
        "scenario_count": len(scenarios),
        "receipt_count": len(receipts),
    }
