"""Authenticate performance controller roles with only invented Git objects."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import (
    SourceCapsule,
    index,
    objects,
    validated_descriptor,
)
from bijux_pollenomics_dev.native_backend import retained_performance as performance

from .test_execution_helper_batches import Consumer, _encoded, _git, _identity, _write

CONTROLS = frozenset(
    {
        "controls/boundary.py",
        "controls/check_contracts.py",
        "controls/measure.py",
        "controls/observe.py",
        "controls/prepare.py",
        "controls/run.py",
        "controls/scaling.py",
        "controls/shared/run_account_qualification.py",
        "controls/storage.py",
        "controls/workloads.py",
        "publication-controls/assemble.py",
        "publication-controls/check_contracts.py",
        "publication-controls/contracts.py",
        "publication-controls/observe.py",
        "publication-controls/prepare.py",
        "publication-controls/run.py",
        "publication-controls/proposal/packages/bijux-pollenomics-dev/"
        "src/bijux_pollenomics_dev/native_backend/retained_performance.py",
    }
)
REFERENCE = (
    "reference-inputs/docs/report/method-certification/"
    "author-site-uncertainty/replay.py"
)
UNADMITTED = "controls/unadmitted.py"
EXTRA_BODY = b"# Own inert unadmitted controller identity.\n"


@dataclass
class PerformanceCase(Consumer):
    """Keep the original performance helper on a tiny real indexed Git boundary."""

    canonical_paths: dict[str, str]

    def rows(self) -> list[dict[str, Any]]:
        """Use the actual consumer's list-shaped original member declaration."""
        return [{"path": name, **pin} for name, pin in self.members.items()]

    def framework(self) -> SourceCapsule:
        """Validate real descriptor and Git objects before the consumer role check."""
        return validated_descriptor(self.repository, self.prefix, self.rows())

    def invoke(self) -> None:
        """Use the maintained helper and real batch reader without a result mock."""
        resolver = performance._validate_source_transport(
            self.repository, self.repository / self.prefix, self.rows()
        )
        for name, body in self.bodies.items():
            assert resolver.read_source(name) == body

    def synchronize(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Bind only explicitly invented metadata to the existing own Git objects."""
        revision = _git(self.repository, "rev-parse", "HEAD").decode().strip()
        paths = [[name, self.canonical_paths[name]] for name in sorted(self.bodies)]
        git_rows = [
            [
                path,
                _git(self.repository, "rev-parse", revision + ":" + path)
                .decode()
                .strip(),
            ]
            for _, path in paths
        ]
        fingerprint = hashlib.sha256(
            json.dumps(
                sorted(git_rows), separators=(",", ":"), ensure_ascii=True
            ).encode()
        ).hexdigest()
        capture = _encoded({"members": self.members})
        _write(self.repository / self.prefix / "capture.json", capture)
        self.descriptor = {
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
                    "member_count": len(paths),
                    "git_entries_sha256": fingerprint,
                    "paths": paths,
                }
            ],
            "generated_members": [],
            "rewritten_source_epoch_executed": False,
        }
        self.detached = frozenset(self.bodies)
        self.repin(monkeypatch)


@pytest.fixture
def performance_case(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> PerformanceCase:
    """Invent every body and initialize a real Git owner, without copying evidence."""
    repository = tmp_path / "repository"
    repository.mkdir()
    _git(
        repository,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    names = sorted(CONTROLS | {REFERENCE, "source-code/packages/owned_performance.py"})
    bodies = {
        name: f"# Own inert performance identity {index}\n".encode()
        for index, name in enumerate(names)
    }
    canonical = {
        name: f"packages/owned_performance/source_{index:03d}.py"
        for index, name in enumerate(names)
    }
    canonical[UNADMITTED] = "packages/owned_performance/unadmitted.py"
    for name, body in bodies.items():
        _write(repository / canonical[name], body)
    _write(repository / canonical[UNADMITTED], EXTRA_BODY)
    _git(repository, "add", "--", *canonical.values())
    _git(
        repository,
        "-c",
        "user.name=Bijux fixture",
        "-c",
        "user.email=fixture@example.invalid",
        "commit",
        "--quiet",
        "--no-gpg-sign",
        "-m",
        "test(performance): retain own controller identities",
    )
    prefix = "data/owned-performance"
    members = {name: _identity(body) for name, body in bodies.items()}
    evidence = _encoded({"owned_evidence": True})
    members["evidence.json"] = _identity(evidence)
    _write(repository / prefix / "evidence.json", evidence)
    case = PerformanceCase(
        family="performance",
        repository=repository,
        prefix=prefix,
        members=members,
        detached=frozenset(bodies),
        bodies=bodies,
        descriptor={},
        batch_reads=[],
        canonical_paths=canonical,
    )
    case.synchronize(monkeypatch)
    return case


def test_all_performance_controls_use_one_real_authenticated_git_batch(
    performance_case: PerformanceCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Require all seventeen named controls and original package/reference roles."""
    real_read = objects.read_blobs
    calls: list[set[str]] = []

    def observed(
        root: Path, members: list[objects.GitSourceMember]
    ) -> dict[str, bytes]:
        result = real_read(root, members)
        calls.append(set(result))
        return result

    monkeypatch.setattr(index, "read_blobs", observed)
    performance_case.invoke()
    assert len(CONTROLS) == 17 and len(performance_case.bodies) == 19
    assert calls == [set(performance_case.bodies)]


@pytest.mark.parametrize(
    "name",
    [
        "controls/measure.py",
        "controls/shared/run_account_qualification.py",
        "publication-controls/assemble.py",
    ],
)
def test_missing_declared_performance_controller_refuses_after_valid_git_baseline(
    performance_case: PerformanceCase, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """A self-consistent smaller capsule must not remove an obligatory control."""
    performance_case.invoke()
    del performance_case.members[name], performance_case.bodies[name]
    performance_case.synchronize(monkeypatch)
    performance_case.framework()
    with pytest.raises(ValueError, match="detached source-role membership"):
        performance_case.invoke()


def test_unadmitted_performance_controller_refuses_after_valid_git_baseline(
    performance_case: PerformanceCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A real additional Git object grants no new execution-controller role."""
    performance_case.invoke()
    performance_case.members[UNADMITTED] = _identity(EXTRA_BODY)
    performance_case.bodies[UNADMITTED] = EXTRA_BODY
    performance_case.synchronize(monkeypatch)
    performance_case.framework()
    with pytest.raises(ValueError, match="detached source-role membership"):
        performance_case.invoke()


@pytest.mark.parametrize(
    "name",
    [
        "controls/measure.py",
        "controls/shared/run_account_qualification.py",
        "publication-controls/assemble.py",
    ],
)
def test_performance_controller_hash_substitution_refuses(
    performance_case: PerformanceCase, monkeypatch: pytest.MonkeyPatch, name: str
) -> None:
    """Actual Git body bytes must match each original logical controller identity."""
    performance_case.invoke()
    performance_case.members[name]["sha256"] = "0" * 64
    performance_case.synchronize(monkeypatch)
    with pytest.raises(ReportRebuildError):
        performance_case.invoke()


def test_physical_performance_controller_duplicate_refuses(
    performance_case: PerformanceCase,
) -> None:
    """Detached controller identity cannot authorize another physical programme copy."""
    performance_case.invoke()
    name = "controls/measure.py"
    _write(
        performance_case.repository / performance_case.prefix / name,
        performance_case.bodies[name],
    )
    with pytest.raises(ReportRebuildError):
        performance_case.invoke()
