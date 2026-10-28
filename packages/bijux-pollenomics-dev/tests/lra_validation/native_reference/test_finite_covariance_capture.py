"""Authenticate the admitted native packet in place and inject bounded read failures."""

from __future__ import annotations

from collections.abc import Callable
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import validated_descriptor
from bijux_pollenomics_dev.lra_validation.native_reference import (
    finite_covariance_capture as capture,
)
from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import _file


@pytest.fixture
def repository() -> Path:
    """Use the complete normal clone; neither packet nor package source is copied."""
    return Path(__file__).resolve().parents[5]


def test_admitted_native_source_population(repository: Path) -> None:
    result = capture.validated_finite_covariance_capture(repository)
    assert len(result.raw_sha256) == 138
    assert len(result.report_source_members) == 129
    assert len(result.input_sha256) == 153
    assert len(result.source_context["protected_science_sha256"]) == 68
    driver = capture.CAPTURE_ROOT + "/capture/oracle/oracle.R"
    assert not (repository / driver).exists()
    assert (
        hashlib.sha256(result.read_input(driver)).hexdigest()
        == result.raw_sha256["oracle/oracle.R"]
    )
    with pytest.raises(ValueError, match="Unlisted"):
        result.read_input("unlisted.csv")


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
def test_modified_admitted_member_refuses(
    repository: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original_file = _file
    original_resolver = validated_descriptor
    full = capture.CAPTURE_ROOT + "/" + name

    def changed_file(root: Path, relative: str) -> bytes:
        body = original_file(root, relative)
        return body + b" " if relative == full else body

    class ChangedReader:
        def __init__(self, reader: Any) -> None:
            self.reader = reader

        def read_source(self, relative: str) -> bytes:
            body: bytes = self.reader.read_source(relative)
            return body + b" " if relative == name else body

        def fresh(self) -> None:
            self.reader.fresh()

    def changed_reader(*args: Any, **kwargs: Any) -> ChangedReader:
        return ChangedReader(original_resolver(*args, **kwargs))

    monkeypatch.setattr(capture, "_file", changed_file)
    monkeypatch.setattr(capture, "validated_descriptor", changed_reader)
    with pytest.raises(ValueError):
        capture.validated_finite_covariance_capture(repository)


@pytest.mark.parametrize(
    "name", ["fixed_site_covariance.py", "joint_fixed_site_covariance.py"]
)
def test_changed_covariance_source_refuses(
    repository: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    original: Callable[[Path, str], bytes] = _file
    full = (
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/reconstruction/"
        + name
    )

    def changed(root: Path, relative: str) -> bytes:
        body = original(root, relative)
        return body + b"\n" if relative == full else body

    monkeypatch.setattr(capture, "_file", changed)
    with pytest.raises(ValueError, match="protected source"):
        capture.validated_finite_covariance_capture(repository)


@pytest.fixture
def retained_comparison(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Any, dict[str, Any], list[Path]]:
    """Construct sealed source-map metadata and independently hashed own input files."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )
    from bijux_pollenomics_dev.lra_validation.native_reference.annulus_capture import (
        AnnulusCapture,
    )

    repository = tmp_path / "own-comparison"
    run, archives = repository / "capture", repository / "archives"
    run.mkdir(parents=True)
    archives.mkdir()
    names = [f"captured/source-{index}.py" for index in range(68)]
    sources = {
        name: hashlib.sha256(b"sealed original science\n").hexdigest() for name in names
    }
    receipt = {"current_inputs_sha256": dict(sources)}
    for name in names:
        path = repository / name
        path.parent.mkdir(exist_ok=True)
        path.write_bytes(b"own current science fixture\n")
    (run / "oracle.csv").write_bytes(b"own,value\npoint,0.5\n")
    (run / "receipt.json").write_text(json.dumps(receipt))
    observed_files = [repository / name for name in names] + [
        run / "oracle.csv",
        run / "receipt.json",
    ]
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in observed_files
    }
    sealed = AnnulusCapture(
        run,
        archives,
        "a" * 40,
        "b" * 64,
        (),
        {},
        {},
        {"protected_science_sha256": sources},
    )
    calls: list[Path] = []

    def authenticate(root: Path) -> AnnulusCapture:
        calls.append(root)
        assert root == repository
        if any(
            hashlib.sha256(path.read_bytes()).hexdigest() != digest
            for path, digest in before.items()
        ):
            raise ValueError("Constructed native/source input changed")
        return sealed

    monkeypatch.setattr(comparison, "validated_finite_covariance_capture", authenticate)
    return repository, sealed, receipt, calls


def test_retained_comparison_authenticates_adopted_source_layout(
    retained_comparison: tuple[Path, Any, dict[str, Any], list[Path]],
) -> None:
    """Only an explicitly authenticated retained profile can use its sealed source map."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    repository, sealed, receipt, calls = retained_comparison
    comparison._require_current_inputs(
        repository,
        sealed.directory,
        sealed.source_archives,
        receipt,
        retained_capture_profile="finite-covariance",
    )
    assert calls == [repository]
    assert len(receipt["current_inputs_sha256"]) == 68
    with pytest.raises(ValueError, match="Current R/Python input changed"):
        comparison._require_current_inputs(
            repository, sealed.directory, sealed.source_archives, receipt
        )
    assert calls == [repository]


@pytest.mark.parametrize("route", ["capture", "archives"])
def test_retained_comparison_refuses_other_source_routes(
    retained_comparison: tuple[Path, Any, dict[str, Any], list[Path]],
    route: str,
) -> None:
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    repository, sealed, receipt, _ = retained_comparison
    run = repository / "other-capture" if route == "capture" else sealed.directory
    archives = (
        repository / "other-archives" if route == "archives" else sealed.source_archives
    )
    with pytest.raises(ValueError, match="source routes or sealed source hashes"):
        comparison._require_current_inputs(
            repository,
            run,
            archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )


@pytest.mark.parametrize("change", ["digest", "missing", "extra", "boolean"])
def test_retained_comparison_refuses_unsealed_source_map(
    retained_comparison: tuple[Path, Any, dict[str, Any], list[Path]],
    change: str,
) -> None:
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    repository, sealed, receipt, _ = retained_comparison
    sources = receipt["current_inputs_sha256"]
    if change == "digest":
        sources[next(iter(sources))] = "0" * 64
    elif change == "missing":
        sources.pop(next(iter(sources)))
    elif change == "extra":
        sources["unknown-source.py"] = "0" * 64
    else:
        sources[next(iter(sources))] = False
    with pytest.raises(ValueError, match="source routes or sealed source hashes"):
        comparison._require_current_inputs(
            repository,
            sealed.directory,
            sealed.source_archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )


@pytest.mark.parametrize(
    "name", ["capture/oracle.csv", "capture/receipt.json", "captured/source-0.py"]
)
def test_retained_comparison_reauthenticates_physical_capture_and_science(
    retained_comparison: tuple[Path, Any, dict[str, Any], list[Path]],
    name: str,
) -> None:
    """The consumer must invoke custody again; own file tampering is not rescued."""
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    repository, sealed, receipt, calls = retained_comparison
    comparison._require_current_inputs(
        repository,
        sealed.directory,
        sealed.source_archives,
        receipt,
        retained_capture_profile="finite-covariance",
    )
    path = repository / name
    path.write_bytes(path.read_bytes() + b"changed")
    with pytest.raises(ValueError, match="Constructed native/source input changed"):
        comparison._require_current_inputs(
            repository,
            sealed.directory,
            sealed.source_archives,
            receipt,
            retained_capture_profile="finite-covariance",
        )
    assert calls == [repository, repository]


@pytest.mark.parametrize("profile", ["annulus", "count-domain", "unknown", "", False])
def test_retained_comparison_refuses_unsupported_profile_before_authentication(
    retained_comparison: tuple[Path, Any, dict[str, Any], list[Path]],
    monkeypatch: pytest.MonkeyPatch,
    profile: object,
) -> None:
    from bijux_pollenomics_dev.lra_validation import (
        live_reference_comparison as comparison,
    )

    repository, sealed, receipt, calls = retained_comparison
    with pytest.raises(ValueError, match="profile must be finite-covariance"):
        comparison._require_current_inputs(
            repository,
            sealed.directory,
            sealed.source_archives,
            receipt,
            retained_capture_profile=profile,  # type: ignore[arg-type]
        )
    assert calls == []
