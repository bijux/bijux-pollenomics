"""Separate historical reader IO from unchanged numerical and native predicates."""

from __future__ import annotations

import ast
import hashlib
from pathlib import Path

from ...contracts import JsonObject, ReportRebuildError
from ...ownership import _regular_confined_file
from ...retained_source import SourceCapsule

CUSTODY_READER_CONTRACTS = {
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/atlas_source_views.py": "Exact API/root API Git preimage getters and historical portal reader metadata role; existing native capture predicates unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/author_site_evaluations.py": "Accepted117 scoped Git IO, exact generated539 aliases, unresolved-profile partition, named managed-footer semantics, finite spatial export role; native helper predicates unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/linux_r_reference.py": "Accepted270 fixed four IO correspondences, exact named docs and generated539 metadata role; all native137/43+23/66 criteria unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/sample_chronology_capture.py": "Accepted97 SourceCapsule IO, historical six portal readers and exact23 named documentation insertions; native9/5/43 predicates unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics.py": "Accepted diagnostics producer read_input only for capture-owned paths; physical Petr input stays physical. No numerical expression change.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics_verification.py": "Accepted registered native/atlas/preimage getter for seven exact inputs; all reference arithmetic unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/finite_covariance_capture.py": "Accepted SourceCapsule finite152 members and historical539 provenance; native tensor/count/covariance checks unchanged.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/source_layout_adoption.py": "Accepted exact Git API witnesses with true two-argument API contract; source-layout member accounting physical, no copied163 packet.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/render.py": "Structured scientific evidence comments remain, ordinary authored-body comment hashes retired; current semantic qualification validates evidence.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/scientific_limits.py": "Accepted schema2 structured scientific qualification authority; nine scientific fields and structured evidence checks retained, ordinary authored-body hashes retired.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/scientific_routes.py": "Accepted explicit reader_dispositions and individual qualification checks; retired private field register is not authority.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/source.py": "Import split only after documentation removal; no function body changes.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/archaeology/native_lead_support/producer.py": "Exact RAÄ historical hash-only old field-metadata witness; unchanged three protocol keys/five lead selection, no parse/current authority.",
    "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/source_completion/method_certification/native_r_comparison.py": "Current physical ownership counts and output-only old reader witnesses; all numerical/native producer admission stays strict.",
}

MIXED_CUSTODY_READER_SOURCES = frozenset(
    (
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/diagnostics_verification.py",
        "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/lra_validation/native_reference/finite_covariance_capture.py",
    )
)

HISTORICAL_CUSTODY_READER_SOURCES = frozenset(CUSTODY_READER_CONTRACTS)


def _unique_function(tree: ast.Module, name: str) -> ast.FunctionDef:
    """Locate one explicitly named numerical or native predicate owner."""
    found = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    if len(found) != 1:
        raise ReportRebuildError(
            "Named scientific function is absent or duplicated: " + name
        )
    return found[0]


def _native_if_contracts(old: ast.FunctionDef, current: ast.FunctionDef) -> None:
    """Preserve nine entire original native predicate blocks without clause stripping."""
    messages = (
        "Actual finite covariance native execution scope differs",
        "Reviewed committed scientific source custody required",
        "Exact native numeric/raw membership differs",
        "Exact execution custody evidence required",
        "Actual terminal or before/after custody differs",
        "Actual native command receipt differs",
        "Exact locked native archive population differs",
        "Cached source provenance differs",
        "Original R certificate changed",
    )

    def guarded(tree: ast.FunctionDef, message: str) -> ast.If:
        found = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.If):
                continue
            for statement in node.body:
                if (
                    isinstance(statement, ast.Raise)
                    and isinstance(statement.exc, ast.Call)
                    and statement.exc.args
                    and isinstance(statement.exc.args[0], ast.Constant)
                    and statement.exc.args[0].value == message
                ):
                    found.append(node)
        if len(found) != 1:
            raise ReportRebuildError("Named native predicate is absent or duplicated")
        return found[0]

    for message in messages:
        if ast.dump(guarded(old, message), include_attributes=False) != ast.dump(
            guarded(current, message), include_attributes=False
        ):
            raise ReportRebuildError("Original native predicate differs: " + message)


def _mixed_custody_contract(name: str, captured: bytes, current: bytes) -> None:
    """Enforce named mathematics and the one declared mixed source-read seam."""
    if name not in MIXED_CUSTODY_READER_SOURCES:
        return
    try:
        old = ast.parse(captured.decode("utf-8"), type_comments=True)
        new = ast.parse(current.decode("utf-8"), type_comments=True)
    except (SyntaxError, UnicodeError, ValueError) as error:
        raise ReportRebuildError("Mixed custody source cannot be parsed") from error
    anchors: tuple[str, ...]
    if name.endswith("/diagnostics.py"):
        anchors = ("vector_diagnostics", "_csv_vector", "_number")
        original_function = _unique_function(old, "build_diagnostics")
        current_function = _unique_function(new, "build_diagnostics")
        before = ast.get_source_segment(captured.decode("utf-8"), original_function)
        after = ast.get_source_segment(current.decode("utf-8"), current_function)
        declared_old = "        if hashlib.sha256((repository / relative).read_bytes()).hexdigest() != digest:"
        declared_new = "        body = (\n            capture.read_input(relative)\n            if relative in capture.input_sha256\n            else _file(repository, relative)\n        )\n        if hashlib.sha256(body).hexdigest() != digest:"
        if (
            before is None
            or after is None
            or before.count(declared_old) != 1
            or after.count(declared_new) != 1
            or after.replace(declared_new, declared_old) != before
        ):
            raise ReportRebuildError(
                "Diagnostics differs beyond the declared source-read seam"
            )
    elif name.endswith("/diagnostics_verification.py"):
        anchors = ("verify_metrics", "verify", "_npy", "_same", "_encoded")
    else:
        anchors = ()
        _native_if_contracts(
            _unique_function(old, "validated_finite_covariance_capture"),
            _unique_function(new, "_validated_finite_covariance_capture"),
        )
    for anchor in anchors:
        if ast.dump(
            _unique_function(old, anchor), include_attributes=False
        ) != ast.dump(_unique_function(new, anchor), include_attributes=False):
            raise ReportRebuildError("Named numerical function differs: " + anchor)


def _historical_custody_source_role(
    repository: Path,
    historical: JsonObject,
    captured: bytes,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject | None:
    """Retain exact old IO witnesses; current validators have separate qualification."""
    name = historical.get("path")
    if name not in HISTORICAL_CUSTODY_READER_SOURCES:
        return None
    if logical not in source_buffer.detached or not logical.endswith("/" + str(name)):
        raise ReportRebuildError("Historical custody source binding differs")
    current = _regular_confined_file(repository, str(name), "current custody reader")
    if current.stat().st_nlink != 1:
        raise ReportRebuildError("Current custody counterpart must be single-link")
    if name in MIXED_CUSTODY_READER_SOURCES:
        if current.stat().st_size > 1024**2:
            raise ReportRebuildError("Mixed custody source exceeds bound")
        _mixed_custody_contract(str(name), captured, current.read_bytes())
    return {
        "path": name,
        "classification": "historical_custody_reader_metadata",
        "scope": CUSTODY_READER_CONTRACTS[str(name)],
        "current_maintained_validator_requires_separate_qualification": True,
        "whole_current_software_equal_old_execution_claimed": False,
        "native_execution_claimed": False,
        "mixed_numeric_predicates_enforced": name in MIXED_CUSTODY_READER_SOURCES,
    }


SWEDISH_REFERENCE_READER_SOURCE = "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/ci/report_rebuild/scientific_captures/swedish_static_basin.py"
_SWEDISH_REFERENCE_READER_SHA256 = (
    "28533911e5bbe0d337b32667e8db442d46be112db939ebfb488a13fee7152fc8"
)
_SWEDISH_REFERENCE_READER_BYTES = 8351
_SWEDISH_REFERENCE_READER_SPANS = (
    (
        b"""# does not run a model, renderer, observation capture or qualified review again.
CAPTURE_PINS = {
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/assumptions/source-reconciliation.json": "c88355fa3ad588e91261f6906884e2d68fe6968dc6f1aa4eccb36ae04b94cb6e",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/actual-runs.json": "7f063989a7a33f7deae9b46733eb967150405bfe5357579c2c6f3ad19638efcf",
""",
        b"""# does not run a model, renderer, observation capture or qualified review again.
CAPTURE_PINS = {
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/independent-r-reference.json": "e598482f99f8c3ecebc5544da04df2b7196a94509224423515422e5cd96b6f98",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/assumptions/source-reconciliation.json": "c88355fa3ad588e91261f6906884e2d68fe6968dc6f1aa4eccb36ae04b94cb6e",
    "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/actual-runs.json": "7f063989a7a33f7deae9b46733eb967150405bfe5357579c2c6f3ad19638efcf",
""",
    ),
    (
        b"""    "pollen-reconstruction/swedish-static-basin-scenarios/figure-native-capture": [
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/figures/panel-comparison.png"
    ],
}
""",
        b"""    "pollen-reconstruction/swedish-static-basin-scenarios/figure-native-capture": [
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/figures/panel-comparison.png"
    ],
    "pollen-reconstruction/swedish-static-basin-scenarios/native-r-reference-account": [
        "docs/report/pollen-reconstruction/swedish-static-basin-scenarios/execution/independent-r-reference.json"
    ],
}
""",
    ),
    (
        b"""        "paths": [entry.path for entry in accepted],
        "source_scope": (
            "Eight exact immutable JSON source/decision captures and one actual native PNG, "
            "maintained-producer, import-observation, figure and independent "
            "mathematical review projections. Actual original candidate/source/"
            "native receipt authority remains in each bound source record. "
            "Current custody does not repeat any numerical computation or "
            "confer new scientific review, source rights, R parity, historical "
""",
        b"""        "paths": [entry.path for entry in accepted],
        "source_scope": (
            "Eight original immutable JSON source/decision captures, one actual native PNG and "
            "one separately admitted independent R numerical-reference summary, "
            "maintained-producer, import-observation, figure and independent "
            "mathematical review projections. Actual original candidate/source/"
            "native receipt authority remains in each bound source record. "
            "The summary retains saved1988/exportdb2/execution6763 plus declared overlays/"
            "canonicald670 source identities; publication transport is a later epoch. "
            "Current custody does not repeat any numerical computation or "
            "confer new scientific review, source rights, R parity, historical "
""",
    ),
)


def swedish_reference_reader_extension_matches(
    historical: bytes, current: bytes
) -> bool:
    """Reverse exactly three reviewed metadata edits to recover the full old reader."""
    if (
        len(historical) != _SWEDISH_REFERENCE_READER_BYTES
        or hashlib.sha256(historical).hexdigest() != _SWEDISH_REFERENCE_READER_SHA256
        or not 0 < len(current) <= 16 * 1024
    ):
        return False
    restored = current
    for old, new in _SWEDISH_REFERENCE_READER_SPANS:
        if historical.count(old) != 1 or restored.count(new) != 1:
            return False
        restored = restored.replace(new, old, 1)
    return restored == historical


def validated_swedish_reference_reader_source(
    repository: Path,
    historical: JsonObject,
    logical: str,
    source_buffer: SourceCapsule,
) -> JsonObject:
    """Bind the additional retained reference to its one original optimizer context."""
    name = SWEDISH_REFERENCE_READER_SOURCE
    expected = {
        "sha256": _SWEDISH_REFERENCE_READER_SHA256,
        "bytes": _SWEDISH_REFERENCE_READER_BYTES,
    }
    if (
        repository != repository.resolve()
        or source_buffer.repository != repository
        or source_buffer.prefix
        != "data/method-certification/author-optimizer-diagnostic-source-capture"
        or source_buffer.descriptor.capture.get("sha256")
        != "f865795aac7585e56c4cf44faac84496d339e1c176fc6ee111cba3cbc9b4ce93"
        or set(historical) != {"path", "sha256", "bytes"}
        or type(historical.get("bytes")) is not int
        or historical != {"path": name, **expected}
        or logical != "executions/optimizer-diagnostics/first-party-inputs/" + name
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
        raise ReportRebuildError("Swedish reference reader source binding differs")
    source_buffer.fresh()
    captured = source_buffer.read_source(logical)
    path = _regular_confined_file(repository, name, "current Swedish reference reader")
    before = path.stat()
    if before.st_nlink != 1 or not 0 < before.st_size <= 16 * 1024:
        raise ReportRebuildError("Swedish reference reader must be bounded single-link")
    current = path.read_bytes()
    if not swedish_reference_reader_extension_matches(captured, current):
        raise ReportRebuildError(
            "Swedish reference reader differs beyond its three metadata edits"
        )
    source_buffer.fresh()
    again = _regular_confined_file(repository, name, "current Swedish reference reader")
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
        any(getattr(before, key) != getattr(after, key) for key in fields)
        or again.read_bytes() != current
    ):
        raise ReportRebuildError("Swedish reference reader changed during verification")
    return {
        "path": name,
        "classification": "finite_swedish_reference_reader_extension",
        "original_member": logical,
        "original_sha256": _SWEDISH_REFERENCE_READER_SHA256,
        "original_bytes": _SWEDISH_REFERENCE_READER_BYTES,
        "whole_old_reader_reconstructed": True,
        "original_nine_capture_pins_preserved": True,
        "current_additional_reference_record_requires_separate_qualification": True,
        "current_native_or_numerical_equivalence_claimed": False,
        "scope": "Only the independent-reference capture pin, owning publication path and source-scope explanation change. Original JSON/PNG pins and all native/control predicates reconstruct exactly. The current ten-record retained reader is qualified separately; the old optimizer source/native epochs and output values remain literal. No R, model or new scientific execution is admitted.",
    }
