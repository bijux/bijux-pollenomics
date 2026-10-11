"""Regular member custody and installed/source closure mutation checks."""

from dataclasses import dataclass
import hashlib
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from bijux_pollenomics_dev.lra_validation.retained_reference import identity, sources
from bijux_pollenomics_dev.lra_validation.retained_reference.comparison import (
    read_vector,
)


@dataclass
class _InstalledModule:
    """Expose the synthetic installed origin while retaining a mutable path."""

    __file__: str


def member_identity(name: str, payload: bytes) -> dict[str, object]:
    """Identify independent synthetic bytes without altering the maintained profile."""
    return {
        "files": {
            name: {
                "sha256": hashlib.sha256(payload).hexdigest(),
                "byte_count": len(payload),
            }
        }
    }


def test_maintained_profile_is_distinct_and_complete() -> None:
    """Maintained profile is distinct and complete."""
    profile = identity.load_profile()
    assert len(profile["files"]) == 143
    assert (
        profile["certificate_sha256"]
        == "9560a9eb36259a4f665f61ba18de108193eb1d4e864f751640a392737501410e"
    )
    assert len([name for name in profile["files"] if name.startswith("oracle/C")]) == 43
    assert len([name for name in profile["files"] if name.endswith("-R.csv")]) == 23


def test_unqualified_bundle_refuses_before_vectors(tmp_path: Path) -> None:
    """Unqualified bundle refuses before vectors."""
    (tmp_path / "certificate.json").write_text("{}")
    with pytest.raises(ValueError, match="population or bytes changed"):
        identity.authenticate_bundle(tmp_path)


def test_member_substitution_and_symlink_refused(tmp_path: Path) -> None:
    """Member substitution and symlink refused."""
    name = "values.csv"
    payload = b"kind,value\nnumeric,1\n"
    path = tmp_path / name
    path.write_bytes(payload)
    bound = member_identity(name, payload)
    assert identity.read_member(tmp_path, name, bound) == payload
    path.write_bytes(payload.replace(b",1", b",2"))
    with pytest.raises(ValueError, match="bytes changed"):
        identity.read_member(tmp_path, name, bound)
    path.unlink()
    other = tmp_path / "other.csv"
    other.write_bytes(payload)
    path.symlink_to(other)
    with pytest.raises(ValueError, match="confined and regular"):
        identity.read_member(tmp_path, name, bound)


def test_member_cannot_escape_even_with_matching_payload(tmp_path: Path) -> None:
    """Member cannot escape even with matching payload."""
    bundle = tmp_path / "bundle"
    bundle.mkdir()
    payload = b"private"
    (tmp_path / "outside").write_bytes(payload)
    with pytest.raises(ValueError, match="confined and regular"):
        identity.read_member(
            bundle, "../outside", member_identity("../outside", payload)
        )


def test_numeric_vector_csv_preserves_nonfinite_positions(tmp_path: Path) -> None:
    """Numeric vector csv preserves nonfinite positions."""
    payload = (
        b"kind,value\nnumeric,1\nnumeric,NaN\nnumeric,Inf\nnumeric,-Inf\nnumeric,NA\n"
    )
    (tmp_path / "values.csv").write_bytes(payload)
    values = read_vector(
        tmp_path, "values.csv", member_identity("values.csv", payload), numeric=True
    )
    np.testing.assert_equal(values, np.array([1.0, np.nan, np.inf, -np.inf, np.nan]))


@pytest.mark.parametrize(
    "payload",
    [
        b"kind,value\ncharacter,1\n",
        b"kind,value,other\nnumeric,1,x\n",
        b"kind,value\nnumeric,malformed\n",
    ],
)
def test_numeric_vector_wrong_kind_or_schema_refused(
    tmp_path: Path, payload: bytes
) -> None:
    """Numeric vector wrong kind or schema refused."""
    (tmp_path / "values.csv").write_bytes(payload)
    with pytest.raises(ValueError):
        read_vector(
            tmp_path, "values.csv", member_identity("values.csv", payload), numeric=True
        )


def installed_fixture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, Path, Path, Path, Path, _InstalledModule]:
    """Separate a candidate repository from physical installed source bytes."""
    repository = tmp_path / "repository"
    repository.mkdir()
    environment = tmp_path / "environment"
    environment.mkdir()
    relative = Path(
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/retained_reference"
    )
    canonical = repository / relative
    canonical.mkdir(parents=True)
    installed = (
        environment
        / "lib/python/site-packages/bijux_pollenomics_dev/lra_validation/retained_reference"
    )
    installed.mkdir(parents=True)
    for root in (canonical, installed):
        (root / "sources.py").write_text("owned = 1\n")
        (root / "reference_profile.json").write_text("{}\n")
    math_relative = Path(
        "packages/bijux-pollenomics-lra/src/bijux_pollenomics_lra/arithmetic.py"
    )
    math_source = repository / math_relative
    math_source.parent.mkdir(parents=True)
    math_source.write_text("value = 1\n")
    math_installed = (
        environment / "lib/python/site-packages/bijux_pollenomics_lra/arithmetic.py"
    )
    math_installed.parent.mkdir(parents=True)
    math_installed.write_bytes(math_source.read_bytes())
    for resource_root in (math_source.parent, math_installed.parent):
        (resource_root / "__init__.py").write_text('"""Synthetic LRA namespace."""\n')
        (resource_root / "models.npz").write_bytes(b"independent-resource-bytes")
    monkeypatch.setattr(
        sources,
        "util",
        SimpleNamespace(
            find_spec=lambda name: SimpleNamespace(
                origin=str(math_installed.parent / "__init__.py")
            )
        ),
    )
    module = _InstalledModule(__file__=str(math_installed))
    monkeypatch.setattr(sources, "__file__", str(installed / "sources.py"))
    monkeypatch.setattr(
        sources,
        "sys",
        SimpleNamespace(
            prefix=str(environment),
            modules={"bijux_pollenomics_lra.arithmetic": module},
        ),
    )
    monkeypatch.setattr(
        sources,
        "_replay_source_hashes",
        lambda repo: {
            math_relative.as_posix(): hashlib.sha256(
                math_source.read_bytes()
            ).hexdigest(),
            math_relative.with_name("models.npz").as_posix(): hashlib.sha256(
                (math_source.parent / "models.npz").read_bytes()
            ).hexdigest(),
        },
    )
    return repository, canonical, installed, math_source, math_installed, module


def test_installed_origins_bound_separately_and_byte_drift_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Installed origins bound separately and byte drift refused."""
    repository, _, _, _, math_installed, _ = installed_fixture(tmp_path, monkeypatch)
    captured = sources.capture_sources(repository)
    assert len(captured["canonical_replay_inputs_sha256"]) == 2
    assert len(captured["consumer_inputs_sha256"]) == 4
    assert str(math_installed) in captured["physical_origins"].values()
    assert sources.require_unchanged_sources(repository, captured) == captured
    math_installed.write_text("value = 2\n")
    with pytest.raises(ValueError, match="installed first-party bytes differ"):
        sources.require_unchanged_sources(repository, captured)


def test_original_source_closure_mutation_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Original source closure mutation refused."""
    repository, _, _, math_source, math_installed, _ = installed_fixture(
        tmp_path, monkeypatch
    )
    captured = sources.capture_sources(repository)
    math_source.write_text("value = 2\n")
    math_installed.write_bytes(math_source.read_bytes())
    with pytest.raises(ValueError, match="canonical calculation source changed"):
        sources.require_unchanged_sources(repository, captured)


def test_consumer_descriptor_mutation_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Consumer descriptor mutation refused."""
    repository, canonical, installed, _, _, _ = installed_fixture(tmp_path, monkeypatch)
    captured = sources.capture_sources(repository)
    for root in (canonical, installed):
        (root / "reference_profile.json").write_text('{"changed": true}\n')
    with pytest.raises(ValueError, match="consumer source changed"):
        sources.require_unchanged_sources(repository, captured)


def test_editable_or_symlinked_physical_import_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Editable or symlinked physical import refused."""
    repository, _, _, math_source, math_installed, module = installed_fixture(
        tmp_path, monkeypatch
    )
    module.__file__ = str(math_source)
    with pytest.raises(ValueError, match="escaped installed source"):
        sources.capture_sources(repository)
    alias = math_installed.with_name("alias.py")
    alias.symlink_to(math_installed)
    module.__file__ = str(alias)
    with pytest.raises(ValueError, match="not regular"):
        sources.capture_sources(repository)


def test_installed_resource_mutation_refused_before_calculation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Installed resource mutation refused before calculation."""
    repository, _, _, _, math_installed, _ = installed_fixture(tmp_path, monkeypatch)
    captured = sources.capture_sources(repository)
    (math_installed.parent / "models.npz").write_bytes(b"substituted-resource-bytes")
    with pytest.raises(ValueError, match="resource bytes differ"):
        sources.require_unchanged_sources(repository, captured)


def test_installed_resource_population_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Installed resource population refused."""
    repository, _, _, _, math_installed, _ = installed_fixture(tmp_path, monkeypatch)
    (math_installed.parent / "extra.json").write_text("{}")
    with pytest.raises(ValueError, match="resource member population differs"):
        sources.capture_sources(repository)


def test_installed_resource_symlink_refused(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Installed resource symlink refused."""
    repository, _, _, math_source, math_installed, _ = installed_fixture(
        tmp_path, monkeypatch
    )
    asset = math_installed.parent / "models.npz"
    asset.unlink()
    asset.symlink_to(math_source.parent / "models.npz")
    with pytest.raises(ValueError, match="not regular"):
        sources.capture_sources(repository)
