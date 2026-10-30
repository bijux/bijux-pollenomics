"""Verify each execution-source consumer against strict owned Git batches."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import subprocess
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import index, objects
from bijux_pollenomics_dev.ci.report_rebuild.retained_source.objects import (
    GitSourceMember,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.country_reports.sweden import (
    metadata as sweden,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.lake_registry.svar_census import (
    transport as census,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.pollen_source import (
    swedish_cohort as cohort,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.vegetation_reference import (
    slu_guide as slu,
)

FAMILIES = ("sweden", "svar_census", "swedish_cohort", "slu_guide")
PROOFS = {
    "plan": "plan.json",
    "inner": "terminal.json",
    "outer": "launch-terminal.json",
    "assembly": "assembly.json",
    "observer": "independent-review.json",
}


def _git(repository: Path, *args: str) -> bytes:
    """Use only the tiny invented repository and the maintained Git environment."""
    return subprocess.check_output(
        [str(objects.git_executable()), "-C", str(repository), *args],
        env=objects.environment(),
        stderr=subprocess.PIPE,
        timeout=10,
    )


def _encoded(value: object) -> bytes:
    """Encode only owned fixture metadata deterministically."""
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def _identity(body: bytes) -> dict[str, Any]:
    """Bind own bytes to the actual source-catalogue identity schema."""
    return {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}


def _write(path: Path, body: bytes) -> None:
    """Write a tiny owned fixture, never copy a package or retained packet."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(body)


@dataclass
class Consumer:
    """Keep tiny metadata and read observations for one actual maintained consumer."""

    family: str
    repository: Path
    prefix: str
    members: dict[str, dict[str, Any]]
    detached: frozenset[str]
    bodies: dict[str, bytes]
    descriptor: dict[str, Any]
    batch_reads: list[set[str]]

    def invoke(self) -> None:
        """Call the original maintained helper without mocking its transport boundary."""
        if self.family == "sweden":
            resolver = sweden._retention_sources(self.repository, PROOFS)
            for name, body in self.bodies.items():
                assert resolver.read_source(name) == body
        elif self.family == "svar_census":
            census._validate_source_members(self.repository, self.prefix, self.members)
        elif self.family == "swedish_cohort":
            cohort._validate_source_members(self.repository, self.prefix)
        else:
            assert self.family == "slu_guide"
            slu._validate_source_members(self.repository, self.prefix)

    def repin(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Admit deliberately constructed metadata through the real registry/parser."""
        raw = _encoded(self.descriptor)
        _write(self.repository / self.prefix / "source-transport.json", raw)
        registry = {
            "schema_version": "retained-source-index.v1",
            "capsules": {
                self.prefix: {"descriptor": "source-transport.json", **_identity(raw)}
            },
            "source_revisions": {},
        }
        raw_index = _encoded(registry)
        _write(self.repository / index.INDEX_PATH, raw_index)
        monkeypatch.setattr(
            index, "INDEX_SHA256", hashlib.sha256(raw_index).hexdigest()
        )
        monkeypatch.setattr(index, "INDEX_BYTES", len(raw_index))


@pytest.fixture(params=FAMILIES)
def consumer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> Consumer:
    """Preserve each exact detached role set while inventing every body and Git object."""
    family = str(request.param)
    if family == "sweden":
        prefix = sweden.BASE.rstrip("/")
        detached = sweden.DETACHED_SOURCE_MEMBERS
        logical_names = {
            *("controller/" + name for name in sweden.CONTROLLER_IDENTITIES),
            *PROOFS.values(),
        }
        capture_name = "source-members.json"
    elif family == "svar_census":
        prefix = str(Path(census.CAPTURE).parent)
        detached = census.DETACHED_SOURCE_MEMBERS
        logical_names = {*detached, "evidence.json"}
        capture_name = "capture.json"
    elif family == "swedish_cohort":
        prefix = str(Path(cohort.CAPTURE).parent)
        detached = cohort.DETACHED_SOURCE_MEMBERS
        logical_names = {*detached, "evidence.json"}
        capture_name = "capture.json"
    else:
        assert family == "slu_guide"
        prefix = str(Path(slu.CAPTURE).parent)
        detached = slu.DETACHED_SOURCE_MEMBERS
        logical_names = {*detached, "evidence.json"}
        capture_name = "capture.json"
    assert detached and detached <= logical_names
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
    bodies: dict[str, bytes] = {}
    paths: list[list[str]] = []
    members: dict[str, dict[str, Any]] = {}
    for number, name in enumerate(sorted(logical_names)):
        raw = (
            f"# Own inert identity {number}\n".encode()
            if name in detached
            else _encoded({"owned_evidence": number})
        )
        members[name] = _identity(raw)
        if name in detached:
            canonical = f"packages/owned_execution_helpers/source_{number:03d}.py"
            _write(repository / canonical, raw)
            bodies[name] = raw
            paths.append([name, canonical])
        else:
            _write(repository / prefix / name, raw)
    _git(repository, "add", "--", *(path for _, path in paths))
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
        "test(source): retain owned helper identities",
    )
    revision = _git(repository, "rev-parse", "HEAD").decode().strip()
    git_rows: list[list[str]] = []
    for _, canonical in paths:
        blob = _git(repository, "rev-parse", "HEAD:" + canonical).decode().strip()
        git_rows.append([canonical, blob])
    raw_map = json.dumps(
        sorted(git_rows), separators=(",", ":"), ensure_ascii=True
    ).encode()
    if family == "sweden":
        proof_rows = {name: members[path] for name, path in PROOFS.items()}
        controller_rows = {
            name: members["controller/" + name] for name in sweden.CONTROLLER_IDENTITIES
        }
        monkeypatch.setattr(sweden, "PROOF_IDENTITIES", proof_rows)
        monkeypatch.setattr(sweden, "CONTROLLER_IDENTITIES", controller_rows)
        document: dict[str, Any] = {
            "schema_version": "sweden-retained-proof-source-members.v1",
            "members": members,
        }
    else:
        document = {"members": members}
        if family == "swedish_cohort":
            monkeypatch.setattr(cohort, "EXPECTED_MEMBERS", members)
        elif family == "slu_guide":
            monkeypatch.setattr(slu, "EXPECTED_MEMBERS", members)
    capture = (
        (json.dumps(document, separators=(",", ":")) + "\n").encode()
        if family == "sweden"
        else _encoded(document)
    )
    _write(repository / prefix / capture_name, capture)
    if family == "sweden":
        monkeypatch.setattr(sweden, "RETENTION_SOURCE_MEMBERS", _identity(capture))
    descriptor = {
        "schema_version": "git-retained-source.v1",
        "capture": {"name": capture_name, **_identity(capture)},
        "historical_native_epochs": [revision],
        "source_revision_correspondence": [
            {"historical_source_commit": revision, "source_revision": revision}
        ],
        "git_groups": [
            {
                "historical_source_commit": revision,
                "source_revision": revision,
                "member_count": len(paths),
                "git_entries_sha256": hashlib.sha256(raw_map).hexdigest(),
                "paths": paths,
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    reads: list[set[str]] = []

    def read_blobs(root: Path, selected: list[GitSourceMember]) -> dict[str, bytes]:
        assert root == repository
        result = objects.read_blobs(root, selected)
        assert result == bodies
        reads.append(set(result))
        return result

    monkeypatch.setattr(index, "read_blobs", read_blobs)
    result = Consumer(
        family, repository, prefix, members, detached, bodies, descriptor, reads
    )
    result.repin(monkeypatch)
    return result


def test_execution_helpers_use_one_strict_git_batch(consumer: Consumer) -> None:
    """Read every declared helper through the real object decoder exactly once."""
    consumer.invoke()
    assert consumer.batch_reads == [set(consumer.detached)]
    for name in consumer.detached:
        assert not (consumer.repository / consumer.prefix / name).exists()


def test_detached_execution_helper_cannot_reappear_physically(
    consumer: Consumer,
) -> None:
    """An extra own body under the retained prefix must fail before another Git read."""
    consumer.invoke()
    assert consumer.batch_reads == [set(consumer.detached)]
    selected = min(consumer.detached)
    _write(
        consumer.repository / consumer.prefix / selected,
        b"unlisted owned source body\n",
    )
    with pytest.raises(ReportRebuildError):
        consumer.invoke()
    assert consumer.batch_reads == [set(consumer.detached)]


@pytest.mark.parametrize(
    "damage", ["missing", "wrong_path", "unreachable", "wrong_digest"]
)
def test_execution_helper_correspondence_refusals(
    consumer: Consumer, monkeypatch: pytest.MonkeyPatch, damage: str
) -> None:
    """Preserve the original cohort correspondence refusals for every maintained helper."""
    consumer.invoke()
    assert consumer.batch_reads == [set(consumer.detached)]
    consumer.batch_reads.clear()
    group = consumer.descriptor["git_groups"][0]
    if damage == "missing":
        group["paths"].pop()
        group["member_count"] -= 1
    elif damage == "wrong_path":
        group["paths"][0][1] = "packages/owned_execution_helpers/absent.py"
    elif damage == "unreachable":
        group["source_revision"] = "f" * 40
        consumer.descriptor["source_revision_correspondence"][0]["source_revision"] = (
            "f" * 40
        )
    else:
        group["git_entries_sha256"] = "f" * 64
    consumer.repin(monkeypatch)
    with pytest.raises(ReportRebuildError):
        consumer.invoke()
    assert consumer.batch_reads == []
