"""Keep captured mathematical support separate from physical source admission."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
    validate_blobs,
)
from bijux_pollenomics_dev.ci.report_rebuild.source_paths import safe_source_file
from bijux_pollenomics_dev.source_completion.pollen_reconstruction import (
    english_receiver_annulus as subject,
)

ROOT = Path(__file__).resolve().parents[5]


def _capture_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any], dict[str, Path]]:
    """Invent coefficients and reuse only genuine source identity metadata in place."""
    falls = [0.001 + index / 10000 for index in range(20)]
    rings = [(81, 500), (500, 1000), (1000, 10000)]
    cases = []
    for index, fall in enumerate(falls):
        for ring, (inner, outer) in enumerate(rings):
            factor = (index * 3 + ring + 1) / 1000
            cases.append(
                {
                    "fall_speed_m_s": fall,
                    "inner_m": inner,
                    "outer_m": outer,
                    "factor": factor,
                    "independent_order64": factor,
                    "independent_order128": factor,
                    "estimated_absolute_error_nonrigorous": 0.0,
                    "coarse_fine_abs": 0.0,
                    "adaptive_fine_abs": 0.0,
                    "passes_frozen_1e_minus7": True,
                }
            )
    dependencies = {
        subject._SOURCE_PREFIX
        + "dispersal/kernels.py": "3cc137c3c13d752adaacdc078cbfee33fd8fc1a065ca6662c6f862dd7a097c0d",
        subject._SOURCE_PREFIX
        + "dispersal/receiver_annulus.py": "9aeae845a11540abcddf77dd9f09a418aed8838e52ba516a7eb058efbeff5563",
        subject._SOURCE_PREFIX
        + "models/errors.py": "95977107f59fb7aa118dcbfcee57fd81655d2ae7f540d94e657ef19d1b69737e",
        subject._SOURCE_PREFIX
        + "models/validation.py": "1c7584947d3248b522151045210f2c9056e41ac3732a5c25dd88eabb6c954414",
    }
    record: dict[str, Any] = {
        "fixture_only": "Invented positive coefficients; no native computation or evidence.",
        "schema_version": "qualified-english-receiver-annulus-kernels.v1",
        "source_manifest_sha256": subject.english.MANIFEST_SHA256,
        "prepared_request_sha256": subject.english.REQUEST_SHA256,
        "producer_native_exit": 1,
        "case_count": 60,
        "receiver_radius_m": 80,
        "diffusion_coefficient": 1.0,
        "turbulence_parameter": 1.0,
        "wind_speed_m_s": 1.0,
        "kernel_candidate": "dd0abe1ece5b4d6230b2eaef19cd8cdafce2cc8e",
        "kernel_dependency_sha256": dependencies,
        "cases": cases,
        "case_sha256": {
            json.dumps(
                [row["fall_speed_m_s"], row["inner_m"], row["outer_m"]],
                separators=(",", ":"),
            ): hashlib.sha256(
                json.dumps(
                    row, sort_keys=True, separators=(",", ":"), allow_nan=False
                ).encode()
            ).hexdigest()
            for row in cases
        },
    }
    target = tmp_path / subject.CAPTURE
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(record, sort_keys=True, allow_nan=False) + "\n").encode()
    target.write_bytes(raw)
    monkeypatch.setattr(subject, "CAPTURE_SHA256", hashlib.sha256(raw).hexdigest())
    sources = {name: ROOT / name for name in dependencies}
    original_safe = safe_source_file

    def source_file(repository: Path, name: str, label: str) -> Path:
        if repository == tmp_path and name in sources:
            path = sources[name]
            return original_safe(path.parent, path.name, label)
        return original_safe(repository, name, label)

    def original_sources(repository: Path, members: list[GitSourceMember]) -> None:
        assert repository == tmp_path
        validate_blobs(ROOT, members)

    monkeypatch.setattr(subject, "_safe_file", source_file)
    monkeypatch.setattr(subject, "validate_blobs", original_sources)
    payload = {
        "parameters": [{"fallspeed_m_s": fall} for fall in [*falls, *falls[:10]]],
        "rings": [{"inner_m": low, "outer_m": high} for low, high in rings],
    }
    kernel, digest = subject._captured_kernel(tmp_path, payload)
    assert kernel.shape == (3, 30) and digest == subject.CAPTURE_SHA256
    assert np.all(kernel > 0)
    return tmp_path, payload, sources


def test_admitted_capture_expands_exact_ring_parameter_support(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify admitted capture expands exact ring parameter support."""
    root, payload, _ = _capture_case(tmp_path, monkeypatch)
    kernel, digest = subject._captured_kernel(root, payload)
    assert digest == subject.CAPTURE_SHA256
    assert kernel.shape == (3, 30)
    assert np.all(kernel > 0)
    np.testing.assert_array_equal(kernel[:, :10], kernel[:, 20:])


def test_changed_ring_or_fall_speed_cannot_reuse_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify changed ring or fall speed cannot reuse capture."""
    root, payload, _ = _capture_case(tmp_path, monkeypatch)
    for dimension in ("ring", "fall"):
        changed = copy.deepcopy(payload)
        if dimension == "ring":
            changed["rings"][0]["inner_m"] = 82
        else:
            changed["parameters"][0]["fallspeed_m_s"] = 0.011
        with pytest.raises(ValueError, match="source/ring support"):
            subject._captured_kernel(root, changed)


def test_changed_capture_or_equation_source_refuses(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify changed capture or equation source refuses."""
    root, payload, sources = _capture_case(tmp_path, monkeypatch)
    capture = root / subject.CAPTURE
    original = capture.read_bytes()
    capture.write_bytes(original + b"\n")
    with pytest.raises(ValueError, match="capture identity"):
        subject._captured_kernel(root, payload)
    capture.write_bytes(original)
    record = json.loads(original)
    source = root / "changed-equation.py"
    source.write_bytes(b"changed equation fixture\n")
    sources[next(iter(record["kernel_dependency_sha256"]))] = source
    with pytest.raises(ValueError, match="mathematical dependency"):
        subject._captured_kernel(root, payload)


def test_changed_validator_body_is_not_an_equation_or_scalar_equivalence_claim(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, payload, sources = _capture_case(tmp_path, monkeypatch)
    validation = root / "changed-admission.py"
    validation.write_bytes(b"unrelated scalar admission implementation\n")
    sources[subject._SOURCE_PREFIX + "models/validation.py"] = validation
    kernel, digest = subject._captured_kernel(root, payload)
    assert kernel.shape == (3, 30)
    assert digest == subject.CAPTURE_SHA256
    assert not (root / "packages").exists()


def test_original_equation_git_identity_still_refuses_a_different_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, payload, _ = _capture_case(tmp_path, monkeypatch)
    identities = dict(subject._ORIGINAL_KERNEL_FILES)
    name = next(iter(identities))
    _, size = identities[name]
    identities[name] = ("0" * 40, size)
    monkeypatch.setattr(subject, "_ORIGINAL_KERNEL_FILES", identities)
    with pytest.raises(ValueError, match="original mathematical dependency"):
        subject._captured_kernel(root, payload)


def test_current_equation_symlink_is_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root, payload, sources = _capture_case(tmp_path, monkeypatch)
    name = next(iter(sources))
    alias = root / "linked-equation.py"
    alias.symlink_to(sources[name])
    sources[name] = alias
    with pytest.raises(ReportRebuildError, match="regular file"):
        subject._captured_kernel(root, payload)


@pytest.mark.parametrize(
    "value",
    [True, False, float("nan"), float("inf"), 10**1000, np.ma.masked, "0.01", [0.01]],
    ids=["true", "false", "nan", "infinite", "overflow", "masked", "text", "container"],
)
def test_non_native_or_invalid_scalar_cannot_reuse_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, value: object
) -> None:
    root, payload, _ = _capture_case(tmp_path, monkeypatch)
    payload["parameters"][0]["fallspeed_m_s"] = value
    with pytest.raises(ValueError, match="native numeric|finite number"):
        subject._captured_kernel(root, payload)


def test_current_admission_keeps_every_frozen_native_scalar_exact() -> None:
    """The original validator returned float(value) on these finite native inputs."""
    record = json.loads((ROOT / subject.CAPTURE).read_bytes())
    for row in record["cases"]:
        values = {
            "receiver_radius_m": record["receiver_radius_m"],
            "diffusion_coefficient": record["diffusion_coefficient"],
            "turbulence_parameter": record["turbulence_parameter"],
            "wind_speed_m_s": record["wind_speed_m_s"],
            "fall_speed_m_s": row["fall_speed_m_s"],
            "inner_m": row["inner_m"],
            "outer_m": row["outer_m"],
        }
        for name, value in values.items():
            assert type(value) in {int, float}
            assert (
                subject._native_number(value, name, positive=True).hex()
                == float(value).hex()
            )


def test_canonical_original_capture_preserves_all_ninety_coefficients() -> None:
    """Read original stored coefficients against genuine Git and equation sources."""
    record = json.loads((ROOT / subject.CAPTURE).read_bytes())
    falls = sorted({row["fall_speed_m_s"] for row in record["cases"]})
    parameters = [*falls, *falls[:10]]
    rings = [(81, 500), (500, 1000), (1000, 10000)]
    payload = {
        "parameters": [{"fallspeed_m_s": fall} for fall in parameters],
        "rings": [{"inner_m": inner, "outer_m": outer} for inner, outer in rings],
    }
    kernel, digest = subject._captured_kernel(ROOT, payload)
    lookup = {
        (row["fall_speed_m_s"], row["inner_m"], row["outer_m"]): row["factor"]
        for row in record["cases"]
    }
    np.testing.assert_array_equal(
        kernel,
        np.array(
            [
                [lookup[(fall, inner, outer)] for fall in parameters]
                for inner, outer in rings
            ]
        ),
    )
    assert kernel.size == 90
    assert digest == subject.CAPTURE_SHA256
