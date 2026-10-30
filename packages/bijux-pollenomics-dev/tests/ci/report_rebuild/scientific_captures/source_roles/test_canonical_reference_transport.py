"""Canonical reader IO keeps fixed old bindings and every unrelated source byte."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as router,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    native_reference_transport as source,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    reference_vector_precision as precision,
)

_CANONICAL_PATHS = (
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/certification.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/evidence.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/native_parity.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/profiles.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/lra_reference/release_gate.py",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/live_reference_comparison.py",
    "packages/bijux-pollenomics-lra/tests/reference/lra_oracle/run_source_domains.py",
)
_LAYERED_PATHS = (_CANONICAL_PATHS[1], _CANONICAL_PATHS[3])
_OLD = b"""# Own non-executed source bytes.
def evaluate(value=17):
    if value < 0:
        raise ValueError("negative")
    return value * 2
source = physical()
bound_scope = "retained"
"""
_PREVIOUS = _OLD.replace(b"source = physical()", b"source = authenticated()")
_CURRENT = _PREVIOUS.replace(
    b"source = authenticated()", b"source = canonical()"
).replace(b'bound_scope = "retained"', b'bound_scope = "canonical"')


def _own_case(
    root: Path, monkeypatch: pytest.MonkeyPatch, name: str, prefix: str
) -> tuple[dict[str, Any], str, Any, Path]:
    """Bind only invented bytes to a real fixed path and capture coordinate."""
    root.mkdir()
    identity = {"bytes": len(_OLD), "sha256": hashlib.sha256(_OLD).hexdigest()}
    if name in _LAYERED_PATHS:
        initial: tuple[tuple[bytes, bytes], ...] = (
            (b"source = physical()", b"source = authenticated()"),
        )
        layers = {
            name: (
                (b"source = authenticated()", b"source = canonical()"),
                (b'bound_scope = "retained"', b'bound_scope = "canonical"'),
            )
        }
    else:
        initial = (
            (b"source = physical()", b"source = canonical()"),
            (b'bound_scope = "retained"', b'bound_scope = "canonical"'),
        )
        layers = {}
    monkeypatch.setattr(
        source,
        "_NATIVE_REFERENCE_TRANSPORT_CONTRACTS",
        {name: (len(_OLD), identity["sha256"], initial)},
    )
    monkeypatch.setattr(source, "_CANONICAL_REFERENCE_IO_SPANS", layers)
    capture_sha, logical_prefix = source._NATIVE_REFERENCE_TRANSPORT_CAPTURES[prefix]
    logical = logical_prefix + name
    capsule = SimpleNamespace(
        repository=root,
        prefix=prefix,
        descriptor=SimpleNamespace(
            capture={"sha256": capture_sha},
            members={logical: dict(identity)},
            groups=[{"resolved_paths": [(logical, name)]}],
        ),
        detached=frozenset({logical}),
        read_source=lambda _: _OLD,
        fresh=lambda: None,
    )
    target = root / name
    target.parent.mkdir(parents=True)
    target.write_bytes(_CURRENT)
    return {"path": name, **identity}, logical, capsule, target


@pytest.mark.parametrize("name", _CANONICAL_PATHS)
@pytest.mark.parametrize("prefix", tuple(source._NATIVE_REFERENCE_TRANSPORT_CAPTURES))
def test_canonical_source_roles_use_the_existing_bounded_dispatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, prefix: str
) -> None:
    row, logical, capsule, _ = _own_case(
        tmp_path / "repository", monkeypatch, name, prefix
    )
    # Isolate the existing IO branch; parser dispatch is qualified below.
    monkeypatch.setattr(router, "REFERENCE_VECTOR_PRECISION_SOURCES", frozenset())
    role = router.validated_current_scientific_source(
        capsule.repository, row, logical, capsule
    )
    assert role is not None
    assert role["classification"] == "finite_native_reference_transport_extension"
    assert role["whole_old_module_reconstructed"] is True
    assert role["historical_native_execution_equal_current_claimed"] is False
    assert role["historical_outputs_regenerated"] is False


@pytest.mark.parametrize("name", _CANONICAL_PATHS)
@pytest.mark.parametrize(
    "damage",
    [
        "capture",
        "logical",
        "detached",
        "member",
        "mapping",
        "old_body",
        "math",
        "unknown_source",
        "symlink",
        "hardlink",
        "stale",
        "concurrent",
    ],
)
def test_canonical_reader_binding_and_freshness_refuse_before_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, damage: str
) -> None:
    prefix = "data/method-certification/linux-r-source-capture"
    row, logical, capsule, target = _own_case(
        tmp_path / "repository", monkeypatch, name, prefix
    )
    repository = capsule.repository
    assert (
        source.validated_native_reference_transport_source(
            repository, row, logical, capsule
        )["whole_old_module_reconstructed"]
        is True
    )
    if damage == "capture":
        capsule.descriptor.capture["sha256"] = "0" * 64
    elif damage == "logical":
        logical += "/foreign"
    elif damage == "detached":
        capsule.detached = frozenset()
    elif damage == "member":
        capsule.descriptor.members[logical] = {"bytes": 0, "sha256": "0" * 64}
    elif damage == "mapping":
        capsule.descriptor.groups *= 2
    elif damage == "old_body":
        capsule.read_source = lambda _: _OLD + b"# altered historical bytes\n"
    elif damage == "math":
        target.write_bytes(_CURRENT.replace(b"return value * 2", b"return value * 3"))
    elif damage == "unknown_source":
        row["path"] = "packages/own/unclassified.py"
    elif damage == "symlink":
        backing = repository / "own_backing.py"
        target.rename(backing)
        target.symlink_to(backing)
    elif damage == "hardlink":
        os.link(target, repository / "own_alias.py")
    elif damage == "stale":

        def stale() -> None:
            raise ReportRebuildError("Own capture changed")

        capsule.fresh = stale
    else:
        calls = 0

        def changing() -> None:
            nonlocal calls
            calls += 1
            if calls == 2:
                target.write_bytes(_CURRENT + b"# concurrent change\n")

        capsule.fresh = changing
    expected = ReportOwnershipError if damage == "symlink" else ReportRebuildError
    with pytest.raises(expected):
        source.validated_native_reference_transport_source(
            repository, row, logical, capsule
        )


@pytest.mark.parametrize("name", _LAYERED_PATHS)
@pytest.mark.parametrize("current", [_PREVIOUS, _CURRENT])
def test_both_reviewed_io_layers_reconstruct_the_same_old_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, current: bytes
) -> None:
    prefix = "data/method-certification/author-optimizer-diagnostic-source-capture"
    _own_case(tmp_path / "repository", monkeypatch, name, prefix)
    assert source.native_reference_transport_extension_matches(name, _OLD, current)


@pytest.mark.parametrize("name", _LAYERED_PATHS)
@pytest.mark.parametrize(
    "damage",
    [
        "default",
        "predicate",
        "math",
        "comment",
        "import",
        "statement",
        "getter",
        "partial_layer",
    ],
)
def test_io_normalization_preserves_all_other_old_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str, damage: str
) -> None:
    prefix = "data/method-certification/author-optimizer-diagnostic-source-capture"
    _own_case(tmp_path / "repository", monkeypatch, name, prefix)
    assert source.native_reference_transport_extension_matches(name, _OLD, _CURRENT)
    if damage == "default":
        current = _CURRENT.replace(b"value=17", b"value=18")
    elif damage == "predicate":
        current = _CURRENT.replace(b"value < 0", b"value <= 0")
    elif damage == "math":
        current = _CURRENT.replace(b"value * 2", b"value * 3")
    elif damage == "comment":
        current = _CURRENT.replace(b"Own non-executed", b"Different non-executed")
    elif damage == "import":
        current = b"import unexpected\n" + _CURRENT
    elif damage == "statement":
        current = _CURRENT + b"unexpected_action()\n"
    elif damage == "getter":
        current = _CURRENT.replace(b"canonical()", b"unbound()")
    else:
        current = _CURRENT.replace(
            b'bound_scope = "canonical"', b'bound_scope = "retained"'
        )
    assert not source.native_reference_transport_extension_matches(name, _OLD, current)


def test_canonical_io_does_not_create_an_unlisted_source_namespace() -> None:
    assert not source.native_reference_transport_extension_matches(
        "packages/own/unlisted.py", _OLD, _CURRENT
    )


@pytest.mark.parametrize("prefix", tuple(source._NATIVE_REFERENCE_TRANSPORT_CAPTURES))
def test_live_reference_parser_dispatch_retains_its_separate_precision_role(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    """Keep the new parser priority distinct from the existing IO-only branch."""
    name = _CANONICAL_PATHS[5]
    row, logical, capsule, _ = _own_case(
        tmp_path / "repository", monkeypatch, name, prefix
    )
    monkeypatch.setattr(
        precision,
        "_REFERENCE_VECTOR_IDENTITIES",
        {name: (len(_OLD), hashlib.sha256(_OLD).hexdigest())},
    )
    monkeypatch.setattr(
        precision,
        "_REFERENCE_VECTOR_SPANS",
        {
            name: (
                (b"source = physical()", b"source = canonical()"),
                (b'bound_scope = "retained"', b'bound_scope = "canonical"'),
            )
        },
    )
    role = router.validated_current_scientific_source(
        capsule.repository, row, logical, capsule
    )
    assert role is not None
    assert role["classification"] == "finite_reference_vector_precision_extension"
    assert role["whole_old_module_reconstructed"] is True
    assert role["current_numeric_parser_changes_binary64_coordinates"] is True
    assert role["historical_native_outputs_equal_current_claimed"] is False
    assert role["historical_outputs_regenerated"] is False
