"""Keep one Linux historical scoring member confined to its original custody."""

from __future__ import annotations

from dataclasses import replace
import os
from pathlib import Path
import subprocess

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    scoring_protocols as subject,
)

from ...source_contracts.test_execution_helper_batches import _identity, _write
from .test_scoring_protocol_custody import (
    _CHALLENGE,
    _CURRENT,
    _OLD,
    _RECEIVER,
    _ROOT,
    _SCORING,
    ScoringCase,
    _case,
)

_LINUX = "data/method-certification/linux-r-source-capture"


def _linux_case(root: Path, monkeypatch: pytest.MonkeyPatch) -> ScoringCase:
    """Use the established inert Git fixture with the fixed Linux logical member."""
    return _case(root, monkeypatch, _LINUX, _CHALLENGE, logical_prefix="source/")


def test_one_linux_scoring_member_preserves_exact_old_source_scope(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Authenticate old Git bytes without a current scoring or native claim."""
    case = _linux_case(tmp_path / "repository", monkeypatch)
    proof = case.admit()
    assert proof["path"] == _CHALLENGE
    assert proof["original_member"] == "source/" + _CHALLENGE
    assert proof["classification"] == "explicit_historical_scoring_arithmetic_profile"
    assert proof["original_sha256"] == _identity(_OLD)["sha256"]
    assert proof["original_bytes"] == len(_OLD)
    assert proof["whole_old_module_reconstructed"] is True
    assert proof["all_other_old_source_bytes_exact"] is True
    assert proof["current_regular_single_link_and_stable"] is True
    assert proof["historical_scoring_profile_explicitly_selected"] is True
    assert proof["old_native_equal_current_scoring_or_math_claimed"] is False
    assert proof["new_quadrature_model_native_or_browser_execution_claimed"] is False
    assert not (case.consumer.repository / _LINUX / case.logical).exists()


@pytest.mark.parametrize(
    "damage",
    (
        "context",
        "capture",
        "logical",
        "repository",
        "path",
        "hash",
        "size",
        "bool_size",
        "extra_field",
        "member_hash",
        "member_size",
        "group_alias",
        "duplicate_group",
        "not_detached",
        "physical_member",
        "old_body",
        "symlink",
        "ancestor_symlink",
        "hardlink",
        "stale",
        "reread_mutation",
        "reread_bytes",
    ),
)
def test_linux_scoring_binding_and_freshness_refuse_after_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Keep exact source coordinates and final current-byte observations mandatory."""
    case = _linux_case(tmp_path / "repository", monkeypatch)
    assert case.admit()["whole_old_module_reconstructed"] is True
    buffer = case.buffer
    if damage == "context":
        buffer.prefix = "data/own-unlisted-context"
    elif damage == "capture":
        buffer.descriptor.capture["sha256"] = "0" * 64
    elif damage == "logical":
        case.logical += "/alias"
    elif damage == "repository":
        buffer.repository = case.consumer.repository.parent
    elif damage == "path":
        case.row["path"] = _ROOT + "source_completion/unlisted.py"
    elif damage == "hash":
        case.row["sha256"] = "0" * 64
    elif damage == "size":
        case.row["bytes"] += 1
    elif damage == "bool_size":
        case.row["bytes"] = True
    elif damage == "extra_field":
        case.row["current"] = True
    elif damage == "member_hash":
        buffer.descriptor.members[case.logical]["sha256"] = "0" * 64
    elif damage == "member_size":
        buffer.descriptor.members[case.logical]["bytes"] += 1
    elif damage == "group_alias":
        buffer.descriptor.groups[0]["resolved_paths"] = [(case.logical, _RECEIVER)]
    elif damage == "duplicate_group":
        buffer.descriptor = replace(
            buffer.descriptor, groups=buffer.descriptor.groups * 2
        )
    elif damage == "not_detached":
        buffer.descriptor = replace(buffer.descriptor, detached=frozenset())
    elif damage == "physical_member":
        _write(case.consumer.repository / _LINUX / case.logical, b"# extra own bytes\n")
    elif damage == "old_body":
        buffer._payloads[case.logical] = _OLD + b"# counterfeit old bytes\n"
    elif damage == "symlink":
        backing = case.consumer.repository / "own-backing"
        case.target.rename(backing)
        case.target.symlink_to(backing)
    elif damage == "ancestor_symlink":
        parent = case.target.parent
        backing = case.consumer.repository / "own-parent"
        parent.rename(backing)
        parent.symlink_to(backing, target_is_directory=True)
    elif damage == "hardlink":
        os.link(case.target, case.consumer.repository / "own-alias")
    elif damage == "stale":
        metadata = case.consumer.repository / _LINUX / "capture.json"
        metadata.write_bytes(metadata.read_bytes() + b"\n")
    elif damage == "reread_mutation":
        original_match = subject.scoring_protocol_extension_matches

        def mutate_after_actual_inverse(
            name: str, captured: bytes, current: bytes
        ) -> bool:
            accepted = original_match(name, captured, current)
            assert accepted
            case.target.write_bytes(_CURRENT + b"# concurrent current edit\n")
            return accepted

        monkeypatch.setattr(
            subject, "scoring_protocol_extension_matches", mutate_after_actual_inverse
        )
    else:
        original_read = Path.read_bytes
        observations = 0

        def changing_final_read(path: Path) -> bytes:
            nonlocal observations
            body = original_read(path)
            if path == case.target:
                observations += 1
                if observations >= 2:
                    return body + b"# changed final byte observation\n"
            return body

        monkeypatch.setattr(Path, "read_bytes", changing_final_read)
    expected = (
        ReportOwnershipError
        if damage in {"symlink", "ancestor_symlink"}
        else ReportRebuildError
    )
    with pytest.raises(expected):
        if damage == "physical_member":
            index.validated_descriptor(
                case.consumer.repository, _LINUX, case.consumer.members
            )
        case.admit()


@pytest.mark.parametrize("name", (_RECEIVER, _SCORING))
def test_other_optimizer_scoring_members_cannot_borrow_linux_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """A valid Linux baseline cannot extend the capture to either other member."""
    baseline = _linux_case(tmp_path / "baseline", monkeypatch)
    assert baseline.admit()["whole_old_module_reconstructed"] is True
    forbidden = _case(
        tmp_path / "forbidden", monkeypatch, _LINUX, name, logical_prefix="source/"
    )
    assert forbidden.buffer.read_source(forbidden.logical) == _OLD
    with pytest.raises(ReportRebuildError, match="source binding differs"):
        forbidden.admit()


def test_actual_linux_source_reconstructs_only_its_fixed_historical_module() -> None:
    """Read actual normal Git source bytes, never import or execute that programme."""
    repository = Path(__file__).resolve().parents[7]
    captured = subprocess.check_output(
        [
            "git",
            "--no-replace-objects",
            "show",
            "794cb962ada617915cc633cb53176cae9a5d90fe:" + _CHALLENGE,
        ],
        cwd=repository,
        timeout=20,
    )
    current = (repository / _CHALLENGE).read_bytes()
    assert len(captured) == 14310
    assert _identity(captured)["sha256"] == (
        "f26f69acc37ff18cbec11109e61fd8970453790f2075d32040471f973e90eaa3"
    )
    assert subject.scoring_protocol_extension_matches(_CHALLENGE, captured, current)
    assert not subject.scoring_protocol_extension_matches(
        _CHALLENGE, captured + b"# foreign old bytes\n", current
    )
    assert not subject.scoring_protocol_extension_matches(
        _CHALLENGE, captured, current + b"# unrelated current code\n"
    )
