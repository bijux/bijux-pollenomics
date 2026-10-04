"""Keep captured mathematical support separate from physical source admission."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    english_receiver_annulus as subject,
)

ROOT = Path(__file__).resolve().parents[5]


def _capture_case(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    """Copy real mathematical capture/source bytes; no pollen fixture is admitted."""
    capture = ROOT / subject.CAPTURE
    record = json.loads(capture.read_bytes())
    for name in [subject.CAPTURE.as_posix(), *record["kernel_dependency_sha256"]]:
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / name, target)
    falls = sorted({row["fall_speed_m_s"] for row in record["cases"]})
    return tmp_path, {
        "parameters": [{"fallspeed_m_s": fall} for fall in [*falls, *falls[:10]]],
        "rings": [
            {"inner_m": low, "outer_m": high}
            for low, high in [(81, 500), (500, 1000), (1000, 10000)]
        ],
    }


def test_admitted_capture_expands_exact_ring_parameter_support(tmp_path: Path) -> None:
    root, payload = _capture_case(tmp_path)
    kernel, digest = subject._captured_kernel(root, payload)
    assert digest == subject.CAPTURE_SHA256
    assert kernel.shape == (3, 30)
    assert np.all(kernel > 0)
    np.testing.assert_array_equal(kernel[:, :10], kernel[:, 20:])


def test_changed_ring_or_fall_speed_cannot_reuse_capture(tmp_path: Path) -> None:
    root, payload = _capture_case(tmp_path)
    for dimension in ("ring", "fall"):
        changed = copy.deepcopy(payload)
        if dimension == "ring":
            changed["rings"][0]["inner_m"] = 82
        else:
            changed["parameters"][0]["fallspeed_m_s"] = 0.011
        with pytest.raises(ValueError, match="source/ring support"):
            subject._captured_kernel(root, changed)


def test_changed_capture_or_equation_source_refuses(tmp_path: Path) -> None:
    root, payload = _capture_case(tmp_path)
    capture = root / subject.CAPTURE
    original = capture.read_bytes()
    capture.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="capture identity"):
        subject._captured_kernel(root, payload)
    capture.write_bytes(original)
    record = json.loads(original)
    source = root / next(iter(record["kernel_dependency_sha256"]))
    source.write_bytes(source.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="mathematical dependency"):
        subject._captured_kernel(root, payload)
