"""Separate historical reader IO from unchanged numerical and native predicates."""

from __future__ import annotations

import ast
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
