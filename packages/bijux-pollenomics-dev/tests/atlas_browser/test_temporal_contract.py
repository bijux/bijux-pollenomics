"""Opt-in temporal receipt versions cannot silently change legacy interpretation."""

from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.contracts import (
    NATIVE_LRA_PROFILE,
    SIGNED_CALENDAR_PROFILE,
    SIGNED_NATIVE_LRA_PROFILE,
    AtlasBrowserContractError,
)
from bijux_pollenomics_dev.ci.atlas_browser.temporal_contract import (
    presentation_temporal_identity,
    receipt_temporal_profile,
    validate_invocation,
)


def test_explicit_versions_bind_browser_and_presentation() -> None:
    legacy = {"schema_version": "atlas-artifact-generation.v1"}
    signed = {
        "schema_version": "atlas-artifact-generation.v2",
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    assert receipt_temporal_profile(legacy) is None
    assert receipt_temporal_profile(signed) == SIGNED_CALENDAR_PROFILE
    assert presentation_temporal_identity(legacy, NATIVE_LRA_PROFILE) == {
        "schema_version": "lra-presentation.v1"
    }
    assert presentation_temporal_identity(signed, SIGNED_NATIVE_LRA_PROFILE) == {
        "schema_version": "lra-presentation.v2",
        "temporal_profile": SIGNED_CALENDAR_PROFILE,
        "temporal_axis": "BP1950",
    }
    for receipt, browser in (
        (legacy, SIGNED_NATIVE_LRA_PROFILE),
        (signed, NATIVE_LRA_PROFILE),
        (signed, "unknown"),
    ):
        with pytest.raises(AtlasBrowserContractError, match="browser profile"):
            presentation_temporal_identity(receipt, browser)


@pytest.mark.parametrize(
    "value",
    [
        {},
        {"schema_version": "future"},
        {"schema_version": "atlas-artifact-generation.v1", "temporal_profile": None},
        {"schema_version": "atlas-artifact-generation.v1", "temporal_axis": "BP1950"},
        {"schema_version": "atlas-artifact-generation.v2"},
        {
            "schema_version": "atlas-artifact-generation.v2",
            "temporal_profile": SIGNED_CALENDAR_PROFILE,
            "temporal_axis": "radiocarbon",
        },
        {
            "schema_version": "atlas-artifact-generation.v2",
            "temporal_profile": True,
            "temporal_axis": "BP1950",
        },
    ],
)
def test_unknown_missing_or_legacy_signed_tags_refuse(value: dict[str, object]) -> None:
    with pytest.raises(AtlasBrowserContractError):
        receipt_temporal_profile(value)


@pytest.mark.parametrize(
    "mutation",
    [
        None,
        "cwd",
        "binary",
        "missing_arg",
        "changed_profile",
        "extra_field",
        "boolean_arg",
    ],
)
def test_invocation_keeps_exact_selected_profile(mutation: str | None) -> None:
    tail = ["-I", "-c", "literal source", "/source", SIGNED_CALENDAR_PROFILE]
    argv: list[object] = ["/env/bin/python", *tail]
    invocation: dict[str, object] = {
        "argv": argv,
        "cwd": "/source",
        "python_binary": "/env/bin/python",
    }
    if mutation == "cwd":
        invocation["cwd"] = "/other"
    elif mutation == "binary":
        invocation["python_binary"] = "/other/python"
    elif mutation == "missing_arg":
        argv.pop()
    elif mutation == "changed_profile":
        argv[-1] = "calendar-unverified"
    elif mutation == "extra_field":
        invocation["approved"] = True
    elif mutation == "boolean_arg":
        argv[-1] = True
    if mutation is None:
        validate_invocation(invocation, tail, source=Path("/source"))
    else:
        with pytest.raises(AtlasBrowserContractError):
            validate_invocation(invocation, tail, source=Path("/source"))
