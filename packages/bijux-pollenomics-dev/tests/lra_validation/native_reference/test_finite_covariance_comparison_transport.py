"""Retained comparison source admission preserves exact routes and direct-source guards."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.lra_validation import live_reference_comparison as comparison


def test_direct_current_source_guard_remains_strict(tmp_path: Path) -> None:
    path = tmp_path / "source.py"
    body = b"controlled_source = 1\n"
    path.write_bytes(body)
    receipt = {"current_inputs_sha256": {"source.py": hashlib.sha256(body).hexdigest()}}
    comparison._require_current_inputs(
        tmp_path, tmp_path / "run", tmp_path / "archives", receipt
    )
    path.write_bytes(body + b" ")
    with pytest.raises(ValueError, match="Current R/Python input changed"):
        comparison._require_current_inputs(
            tmp_path, tmp_path / "run", tmp_path / "archives", receipt
        )


@pytest.mark.parametrize(
    "change", [None, "run", "archives", "hash", "unknown-profile", "source-refusal"]
)
def test_retained_profile_requires_guarded_capture_and_exact_routes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str | None
) -> None:
    run, archives = tmp_path / "run", tmp_path / "archives"
    expected = {"source.py": "a" * 64}
    receipt = {"current_inputs_sha256": dict(expected)}
    calls: list[Path] = []

    def admitted(repository: Path) -> Any:
        calls.append(repository)
        if change == "source-refusal":
            raise ValueError("Current protected source differs")
        return SimpleNamespace(
            directory=run,
            source_archives=archives,
            source_context={"protected_science_sha256": expected},
        )

    monkeypatch.setattr(comparison, "validated_finite_covariance_capture", admitted)
    selected_run = tmp_path / "other-run" if change == "run" else run
    selected_archives = (
        tmp_path / "other-archives" if change == "archives" else archives
    )
    if change == "hash":
        receipt["current_inputs_sha256"]["source.py"] = "b" * 64
    profile = "other" if change == "unknown-profile" else "finite-covariance"
    if change is None:
        comparison._require_current_inputs(
            tmp_path,
            selected_run,
            selected_archives,
            receipt,
            retained_capture_profile=profile,
        )
        assert calls == [tmp_path]
    else:
        with pytest.raises(ValueError):
            comparison._require_current_inputs(
                tmp_path,
                selected_run,
                selected_archives,
                receipt,
                retained_capture_profile=profile,
            )
        assert calls == ([] if change == "unknown-profile" else [tmp_path])
