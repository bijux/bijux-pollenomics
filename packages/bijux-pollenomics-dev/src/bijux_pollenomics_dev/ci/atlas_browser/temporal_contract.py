"""Explicit temporal presentation/receipt versions; no source or Git authority."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

from .contracts import (
    NATIVE_LRA_PROFILE,
    SIGNED_CALENDAR_PROFILE,
    SIGNED_NATIVE_LRA_PROFILE,
    AtlasBrowserContractError,
)


def receipt_temporal_profile(receipt: Mapping[str, Any]) -> str | None:
    """Refuse tags without the exact opt-in receipt version and axis."""
    if receipt.get("schema_version") == "atlas-artifact-generation.v1":
        if "temporal_profile" in receipt or "temporal_axis" in receipt:
            raise AtlasBrowserContractError(
                "legacy generator cannot declare signed chronology"
            )
        return None
    if (
        receipt.get("schema_version") != "atlas-artifact-generation.v2"
        or receipt.get("temporal_profile") != SIGNED_CALENDAR_PROFILE
        or receipt.get("temporal_axis") != "BP1950"
    ):
        raise AtlasBrowserContractError("unsupported generator temporal contract")
    return SIGNED_CALENDAR_PROFILE


def presentation_temporal_identity(
    receipt: Mapping[str, Any], browser_profile: str
) -> dict[str, str]:
    """Bind the requested browser profile to the admitted generator declaration."""
    profile = receipt_temporal_profile(receipt)
    if browser_profile == NATIVE_LRA_PROFILE and profile is None:
        return {"schema_version": "lra-presentation.v1"}
    if (
        browser_profile == SIGNED_NATIVE_LRA_PROFILE
        and profile == SIGNED_CALENDAR_PROFILE
    ):
        return {
            "schema_version": "lra-presentation.v2",
            "temporal_profile": profile,
            "temporal_axis": "BP1950",
        }
    raise AtlasBrowserContractError("generator receipt and browser profile differ")


def validate_invocation(
    invocation: object, expected_tail: Sequence[str], *, source: Path
) -> None:
    """Validate declared argv/cwd without executing or authenticating source bytes."""
    if not isinstance(invocation, dict) or set(invocation) != {
        "argv",
        "cwd",
        "python_binary",
    }:
        raise AtlasBrowserContractError("generator invocation is incomplete")
    argv = invocation["argv"]
    binary = invocation["python_binary"]
    if (
        not isinstance(argv, list)
        or len(argv) != len(expected_tail) + 1
        or any(not isinstance(value, str) for value in argv)
        or not isinstance(binary, str)
        or not Path(binary).is_absolute()
        or argv[0] != binary
        or invocation["cwd"] != str(source)
    ):
        raise AtlasBrowserContractError("generator invocation identity differs")
    if argv[1:] != list(expected_tail):
        raise AtlasBrowserContractError("generator invocation arguments differ")
