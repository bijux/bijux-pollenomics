"""Keep historical finite evidence distinct from current source admission."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference import (
    finite_covariance_capture as finite,
)


def test_historical_reader_does_not_run_current_source_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    monkeypatch.setattr(
        finite, "_validated_finite_covariance_capture", lambda root: sentinel
    )

    def forbidden(*args: object) -> None:
        raise AssertionError("Historical authentication must not imply current reuse")

    monkeypatch.setattr(finite, "require_current_finite_covariance_sources", forbidden)
    assert finite.historical_finite_covariance_capture(tmp_path) is sentinel


def test_current_entrypoint_keeps_its_separate_reuse_gate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel = object()
    monkeypatch.setattr(
        finite, "_validated_finite_covariance_capture", lambda root: sentinel
    )
    calls: list[object] = []
    monkeypatch.setattr(
        finite,
        "require_current_finite_covariance_sources",
        lambda root, capture: calls.append(capture),
    )
    assert finite.validated_finite_covariance_capture(tmp_path) is sentinel
    assert calls == [sentinel]


def test_public_source_context_cannot_weaken_private_current_authority(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sealed = {"protected_science_sha256": {"own.py": "1" * 64}}
    raw = json.dumps({"source_context": sealed}).encode()
    private_name = finite.CAPTURE_ROOT + "/capture/capture.json"
    reads: list[str] = []

    def read(name: str) -> bytes:
        reads.append(name)
        assert name == private_name
        return raw

    capture = SimpleNamespace(
        source_context={"protected_science_sha256": {}},
        input_sha256={private_name: hashlib.sha256(raw).hexdigest()},
        read_input=read,
    )
    seen: list[dict[str, Any]] = []
    monkeypatch.setattr(
        finite, "_require_current_sources", lambda root, context: seen.append(context)
    )
    finite.require_current_finite_covariance_sources(
        tmp_path, cast(finite.FiniteCovarianceCapture, capture)
    )
    assert seen == [sealed]
    assert reads == [private_name, private_name]


def test_current_admission_keeps_its_original_input_recheck(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = json.dumps({"source_context": {"protected_science_sha256": {}}}).encode()
    private_name = finite.CAPTURE_ROOT + "/capture/capture.json"
    capture = SimpleNamespace(
        source_context={},
        input_sha256={private_name: "0" * 64},
        read_input=lambda name: record,
    )
    monkeypatch.setattr(finite, "_require_current_sources", lambda *args: None)
    with pytest.raises(ValueError, match="changed during validation"):
        finite.require_current_finite_covariance_sources(
            tmp_path, cast(finite.FiniteCovarianceCapture, capture)
        )
