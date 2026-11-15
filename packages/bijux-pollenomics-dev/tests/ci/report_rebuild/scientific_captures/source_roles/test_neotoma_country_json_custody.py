"""Country parser evolution retains inert original bodies through normal Git custody."""

from __future__ import annotations

from dataclasses import dataclass, replace
from functools import lru_cache
import json
import os
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError
from bijux_pollenomics_dev.ci.report_rebuild.ownership import ReportOwnershipError
from bijux_pollenomics_dev.ci.report_rebuild.retained_source import SourceCapsule, index
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    sample_chronology_capture as chronology,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures import (
    source_correspondence as router,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.source_roles import (
    neotoma_country_json as subject,
)

from ...source_contracts.test_execution_helper_batches import (
    Consumer,
    _encoded,
    _git,
    _identity,
    _write,
)

SOURCE = "packages/bijux-pollenomics/src/bijux_pollenomics/collection/sources/neotoma/country/site_geometry.py"
CONTEXTS = (
    "data/atlas/sample-chronology-source-view-capture",
    "data/method-certification/author-optimizer-diagnostic-source-capture",
    "data/method-certification/constrained-author-source-capture",
    "data/method-certification/author-radius-source-capture",
)


@lru_cache(maxsize=1)
def old_body() -> bytes:
    repository = next(
        p
        for p in Path(__file__).resolve().parents
        if (p / "configs/pytest.ini").is_file()
    )
    body = _git(
        repository, "show", "f5ab77edcd3affee65723074d21b83161b4bf542:" + SOURCE
    )
    assert _identity(body) == {
        "bytes": 1390,
        "sha256": "d505b30b823ecfa8f039a5154e6382ec46ee9174f9134026b7d71616574b4040",
    }
    return body


def current_body() -> bytes:
    result = old_body()
    for original, current in subject._COUNTRY_JSON_SPANS:
        assert result.count(original) == 1
        result = result.replace(original, current, 1)
    return result


@dataclass
class Case:
    consumer: Consumer
    row: dict[str, Any]
    logical: str
    target: Path
    buffer: SourceCapsule

    def admit(self) -> dict[str, Any]:
        return subject.validated_neotoma_country_json_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )

    def dispatch(self) -> object:
        if self.consumer.prefix == CONTEXTS[0]:
            chronology._validate_current_source(
                self.consumer.repository,
                SOURCE,
                self.logical,
                old_body(),
                self.row["sha256"],
                self.buffer.detached,
                source_buffer=self.buffer,
            )
            return None
        return router.validated_current_scientific_source(
            self.consumer.repository, self.row, self.logical, self.buffer
        )


def case(root: Path, monkeypatch: pytest.MonkeyPatch, prefix: str) -> Case:
    owner = subject
    root.mkdir()
    _git(
        root,
        "init",
        "--quiet",
        "--template=",
        "--initial-branch=main",
        "--object-format=sha1",
    )
    target = root / SOURCE
    _write(target, old_body())
    _git(root, "add", "--", SOURCE)
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
        "test(country): retain inert geometry source",
    )
    revision = _git(root, "rev-parse", "HEAD").decode().strip()
    blob = _git(root, "rev-parse", "HEAD:" + SOURCE).decode().strip()
    _, prefixes = owner._CAPTURE_CONTEXTS[prefix]
    logicals = [p + SOURCE for p in prefixes]
    members = {name: _identity(old_body()) for name in logicals}
    capture = _encoded({"members": members})
    _write(root / prefix / "capture.json", capture)
    mapping = json.dumps(
        sorted([[SOURCE, blob] for _ in logicals]), separators=(",", ":")
    ).encode()
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
                "member_count": len(logicals),
                "git_entries_sha256": _identity(mapping)["sha256"],
                "paths": [[name, SOURCE] for name in logicals],
            }
        ],
        "generated_members": [],
        "rewritten_source_epoch_executed": False,
    }
    consumer = Consumer(
        "qualification",
        root,
        prefix,
        members,
        frozenset(logicals),
        {name: old_body() for name in logicals},
        descriptor,
        [],
    )
    consumer.repin(monkeypatch)
    contexts = dict(owner._CAPTURE_CONTEXTS)
    contexts[prefix] = (_identity(capture)["sha256"], prefixes)
    monkeypatch.setattr(owner, "_CAPTURE_CONTEXTS", contexts)
    buffer = index.validated_descriptor(root, prefix, members)
    target.write_bytes(current_body())
    return Case(
        consumer, {"path": SOURCE, **_identity(old_body())}, logicals[0], target, buffer
    )


@pytest.mark.parametrize("prefix", CONTEXTS)
def test_real_git_originals_and_maintained_dispatch_admit_only_the_refusal_guard(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    prefix: str,
) -> None:
    owned = case(tmp_path / "repository", monkeypatch, prefix)
    result = owned.admit()
    assert result["classification"] == "strict_neotoma_country_json_refusal"
    assert result["whole_old_module_reconstructed"] is True
    assert result["current_country_or_numerical_equivalence_claimed"] is False
    assert result["historical_program_execution_claimed"] is False
    owned.dispatch()
    for alias in result["original_members"]:
        assert owned.buffer.read_source(alias) == old_body()
        assert not (owned.consumer.repository / prefix / alias).exists()


@pytest.mark.parametrize(
    "damage",
    [
        "append",
        "duplicate_span",
        "bbox",
        "geometry",
        "missing_span",
        "old_body",
        "foreign_source",
    ],
)
def test_two_span_inverse_refuses_every_other_source_change(damage: str) -> None:
    owner = subject
    current = current_body()
    name, old = SOURCE, old_body()
    if damage == "append":
        current += b"# foreign\n"
    elif damage == "duplicate_span":
        current += owner._COUNTRY_JSON_SPANS[0][1]
    elif damage == "bbox":
        current = current.replace(b"if not point_in_bbox", b"if point_in_bbox")
    elif damage == "geometry":
        current = current.replace(b'site.get("geography")', b'site.get("location")')
    elif damage == "missing_span":
        current = current.replace(
            owner._COUNTRY_JSON_SPANS[0][1], owner._COUNTRY_JSON_SPANS[0][0], 1
        )
    elif damage == "old_body":
        old += b"# foreign\n"
    else:
        name = SOURCE.replace("site_geometry.py", "decisions.py")
    assert not owner.country_json_protocol_matches(name, old, current)


@pytest.mark.parametrize(
    "damage",
    [
        "capture",
        "context",
        "logical",
        "historical",
        "mapping",
        "extra_mapping_alias",
        "foreign_cached_body",
        "member",
        "detached",
        "symlink",
        "hardlink",
        "source_edit",
        "repository_alias",
        "missing_radius_alias",
        "metadata_drift",
        "inode_drift",
    ],
)
def test_success_then_source_binding_and_freshness_damage_refuses(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    damage: str,
) -> None:
    owned = case(tmp_path / "repository", monkeypatch, CONTEXTS[3])
    owned.admit()
    if damage == "capture":
        owned.buffer = replace(
            owned.buffer,
            descriptor=replace(
                owned.buffer.descriptor,
                capture={**owned.buffer.descriptor.capture, "sha256": "0" * 64},
            ),
        )
    elif damage == "context":
        owned.buffer = replace(owned.buffer, prefix="data/foreign")
    elif damage == "logical":
        owned.logical = "foreign/" + SOURCE
    elif damage == "historical":
        owned.row = {**owned.row, "sha256": "0" * 64}
    elif damage == "mapping":
        group = {
            **owned.buffer.descriptor.groups[0],
            "resolved_paths": [[owned.logical, "packages/foreign.py"]],
        }
        owned.buffer = replace(
            owned.buffer, descriptor=replace(owned.buffer.descriptor, groups=(group,))
        )
    elif damage == "extra_mapping_alias":
        group = {
            **owned.buffer.descriptor.groups[0],
            "resolved_paths": [
                *owned.buffer.descriptor.groups[0]["resolved_paths"],
                ["unowned/alias.py", SOURCE],
            ],
        }
        owned.buffer = replace(
            owned.buffer, descriptor=replace(owned.buffer.descriptor, groups=(group,))
        )
    elif damage == "foreign_cached_body":
        owned.buffer = replace(
            owned.buffer, _payloads=dict.fromkeys(owned.buffer.detached, b"foreign")
        )
    elif damage == "member":
        owned.buffer = replace(
            owned.buffer,
            descriptor=replace(
                owned.buffer.descriptor, members={owned.logical: _identity(b"foreign")}
            ),
        )
    elif damage == "detached":
        owned.buffer = replace(
            owned.buffer,
            descriptor=replace(owned.buffer.descriptor, detached=frozenset()),
        )
    elif damage in {"symlink", "hardlink"}:
        actual = owned.target.with_name("current.py")
        owned.target.rename(actual)
        if damage == "symlink":
            owned.target.symlink_to(actual)
        else:
            os.link(actual, owned.target)
    elif damage == "source_edit":
        owned.target.write_bytes(current_body() + b"# foreign\n")
    elif damage == "repository_alias":
        alias = tmp_path / "alias"
        alias.symlink_to(owned.consumer.repository, target_is_directory=True)
        owned.consumer.repository = alias
    elif damage == "missing_radius_alias":
        members = dict(owned.buffer.descriptor.members)
        members.pop(next(name for name in members if name != owned.logical))
        owned.buffer = replace(
            owned.buffer, descriptor=replace(owned.buffer.descriptor, members=members)
        )
    else:
        original = subject.country_json_protocol_matches

        def change(name: str, old: bytes, current: bytes) -> bool:
            result = original(name, old, current)
            if damage == "metadata_drift":
                p = owned.consumer.repository / owned.consumer.prefix / "capture.json"
                p.write_bytes(p.read_bytes() + b" ")
            else:
                p = owned.target.with_name("replacement.py")
                p.write_bytes(current)
                p.replace(owned.target)
            return result

        monkeypatch.setattr(subject, "country_json_protocol_matches", change)
    with pytest.raises((ReportRebuildError, ReportOwnershipError)):
        owned.admit()
