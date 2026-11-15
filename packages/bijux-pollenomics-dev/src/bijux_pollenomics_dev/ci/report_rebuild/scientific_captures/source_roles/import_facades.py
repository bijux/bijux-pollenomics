"""Bind deferred public imports to three fixed original/current whole-source pairs."""

from __future__ import annotations

import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

_ROOT = "packages/bijux-pollenomics/src/bijux_pollenomics/"
_SOURCE_PAIRS: dict[str, tuple[int, str, int, str]] = {
    _ROOT + "__init__.py": (
        1429,
        "e72be5803a76413853e2a0c39d42e380766dec85cd19c5fc0fff727bd1879133",
        3631,
        "382adbefbd8b8e5e76b4d77e253c3f6788ad62988bea577a85cd9c5b4712f799",
    ),
    _ROOT + "collection/__init__.py": (
        1437,
        "ee5e80046504a0b1cd9f5145aa2ffaa8ca98a5d1edf324035adf1be522264c86",
        3543,
        "ee9ade3ab1bd1d05a1d19721bc7116f6635d99239c7660d6834703b659288b22",
    ),
    _ROOT + "collection/sources/neotoma/__init__.py": (
        1959,
        "658a9590a1ae9e688af5243f601f5ec6a4744907ee71c69e6fd44f16a489ca98",
        4460,
        "919c80cdf20b41758ab2147dfb36f932b60081ca3bea433426f2a6e7eab3008d",
    ),
}
PUBLIC_IMPORT_FACADE_SOURCES = frozenset(_SOURCE_PAIRS)
_CAPTURE_CONTEXTS = {
    "data/atlas/sample-chronology-source-view-capture": (
        "2491a59a0d5cde5dffd05397c4a7dcc95ab98ba922019863e5ea2662681dba62",
        "source/",
    ),
    "data/method-certification/author-optimizer-diagnostic-source-capture": (
        "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93",
        "executions/optimizer-diagnostics/first-party-inputs/",
    ),
}


def import_facade_pair_matches(name: str, captured: bytes, current: bytes) -> bool:
    """Recognize only reviewed complete source bytes, without executing either body."""
    pair = _SOURCE_PAIRS.get(name)
    return (
        pair is not None
        and (
            len(captured),
            hashlib.sha256(captured).hexdigest(),
            len(current),
            hashlib.sha256(current).hexdigest(),
        )
        == pair
    )


def validated_import_facade_source(
    repository: Path, historical: JsonObject, logical: str, source_buffer: SourceCapsule
) -> JsonObject:
    """Authenticate a declared import boundary without relabeling the old execution."""
    name = historical.get("path")
    pair = _SOURCE_PAIRS.get(name) if isinstance(name, str) else None
    context = _CAPTURE_CONTEXTS.get(source_buffer.prefix)
    if not isinstance(name, str) or pair is None:
        raise ReportRebuildError("Unknown public import facade source")
    expected = {"bytes": pair[0], "sha256": pair[1]}
    if (
        context is None
        or repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.descriptor.capture.get("sha256") != context[0]
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != context[1] + name
        or logical not in source_buffer.detached
        or source_buffer.descriptor.members.get(logical) != expected
        or [
            path
            for group in source_buffer.descriptor.groups
            for member, path in group["resolved_paths"]
            if member == logical
        ]
        != [name]
    ):
        raise ReportRebuildError("Public import facade original binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current public import facade")
    before = path.stat()
    if before.st_nlink != 1 or before.st_size != pair[2]:
        raise ReportRebuildError("Current public import facade is linked or differs")
    current = path.read_bytes()
    if not import_facade_pair_matches(name, captured, current):
        raise ReportRebuildError("Public import facade whole-source pair differs")
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current public import facade")
    after = again.stat()
    fields = (
        "st_dev",
        "st_ino",
        "st_mode",
        "st_nlink",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
    )
    if (
        any(getattr(before, field) != getattr(after, field) for field in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Public import facade changed during correspondence")
    return {
        "path": name,
        "classification": "fixed_public_import_facade_correspondence",
        "original_member": logical,
        "historical": expected,
        "current": {"bytes": pair[2], "sha256": pair[3]},
        "whole_original_and_current_source_bytes_authenticated": True,
        "current_regular_single_link_and_stable": True,
        "historical_execution_epoch_changed": False,
        "current_api_qualification_required_separately": True,
        "current_source_or_numerical_equivalence_claimed": False,
        "historical_program_execution_claimed": False,
        "scope": "Only three exact public import facades defer existing owner imports. Original source/Git witnesses and execution epochs remain literal; current API compatibility has separate constructed controls. No whole-tree, numerical, browser or scientific equivalence follows.",
    }
