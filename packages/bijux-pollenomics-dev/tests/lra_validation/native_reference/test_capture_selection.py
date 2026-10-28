"""Keep finite native capture selection explicit and refuse silent fallback."""

from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference import (
    capture_selection as selector,
)


@pytest.mark.parametrize(
    "profile", [None, "annulus", "count-domain", "finite-covariance"]
)
def test_only_selected_validator_runs(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, profile: str | None
) -> None:
    historical = object()
    current = object()
    finite = object()
    calls: list[str] = []

    def annulus(root: Path) -> Any:
        assert root == tmp_path
        calls.append("annulus")
        return historical

    def count_domain(root: Path) -> Any:
        assert root == tmp_path
        calls.append("count-domain")
        return current

    def finite_covariance(root: Path) -> Any:
        assert root == tmp_path
        calls.append("finite-covariance")
        return finite

    monkeypatch.setattr(
        selector, "validated_finite_covariance_capture", finite_covariance
    )
    monkeypatch.setattr(selector, "validated_annulus_capture", annulus)
    monkeypatch.setattr(selector, "validated_count_domain_capture", count_domain)
    result = (
        selector.validated_current_capture(tmp_path)
        if profile is None
        else selector.validated_current_capture(tmp_path, profile=cast(Any, profile))
    )
    expected = {
        "annulus": historical,
        "count-domain": current,
        "finite-covariance": finite,
    }
    assert result is expected[profile or "annulus"]
    assert calls == [profile or "annulus"]


@pytest.mark.parametrize("profile", ["unknown", "", None, False, 1])
def test_unknown_explicit_profile_refuses_before_source_access(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, profile: object
) -> None:
    def forbidden(root: Path) -> Any:
        raise AssertionError("Unrecognized selection accessed a source")

    monkeypatch.setattr(selector, "validated_annulus_capture", forbidden)
    monkeypatch.setattr(selector, "validated_count_domain_capture", forbidden)
    monkeypatch.setattr(selector, "validated_finite_covariance_capture", forbidden)
    with pytest.raises(ValueError, match="profile"):
        selector.validated_current_capture(tmp_path, profile=cast(Any, profile))


@pytest.mark.parametrize("profile", ["count-domain", "finite-covariance"])
@pytest.mark.parametrize("error", [FileNotFoundError, ValueError])
def test_selected_packet_failure_never_falls_back(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    error: type[Exception],
    profile: str,
) -> None:
    def failed(root: Path) -> Any:
        raise error("Selected packet missing or unauthenticated")

    def forbidden(root: Path) -> Any:
        raise AssertionError("Failed current selection silently fell back")

    monkeypatch.setattr(selector, "validated_count_domain_capture", failed)
    monkeypatch.setattr(selector, "validated_finite_covariance_capture", failed)
    monkeypatch.setattr(selector, "validated_annulus_capture", forbidden)
    with pytest.raises(error, match="Selected packet"):
        selector.validated_current_capture(tmp_path, profile=cast(Any, profile))
