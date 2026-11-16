"""Only a live session bound to the exact operation and resolvers is authority."""

from contextlib import nullcontext
from dataclasses import replace
from pathlib import Path
import shutil
from typing import Any

import pytest

from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import (
    _check_session,
    _LinkedEvidenceSession,
)

from .native_products import observe_work, session_arguments


def inputs(arguments: dict[str, Any]) -> dict[str, Any]:
    """Build the exact replay-bound session identity."""
    owner = arguments["source_owner"]
    return {
        "operation": arguments["operation"],
        "evidence": owner.evidence,
        "source_facets": owner.source_facets,
        "scope_inputs": arguments["scope_inputs"],
        "legacy_rosters": arguments["legacy_rosters"],
    }


@pytest.mark.parametrize("token", [True, {}, object()])
def test_caller_values_are_not_session_authority(token: Any) -> None:
    with pytest.raises(ValueError, match="source-owned"):
        _check_session(token)


def test_inactive_cross_operation_and_closed_sessions_refuse(
    session_products: dict[str, Any], monkeypatch: Any
) -> None:
    arguments = session_arguments(session_products)
    session = _LinkedEvidenceSession(**arguments)
    work = observe_work(monkeypatch)
    with pytest.raises(ValueError, match="inactive"):
        session.check(**inputs(arguments))
    with session:
        with pytest.raises(ValueError, match="another operation"):
            session.check(**{**inputs(arguments), "operation": object()})
        session.check(**inputs(arguments))
    with pytest.raises(ValueError, match="inactive"):
        session.check(**inputs(arguments))
    with pytest.raises(ValueError, match="reused"):
        session.__enter__()
    assert work["native_detail_opens"] == 0


@pytest.mark.parametrize("resolver", ["evidence", "facet", "scope"])
def test_equal_pin_different_physical_resolver_refuses(
    session_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, resolver: str
) -> None:
    arguments = session_arguments(session_products)
    supplied = inputs(arguments)
    owner = arguments["source_owner"]
    work = observe_work(monkeypatch)
    with _LinkedEvidenceSession(**arguments) as session:
        if resolver == "evidence":
            copied = tmp_path / "copied-evidence"
            shutil.copytree(owner.evidence.directory, copied)
            supplied["evidence"] = replace(owner.evidence, directory=copied)
        elif resolver == "facet":
            pin, path = next(iter(owner.source_facets.items()))
            copied = tmp_path / "copied-facet"
            shutil.copytree(path, copied)
            supplied["source_facets"] = {**owner.source_facets, pin: copied}
        else:
            pin, scope = next(iter(arguments["scope_inputs"].items()))
            copied = tmp_path / "copied-roster.json"
            copied.write_bytes(scope.roster_path.read_bytes())
            supplied["scope_inputs"] = {pin: replace(scope, roster_path=copied)}
        with pytest.raises(ValueError, match="identity|exact source"):
            session.check(**supplied)
    assert work["native_detail_opens"] == 0


def test_index_mutation_does_not_change_cached_authority(
    session_products: dict[str, Any],
) -> None:
    arguments = session_arguments(session_products)
    with _LinkedEvidenceSession(**arguments) as session:
        first = session.index(**inputs(arguments))
        first["targets"].clear()
        assert session.index(**inputs(arguments))["targets"]


def test_real_ancestry_file_profile_boundary(
    session_products: dict[str, Any], tmp_path: Path
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.authority import (
        MAX_SOURCE_FILES,
    )

    assert MAX_SOURCE_FILES == 32768
    root = tmp_path / "finite-source-members"
    root.mkdir()
    for index in range(40960):
        (root / str(index)).touch()
    arguments = session_arguments(session_products)
    session = _LinkedEvidenceSession(**arguments)
    try:
        tree = session._seal(root)
        assert len(tree.files) == 40960
    finally:
        session._close()
    (root / "overflow").touch()
    session = _LinkedEvidenceSession(**arguments)
    try:
        with pytest.raises(ValueError):
            session._seal(root)
    finally:
        session._close()


def test_cold_session_constructor_has_no_ancestry_import_cycle(
    session_products: dict[str, Any],
) -> None:
    import subprocess
    import sys

    script = """
from pathlib import Path
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.session import _LinkedEvidenceSession
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts import session as session_owner
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.evidence_parts.ownership import _LinkedEvidenceSources
import sys
assert Path(session_owner.__file__).parent == Path(sys.argv[1])
from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources.models import NeotomaLinkedEvidence
owner = _LinkedEvidenceSources(NeotomaLinkedEvidence(Path('.'), 'a' * 64), {}, {}, Path('.'), 'b' * 64, Path('.'), 'c' * 64)
assert _LinkedEvidenceSession(source_owner=owner, scope_inputs={}, legacy_rosters={}, operation=object(), _max_source_files=40960)._max_source_files == 40960
"""
    from inspect import getfile

    subprocess.run(
        [
            sys.executable,
            "-B",
            "-c",
            script,
            str(Path(getfile(_LinkedEvidenceSession)).parent),
        ],
        check=True,
        capture_output=True,
    )


@pytest.mark.parametrize("resolver", ["declared", "copied", "unanchored"])
def test_replay_binds_capture_to_exact_session_resolver(
    session_products: dict[str, Any], tmp_path: Path, monkeypatch: Any, resolver: str
) -> None:
    from bijux_pollenomics.collection.sources.neotoma.capture.linked_resources import (
        replay,
    )

    arguments = session_arguments(session_products)
    owner = arguments["source_owner"]
    pin, directory = next(
        (pin, path)
        for pin, path in owner.capture_sources.items()
        if path.name == "first-details"
    )
    if resolver == "copied":
        directory = shutil.copytree(directory, tmp_path / "copied-capture")
    expected = pin if resolver != "unanchored" else None
    work = observe_work(monkeypatch)
    with _LinkedEvidenceSession(**arguments) as session:
        refusal = (
            nullcontext()
            if resolver == "declared"
            else pytest.raises(ValueError, match="capture resolver")
        )
        with refusal:
            replay._replay_linked_resources(
                directory,
                expected_manifest_sha256=expected,
                source_facets=owner.source_facets,
                evidence=owner.evidence,
                scope_inputs=arguments["scope_inputs"],
                legacy_rosters=arguments["legacy_rosters"],
                _session=session,
                _operation=arguments["operation"],
            )
    assert work["native_detail_opens"] == int(resolver == "declared")
