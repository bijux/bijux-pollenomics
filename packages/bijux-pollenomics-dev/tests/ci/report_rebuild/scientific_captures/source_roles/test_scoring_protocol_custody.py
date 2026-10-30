"""Bind inert scoring pairs through genuine Git and stable current file custody."""

from __future__ import annotations

from dataclasses import dataclass, replace
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    scoring_protocols as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

_ROOT = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/"
_CHALLENGE = _ROOT + "lra_validation/site_leakage_challenge.py"
_RECEIVER = (
    _ROOT + "source_completion/pollen_reconstruction/english_receiver_annulus.py"
)
_SCORING = _ROOT + "source_completion/lilla_gloppsjon_direct_pollen_scoring.py"
_NAMES = (_CHALLENGE, _RECEIVER, _SCORING)
_OPTIMIZER = "data/method-certification/author-optimizer-diagnostic-source-capture"
_OLD = b"# Own inert scoring source; never imported.\n# prior scoring protocol\n"
_PAIRS = ((b"# prior scoring protocol", b"# explicit scoring protocol"),)
_CURRENT = _OLD.replace(*_PAIRS[0])


@dataclass
class ScoringCase:
    """Own inert bytes and actual descriptor state for one fixed scoring coordinate."""

    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        """Use the maintained wrapper without replacing its Git reader."""
        return subject.validated_scoring_protocol_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def _case(
    root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str, name: str
) -> ScoringCase:
    """Commit one invented comment body and bind it through the existing parser."""
    root.mkdir()
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    target = root / name
    _write(target, _OLD)
    _git(root, "add", "--", name)
    _git(
        root,
        "-c",
        "user.name=Bijux fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--no-gpg-sign",
        "-m",
        "test(scoring): bind inert scoring comments",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + name).decode().strip()
    logical = "executions/optimizer-diagnostics/first-party-inputs/" + name
    identity = _identity(_OLD)
    members = {logical: identity}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    mapping = json.dumps([[name, blob]], separators=(",", ":")).encode()
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": "capture.json", **_identity(capture)},
        "historical_native_epochs": [revision],
        "source_revision_correspondence": [
            {"historical_source_commit": revision, "source_revision": revision}
        ],
        "git_groups": [
            {
                "historical_source_commit": revision,
                "source_revision": revision,
                "member_count": 1,
                "git_entries_sha256": hashlib.sha256(mapping).hexdigest(),
                "paths": [[logical, name]],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "scoring",
        root,
        prefix,
        members,
        frozenset({logical}),
        {logical: _OLD},
        descriptor,
        [],
    )
    consumer.repin(monkeypatch)
    monkeypatch.setattr(
        subject,
        "_SCORING_PROTOCOL_CONTRACTS",
        {path: (len(_OLD), identity["sha256"], _PAIRS) for path in _NAMES},
    )
    monkeypatch.setattr(
        subject, "_OPTIMIZER_CAPTURE_SHA256", _identity(capture)["sha256"]
    )
    buffer = index.validated_descriptor(root, prefix, members)
    assert buffer.read_source(logical) == _OLD
    assert not (root / prefix / logical).exists()
    target.write_bytes(_CURRENT)
    return ScoringCase(consumer, {"path": name, **identity}, logical, target, buffer)


@pytest.mark.parametrize("name", _NAMES)
def test_scoring_roles_read_real_git_without_executing_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Authenticate full own old bytes and keep every native-equivalence flag false."""
    case = _case(tmp_path / "repository", monkeypatch, _OPTIMIZER, name)
    result = case.admit()
    receiver = name == _RECEIVER
    assert result["classification"] == (
        "finite_stored_receiver_coefficient_reader"
        if receiver
        else "explicit_historical_scoring_arithmetic_profile"
    )
    assert result["original_member"] == case.logical
    assert result["original_sha256"] == _identity(_OLD)["sha256"]
    assert result["original_bytes"] == len(_OLD)
    assert result["whole_old_module_reconstructed"] is True
    assert result["all_other_old_source_bytes_exact"] is True
    assert result["current_regular_single_link_and_stable"] is True
    assert result["saved_coefficients_read_not_recomputed"] is receiver
    assert result["current_scalar_admission_intentionally_separate"] is receiver
    assert result["historical_scoring_profile_explicitly_selected"] is not receiver
    assert result["old_native_equal_current_scoring_or_math_claimed"] is False
    assert result["new_quadrature_model_native_or_browser_execution_claimed"] is False
    assert not (case.consumer.repository / _OPTIMIZER / case.logical).exists()


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
def test_scoring_binding_and_freshness_refuse_after_a_real_positive_baseline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Keep exact source coordinates and final current-byte observations mandatory."""
    case = _case(tmp_path / "repository", monkeypatch, _OPTIMIZER, _CHALLENGE)
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
        _write(
            case.consumer.repository / _OPTIMIZER / case.logical, b"# extra own bytes\n"
        )
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
        metadata = case.consumer.repository / _OPTIMIZER / "capture.json"
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
                case.consumer.repository, _OPTIMIZER, case.consumer.members
            )
        case.admit()
