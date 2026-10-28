"""Keep the native Linux reference predicates strict through source transport."""

from __future__ import annotations

import ast
import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

import pytest
from bijux_pollenomics_dev.ci.report_rebuild.contracts import ReportRebuildError

ROOT = Path(__file__).resolve().parents[4]
MODULE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/linux_r_reference.py"
EPOCH = "6d8f1c5beffc2627b14e3330f8567e60f0fc8c36"


@dataclass
class NativeEvidence:
    packet: Path
    capture: dict[str, Any]
    objects: dict[str, dict[str, Any]]
    body: bytes
    calls: list[str]

    def read(self, name: str) -> bytes:
        self.calls.append(name)
        assert name.startswith("source/packages/synthetic/")
        assert not (self.packet / name).exists()
        return self.body

    def publish(self) -> None:
        for name, value in self.objects.items():
            target = self.packet / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(json.dumps(value))


def native_helpers(source: str) -> dict[str, Any]:
    """Load only the native-reference function AST for source-free controls."""
    tree = ast.parse(source)
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name in {"_object", "_json", "_zero", "_native_references"}
    ]
    assert len(tree.body) == 4
    values: dict[str, Any] = {
        "Path": Path,
        "PurePosixPath": PurePosixPath,
        "Any": Any,
        "JsonObject": dict[str, Any],
        "Callable": Callable,
        "ReportRebuildError": ReportRebuildError,
        "json": json,
        "hashlib": hashlib,
        "SOURCE_CANDIDATE": EPOCH,
    }
    exec(compile(tree, MODULE, "exec"), values)
    return values


@pytest.fixture
def helpers() -> dict[str, Any]:
    """Expose native custody helpers without importing scientific producers."""
    return native_helpers((ROOT / MODULE).read_text())


@pytest.fixture
def evidence(tmp_path: Path) -> NativeEvidence:
    """Construct exact small native receipt and callback byte fixtures."""
    body = b"explicit source-free synthetic body"
    references = {
        "plan": "execution/plan.json",
        "common_terminal": "execution/terminal.json",
        "outer_terminal": "execution/linux-source-terminal.json",
        "independent_numerical_review": "execution/independent-review.json",
        "source_reference": "execution/source-reference.json",
    }
    plan: dict[str, Any] = {
        "candidate": EPOCH,
        "canonical_identity": {"synthetic": True},
        "stages": [{"argv": ["synthetic-one"]}, {"argv": ["synthetic-two"]}],
    }
    checksum = hashlib.sha256(json.dumps(plan).encode()).hexdigest()
    objects: dict[str, dict[str, Any]] = {
        references["plan"]: plan,
        references["common_terminal"]: {
            "candidate": EPOCH,
            "plan_sha256": checksum,
            "actual_exit": 0,
            "canonical_before": plan["canonical_identity"],
            "canonical_after": plan["canonical_identity"],
            "before_pin_mismatches": [],
            "after_pin_mismatches": [],
            "stages": [
                {"actual_exit": 0, "timed_out": False, "argv": ["synthetic-one"]},
                {"actual_exit": 0, "timed_out": False, "argv": ["synthetic-two"]},
            ],
        },
        references["outer_terminal"]: {
            "candidate": EPOCH,
            "registered_plan_sha256": checksum,
            "actual_exit": 0,
            "common_actual_exit": 0,
            "all_protected_inputs_unchanged": True,
            "memory_bound_passed": True,
            "storage_bound_passed": True,
        },
        references["independent_numerical_review"]: {
            "candidate": EPOCH,
            "core_cases": 43,
            "source_domain_cases": 23,
            "all_complete_source_runtime_output_joins_passed": True,
            "release_certificate": False,
            "independent_comparisons": [{} for _ in range(66)],
        },
        references["source_reference"]: {
            "base_candidate": EPOCH,
            "source_files": {
                f"packages/synthetic/owner-{i}.py": hashlib.sha256(body).hexdigest()
                for i in range(2148)
            },
        },
    }
    result = NativeEvidence(
        tmp_path,
        {
            "schema_version": "retained-linux-r-source-capture.v1",
            "source_candidate": EPOCH,
            "execution_references": references,
        },
        objects,
        body,
        [],
    )
    result.publish()
    return result


def test_all_native_source_reads_use_the_explicit_scoped_callback(
    helpers: dict[str, Any],
    evidence: NativeEvidence,
) -> None:
    """Require every native source member to use its declared retained-byte callback."""
    helpers["_native_references"](evidence.packet, evidence.capture, evidence.read)
    assert len(evidence.calls) == 2148
    assert evidence.calls == [
        "source/" + name
        for name in evidence.objects["execution/source-reference.json"]["source_files"]
    ]


def test_changed_callback_bytes_cannot_pass_old_source_pins(
    helpers: dict[str, Any],
    evidence: NativeEvidence,
) -> None:
    """Refuse changed retained bytes despite an unchanged declared source pin."""
    evidence.body += b" changed"
    with pytest.raises(ReportRebuildError, match="executed source bytes differ"):
        helpers["_native_references"](evidence.packet, evidence.capture, evidence.read)


def test_callback_refusal_cannot_fall_back_to_a_current_source_file(
    helpers: dict[str, Any],
    evidence: NativeEvidence,
) -> None:
    """Propagate a refused retained read without consulting current source bytes."""

    def refused(name: str) -> bytes:
        raise ReportRebuildError("synthetic retained source refused")

    with pytest.raises(ReportRebuildError, match="synthetic retained source refused"):
        helpers["_native_references"](evidence.packet, evidence.capture, refused)


@pytest.mark.parametrize(
    "damage",
    [
        "missing_source",
        "unsafe_source",
        "wrong_epoch",
        "boolean_exit",
        "changed_argv",
        "false_review",
        "case_count",
        "comparison_count",
    ],
)
def test_transport_preserves_the_original_native_evidence_refusals(
    helpers: dict[str, Any],
    evidence: NativeEvidence,
    damage: str,
) -> None:
    """Retain exact native epoch, completion, inventory and integer-zero guards."""
    if damage == "missing_source":
        evidence.objects["execution/source-reference.json"]["source_files"].pop(
            "packages/synthetic/owner-0.py"
        )
    elif damage == "unsafe_source":
        sources = evidence.objects["execution/source-reference.json"]["source_files"]
        sources["../escape.py"] = sources.pop("packages/synthetic/owner-0.py")
    elif damage == "wrong_epoch":
        evidence.objects["execution/independent-review.json"]["candidate"] = "0" * 40
    elif damage == "boolean_exit":
        evidence.objects["execution/terminal.json"]["actual_exit"] = False
    elif damage == "changed_argv":
        evidence.objects["execution/terminal.json"]["stages"][0]["argv"] = [
            "different-command"
        ]
    elif damage == "false_review":
        evidence.objects["execution/independent-review.json"][
            "all_complete_source_runtime_output_joins_passed"
        ] = False
    elif damage == "case_count":
        evidence.objects["execution/independent-review.json"]["source_domain_cases"] = (
            22
        )
    else:
        evidence.objects["execution/independent-review.json"][
            "independent_comparisons"
        ].pop()
    evidence.publish()
    with pytest.raises(ReportRebuildError):
        helpers["_native_references"](evidence.packet, evidence.capture, evidence.read)


def projection_helpers(source: str) -> dict[str, Any]:
    """Load the reviewed current-source projection helpers in isolation."""
    tree = ast.parse(source)
    tree.body = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name
        in {"_named_documentation_insertions", "_require_scientific_projection"}
    ]
    assert len(tree.body) == 2
    values: dict[str, Any] = {
        "Path": Path,
        "Any": Any,
        "ast": ast,
        "hashlib": hashlib,
        "ReportRebuildError": ReportRebuildError,
        "_file": lambda repository, name, label: repository / name,
        "_CURRENT_READER_CORRESPONDENCE": {},
        "_DOCUMENTED_NUMERIC_DEFINITIONS": {},
    }
    exec(compile(tree, MODULE, "exec"), values)
    return values


@pytest.fixture
def projection() -> dict[str, Any]:
    """Construct historical and current source identities from invented bytes."""
    return projection_helpers((ROOT / MODULE).read_text())


def test_ordinary_exact_source_retains_its_original_size_bound(
    tmp_path: Path,
    projection: dict[str, Any],
) -> None:
    """Admit an unchanged ordinary source at its original declared byte bound."""
    body = b"s" * 822732
    (tmp_path / "native-input.tar.gz").write_bytes(body)
    projection["_require_scientific_projection"](
        tmp_path,
        "native-input.tar.gz",
        {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)},
        body,
    )


@pytest.mark.parametrize(
    "damage", ["numeric", "comment", "wrong_old_identity", "unknown_path"]
)
def test_reader_correspondence_is_exact_and_never_a_generic_source_fallback(
    tmp_path: Path,
    projection: dict[str, Any],
    damage: str,
) -> None:
    """Admit only the fixed reader identities and refuse other current bodies."""
    old = b"def read(): return 1\n"
    current = b"def read(): return 1  # explicit synthetic transport body\n"
    name = "reader.py"
    identity: dict[str, Any] = {
        "sha256": hashlib.sha256(old).hexdigest(),
        "bytes": len(old),
    }
    projection["_CURRENT_READER_CORRESPONDENCE"][name] = [
        identity["sha256"],
        identity["bytes"],
        hashlib.sha256(current).hexdigest(),
        len(current),
    ]
    (tmp_path / name).write_bytes(current)
    check = projection["_require_scientific_projection"]
    check(tmp_path, name, identity, old)
    if damage == "numeric":
        current = current.replace(b"return 1", b"return 2")
    elif damage == "comment":
        current += b"# another body\n"
    elif damage == "wrong_old_identity":
        projection["_CURRENT_READER_CORRESPONDENCE"][name][0] = "0" * 64
    else:
        name = "other.py"
    (tmp_path / name).write_bytes(current)
    with pytest.raises(ReportRebuildError):
        check(tmp_path, name, identity, old)


@pytest.mark.parametrize(
    "damage", ["historical_bytes", "historical_size", "historical_sha"]
)
def test_original_source_identity_cannot_be_replaced_by_current_correspondence(
    tmp_path: Path,
    projection: dict[str, Any],
    damage: str,
) -> None:
    """Require the captured identity before considering an explicit correspondence."""
    old = b"synthetic historical source"
    current = b"synthetic current source"
    name = "reader.py"
    identity: dict[str, Any] = {
        "sha256": hashlib.sha256(old).hexdigest(),
        "bytes": len(old),
    }
    projection["_CURRENT_READER_CORRESPONDENCE"][name] = [
        identity["sha256"],
        identity["bytes"],
        hashlib.sha256(current).hexdigest(),
        len(current),
    ]
    (tmp_path / name).write_bytes(current)
    if damage == "historical_bytes":
        old += b"x"
    elif damage == "historical_size":
        identity["bytes"] += 1
    else:
        identity["sha256"] = "0" * 64
    with pytest.raises(ReportRebuildError, match="original source projection"):
        projection["_require_scientific_projection"](tmp_path, name, identity, old)


@pytest.mark.parametrize(
    "damage",
    [
        "numeric",
        "comment",
        "other_doc",
        "signature",
        "duplicate",
        "missing_declared_doc",
    ],
)
def test_only_named_literal_documentation_insertions_preserve_numeric_source(
    tmp_path: Path,
    projection: dict[str, Any],
    damage: str,
) -> None:
    """Permit the named literal docs while preserving every other source byte."""
    old = b"def first():\n    return 1\n\ndef second():\n    return 2\n"
    current = old.replace(
        b"def first():\n",
        b'def first():\n    """Explicit synthetic documentation."""\n',
    )
    name = "counting.py"
    identity: dict[str, Any] = {
        "sha256": hashlib.sha256(old).hexdigest(),
        "bytes": len(old),
    }
    projection["_DOCUMENTED_NUMERIC_DEFINITIONS"][name] = ["first"]
    (tmp_path / name).write_bytes(current)
    check = projection["_require_scientific_projection"]
    check(tmp_path, name, identity, old)
    if damage == "numeric":
        current = current.replace(b"return 1", b"return 3")
    elif damage == "comment":
        current += b"# additional comment\n"
    elif damage == "other_doc":
        current = current.replace(
            b"def second():\n", b'def second():\n    """Another definition."""\n'
        )
    elif damage == "signature":
        current = current.replace(b"def first():", b"def first(value):")
    elif damage == "duplicate":
        current += b"\ndef first():\n    return 4\n"
    else:
        projection["_DOCUMENTED_NUMERIC_DEFINITIONS"][name] = ["first", "second"]
    (tmp_path / name).write_bytes(current)
    with pytest.raises(
        ReportRebuildError, match="current scientific implementation changed"
    ):
        check(tmp_path, name, identity, old)
