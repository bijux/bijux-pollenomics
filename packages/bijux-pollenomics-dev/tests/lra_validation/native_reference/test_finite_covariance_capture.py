"""Refuse changed scientific inputs, physical aliases and incomplete native custody."""

import json
import os
from pathlib import Path
import shutil

import pytest

from bijux_pollenomics_dev.lra_validation.native_reference.finite_covariance_capture import (
    CAPTURE_ROOT,
    validated_finite_covariance_capture,
)


@pytest.fixture
def repository(tmp_path: Path) -> Path:
    """Copy the admitted finite packet and scientific inputs into independently owned files."""
    maintained = Path(__file__).resolve().parents[5]
    root = tmp_path / "repository"
    shutil.copytree(maintained / CAPTURE_ROOT, root / CAPTURE_ROOT)
    record = json.loads((root / CAPTURE_ROOT / "capture/capture.json").read_text())
    names = [
        *record["source_context"]["protected_science_sha256"],
        "docs/report/method-certification/original-r-reference/reference-bundle/certificate.json",
    ]
    from bijux_pollenomics_dev.lra_validation.native_reference import (
        source_layout_adoption as layout,
    )

    for name in names:
        current = layout.RELOCATIONS.get(name, name)
        target = root / current
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(maintained / current, target)
    extra = [
        layout.PROOF_PATH,
        layout.PREIMAGE_PATH,
        *layout.RELOCATIONS.values(),
        "configs/ci/report-capture-projections/atlas-source-view-api.json",
        "configs/ci/report-capture-projections/atlas-source-view-root-api.json",
        "data/atlas/source-view-capture/source/" + layout.API_PATH,
        "data/atlas/source-view-capture/source/" + layout.ROOT_API_PATH,
    ]
    for name in extra:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(maintained / name, target)
    return root


def test_admitted_native_source_population(repository: Path) -> None:
    capture = validated_finite_covariance_capture(repository)
    assert len(capture.raw_sha256) == 138
    assert len(capture.report_source_members) == 129
    assert len(capture.input_sha256) == 153
    assert len(capture.source_context["protected_science_sha256"]) == 68


@pytest.mark.parametrize(
    "name",
    [
        "capture/oracle/C0000.csv",
        "capture/receipt.json",
        "capture/capture.json",
        "execution-evidence/plan.json",
        "execution-evidence/terminal.json",
        "execution-evidence/independent-terminal-review.json",
        "source-archives/GenSA_1.1.15.tar.gz",
    ],
)
def test_modified_admitted_member_refuses(repository: Path, name: str) -> None:
    target = repository / CAPTURE_ROOT / name
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ValueError):
        validated_finite_covariance_capture(repository)


@pytest.mark.parametrize(
    "name", ["fixed_site_covariance.py", "joint_fixed_site_covariance.py"]
)
def test_changed_covariance_source_refuses(repository: Path, name: str) -> None:
    target = (
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction"
        / name
    )
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError, match="protected source"):
        validated_finite_covariance_capture(repository)


def test_undeclared_physical_member_refuses(repository: Path) -> None:
    (repository / CAPTURE_ROOT / "capture/undeclared.csv").write_text("0,0\n")
    with pytest.raises(ValueError, match="extra/missing"):
        validated_finite_covariance_capture(repository)


@pytest.mark.parametrize("alias", ["symlink", "hardlink"])
def test_member_file_alias_refuses(repository: Path, alias: str) -> None:
    target = repository / CAPTURE_ROOT / "capture/oracle/C0000.csv"
    backing = repository / "backing.csv"
    target.rename(backing)
    if alias == "symlink":
        target.symlink_to(backing)
    else:
        os.link(backing, target)
    with pytest.raises(ValueError):
        validated_finite_covariance_capture(repository)


def test_retained_comparison_authenticates_adopted_source_layout(
    repository: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Use the real finite packet and all 68 sealed sources after named custody."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    capture = validated_finite_covariance_capture(repository)
    receipt = json.loads((capture.directory / "receipt.json").read_text())
    calls: list[Path] = []

    def authenticate(root: Path) -> object:
        calls.append(root)
        return validated_finite_covariance_capture(root)

    monkeypatch.setattr(comparison, "validated_finite_covariance_capture", authenticate)
    comparison._require_current_inputs(
        repository,
        capture.directory,
        capture.source_archives,
        receipt,
        retained_capture_profile="finite-covariance",
    )
    assert calls == [repository]
    assert len(receipt["current_inputs_sha256"]) == 68
    assert not (
        repository
        / "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/joint_site_draws.py"
    ).exists()
    with pytest.raises(ValueError, match="Current R/Python input changed"):
        comparison._require_current_inputs(
            repository, capture.directory, capture.source_archives, receipt
        )
    assert calls == [repository]


@pytest.mark.parametrize("route", ["capture", "archives"])
def test_retained_comparison_refuses_other_source_routes(
    repository: Path, route: str
) -> None:
    """An authenticated packet cannot authorize another native or archive route."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    capture = validated_finite_covariance_capture(repository)
    receipt = json.loads((capture.directory / "receipt.json").read_text())
    run = repository / "other-capture" if route == "capture" else capture.directory
    archives = (
        repository / "other-archives"
        if route == "archives"
        else capture.source_archives
    )
    with pytest.raises(ValueError, match="source routes or sealed source hashes"):
        comparison._require_current_inputs(
            repository,
            run,
            archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )


@pytest.mark.parametrize("change", ["digest", "missing", "extra"])
def test_retained_comparison_refuses_unsealed_source_map(
    repository: Path, change: str
) -> None:
    """All 68 receipt hashes must equal the sealed capture context exactly."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    capture = validated_finite_covariance_capture(repository)
    receipt = json.loads((capture.directory / "receipt.json").read_text())
    sources = receipt["current_inputs_sha256"]
    if change == "digest":
        sources[next(iter(sources))] = "0" * 64
    elif change == "missing":
        sources.pop(next(iter(sources)))
    else:
        sources["unknown-source.py"] = "0" * 64
    with pytest.raises(ValueError, match="source routes or sealed source hashes"):
        comparison._require_current_inputs(
            repository,
            capture.directory,
            capture.source_archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )


@pytest.mark.parametrize(
    "name",
    [
        "data/method-certification/native-r-finite-covariance/capture/oracle/C0000.csv",
        "data/method-certification/native-r-finite-covariance/capture/receipt.json",
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/fixed_site_covariance.py",
    ],
)
def test_retained_comparison_reauthenticates_physical_capture_and_science(
    repository: Path, name: str
) -> None:
    """The source-adoption route must preserve native-byte and scientific tamper refusal."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    capture = validated_finite_covariance_capture(repository)
    receipt = json.loads((capture.directory / "receipt.json").read_text())
    target = repository / name
    target.write_bytes(target.read_bytes() + b"\n")
    with pytest.raises(ValueError):
        comparison._require_current_inputs(
            repository,
            capture.directory,
            capture.source_archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )


@pytest.mark.parametrize("profile", ["annulus", "count-domain", "unknown", "", False])
def test_retained_comparison_refuses_unsupported_profile_before_authentication(
    repository: Path, monkeypatch: pytest.MonkeyPatch, profile: object
) -> None:
    """Only the explicit finite-covariance selector can use governed source custody."""
    from typing import Any, cast

    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    def forbidden(_: Path) -> None:
        pytest.fail("unknown profiles must refuse before capture authentication")

    monkeypatch.setattr(comparison, "validated_finite_covariance_capture", forbidden)
    with pytest.raises(ValueError, match="profile must be finite-covariance"):
        comparison._require_current_inputs(
            repository,
            repository / "capture",
            repository / "archives",
            {"current_inputs_sha256": {}},
            retained_capture_profile=cast(Any, profile),
        )
