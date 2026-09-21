"""Execute the actual probe startup guards before any browser side effects."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

from bijux_pollenomics_dev.ci import atlas_browser
from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    NATIVE_LRA_PROFILE,
    RAA_RETAINED_CONTEXT_PROFILE,
    SIGNED_NATIVE_LRA_PROFILE,
    VERIFICATION_PROFILES,
)


def test_actual_profile_and_candidate_entry_guards_match_declared_contract() -> None:
    source = Path(atlas_browser.__file__).with_name("probe.mjs").read_text()
    schema = source[
        source.index("if (!['atlas-browser-verification-plan.v2'") : source.index(
            "const repositoryRoot"
        )
    ]
    profile = source[
        source.index("const verificationProfile") : source.index("const providerHosts")
    ]
    kind = source[
        source.index("const nativeArtifactMode") : source.index("let activeScenario")
    ]
    profiles = [*sorted(VERIFICATION_PROFILES), "unknown", None, True]
    plans = [
        {"schema_version": schema, "verification_profile": profile}
        for schema in [
            "atlas-browser-verification-plan.v2",
            "atlas-browser-verification-plan.v3",
            "atlas-browser-verification-plan.v4",
            "unsupported",
        ]
        for profile in profiles
    ]
    script = (
        "function admit(plan){try{"
        + schema
        + profile
        + kind
        + "return true;}catch{return false;}}\n"
    )
    script += f"console.log(JSON.stringify({json.dumps(plans)}.map(admit)));"
    completed = subprocess.run(
        ["node", "--input-type=module", "--eval", script],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    observed = json.loads(completed.stdout)
    expected = [
        plan["schema_version"]
        in {
            "atlas-browser-verification-plan.v2",
            "atlas-browser-verification-plan.v3",
            "atlas-browser-verification-plan.v4",
        }
        and plan["verification_profile"] in VERIFICATION_PROFILES
        and (
            (plan["schema_version"] == "atlas-browser-verification-plan.v3")
            == (
                plan["verification_profile"]
                in {NATIVE_LRA_PROFILE, SIGNED_NATIVE_LRA_PROFILE}
            )
            and (plan["schema_version"] == "atlas-browser-verification-plan.v4")
            == (plan["verification_profile"] == RAA_RETAINED_CONTEXT_PROFILE)
        )
        for plan in plans
    ]
    assert observed == expected
    assert sum(observed) == 5
