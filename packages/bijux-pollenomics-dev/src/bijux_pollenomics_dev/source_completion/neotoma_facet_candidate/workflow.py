"""Read-only reconciliation of pinned candidate and selected source evidence."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from bijux_pollenomics.core.filesystem import read_regular_file

from .comparison import reconcile
from .private_output import write_private_receipt
from .source_inputs import verify_source_inputs
from .static_details import decode_details


@dataclass(frozen=True)
class PinnedInput:
    """A caller-selected file and its independently supplied digest."""

    path: Path
    sha256: str


@dataclass(frozen=True)
class AuditInputs:
    """Exact candidate, source declaration and selected cohort identities."""

    candidate_root: Path
    capsule_root: Path
    producer: PinnedInput
    producer_supervisor: PinnedInput
    asset_audit: PinnedInput
    source_comparison: PinnedInput
    source_comparison_supervisor: PinnedInput
    selection: PinnedInput
    source_declarations: PinnedInput
    source_supervisor: PinnedInput
    expected_source_revision: str
    expected_comparison_reference_sha256: str
    expected_comparison_reference_receipt_sha256: str
    expected_comparison_reference_supervisor_sha256: str
    expected_sites: int
    expected_datasets: int
    expected_selected: int


def _held(source: PinnedInput) -> bytes:
    if (
        not isinstance(source.sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", source.sha256) is None
    ):
        raise ValueError("Audit input identity is malformed")
    data = read_regular_file(source.path, max_bytes=32 * 1024**2)
    if sha256(data).hexdigest() != source.sha256:
        raise ValueError("Audit input digest differs")
    return data


def _object(raw: bytes) -> dict[str, Any]:
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ValueError("Audit input JSON is not an object")
    return value


def audit_candidate(inputs: AuditInputs) -> dict[str, Any]:
    """Return private identity reconciliation without publishing source bodies.

    The selected declarations are a pinned prior typed-owner result, not a live
    replay. Comparison reference identities are checked against the pinned
    comparison receipt; reference bytes are not revalidated here. Locally pinned
    receipts and source buffers do not attest execution, rights, an atomic
    snapshot, original acquisition or scientific admission.
    """
    if (
        not isinstance(inputs.expected_source_revision, str)
        or re.fullmatch(r"[0-9a-f]{40}", inputs.expected_source_revision) is None
    ):
        raise ValueError("Expected source revision is malformed")
    if any(
        not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None
        for value in (
            inputs.expected_comparison_reference_sha256,
            inputs.expected_comparison_reference_receipt_sha256,
            inputs.expected_comparison_reference_supervisor_sha256,
        )
    ):
        raise ValueError("Comparison reference identities are malformed")
    sources = (
        inputs.producer,
        inputs.producer_supervisor,
        inputs.asset_audit,
        inputs.source_comparison,
        inputs.source_comparison_supervisor,
        inputs.selection,
        inputs.source_declarations,
        inputs.source_supervisor,
    )
    buffers = [_held(source) for source in sources]
    (
        producer,
        supervisor,
        assets,
        comparison,
        comparison_supervisor,
        selection,
        declarations,
        source_supervisor,
    ) = map(_object, buffers)
    if (
        producer.get("status") != "producer_returned"
        or supervisor.get("status") != "completed"
        or type(supervisor.get("exit_code")) is not int
        or supervisor.get("exit_code") != 0
        or supervisor.get("timed_out") is not False
        or supervisor.get("producer_receipt_sha256") != inputs.producer.sha256
        or assets.get("status") != "PASS"
        or assets.get("producer_receipt_sha256") != inputs.producer.sha256
        or assets.get("supervisor_receipt_sha256") != inputs.producer_supervisor.sha256
        or comparison.get("status") != "PASS"
        or comparison.get("producer_receipt_sha256") != inputs.producer.sha256
        or comparison.get("supervisor_receipt_sha256")
        != inputs.producer_supervisor.sha256
        or comparison.get("asset_receipt_sha256") != inputs.asset_audit.sha256
        or comparison.get("reference_sha256")
        != inputs.expected_comparison_reference_sha256
        or comparison.get("reference_receipt_sha256")
        != inputs.expected_comparison_reference_receipt_sha256
        or comparison.get("reference_supervisor_sha256")
        != inputs.expected_comparison_reference_supervisor_sha256
        or type(comparison.get("sites")) is not int
        or comparison.get("sites") != inputs.expected_sites
        or type(comparison.get("datasets")) is not int
        or comparison.get("datasets") != inputs.expected_datasets
        or comparison_supervisor.get("status") != "completed"
        or type(comparison_supervisor.get("exit_code")) is not int
        or comparison_supervisor.get("exit_code") != 0
        or comparison_supervisor.get("timed_out") is not False
        or comparison_supervisor.get("verification_receipt_sha256")
        != inputs.source_comparison.sha256
    ):
        raise ValueError("Candidate receipt linkage differs")
    if (
        selection.get("status") != "PASS"
        or declarations.get("status") != "PASS"
        or declarations.get("source_revision") != inputs.expected_source_revision
        or declarations.get("inventory_sha256") != inputs.selection.sha256
        or declarations.get("declaration_profile")
        != "neotoma-scoped-facet-declarations.v1"
        or source_supervisor.get("status") != "completed"
        or type(source_supervisor.get("exit_code")) is not int
        or source_supervisor.get("exit_code") != 0
        or source_supervisor.get("timed_out") is not False
        or source_supervisor.get("experiment_receipt_sha256")
        != inputs.source_declarations.sha256
    ):
        raise ValueError("Selected source receipt linkage differs")
    files = producer.get("output_files")
    selected, source_rows = selection.get("selected"), declarations.get("selected")
    if (
        not isinstance(files, dict)
        or assets.get("document_sha256") != files.get("nordic_map.html")
        or not isinstance(selected, list)
        or not isinstance(source_rows, list)
    ):
        raise ValueError("Audit input populations differ")
    build, records = decode_details(inputs.candidate_root, files)
    if (
        assets.get("candidate_build") != build
        or comparison.get("candidate_build") != build
    ):
        raise ValueError("Candidate build identity differs")
    rows = reconcile(
        records,
        selected,
        source_rows,
        expected_sites=inputs.expected_sites,
        expected_datasets=inputs.expected_datasets,
        expected_selected=inputs.expected_selected,
    )
    verify_source_inputs(inputs.capsule_root, selected, source_rows)
    build_after, records_after = decode_details(inputs.candidate_root, files)
    if build_after != build or json.dumps(
        records,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ) != json.dumps(
        records_after,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ):
        raise ValueError("Candidate details changed during audit")
    verify_source_inputs(inputs.capsule_root, selected, source_rows)
    if any(_held(source) != raw for source, raw in zip(sources, buffers, strict=True)):
        raise ValueError("Audit input changed during reconciliation")
    return {
        "schema_version": "neotoma-facet-candidate-reconciliation.v1",
        "status": "PASS",
        "publication_allowed": False,
        "candidate_build": build,
        "candidate_producer_sha256": inputs.producer.sha256,
        "candidate_supervisor_sha256": inputs.producer_supervisor.sha256,
        "asset_audit_sha256": inputs.asset_audit.sha256,
        "source_comparison_sha256": inputs.source_comparison.sha256,
        "source_comparison_supervisor_sha256": inputs.source_comparison_supervisor.sha256,
        "selection_sha256": inputs.selection.sha256,
        "source_declarations_sha256": inputs.source_declarations.sha256,
        "source_supervisor_sha256": inputs.source_supervisor.sha256,
        "source_revision": inputs.expected_source_revision,
        "scope": "private selected identity evidence only; no publication authorization, scientific admission, atomicity or independent execution attestation",
        "selected": rows,
    }


def audit_to_private_receipt(inputs: AuditInputs, output: Path) -> None:
    """Run complete reconciliation before exclusively attaching private output."""
    output = Path(output).absolute()
    parent = output.parent.resolve(strict=True)
    if any(
        parent.is_relative_to(root.resolve(strict=True))
        for root in (inputs.candidate_root, inputs.capsule_root)
    ) or any(
        parent.is_relative_to(item.path.parent.resolve(strict=True))
        for item in (
            inputs.producer,
            inputs.producer_supervisor,
            inputs.asset_audit,
            inputs.source_comparison,
            inputs.source_comparison_supervisor,
            inputs.selection,
            inputs.source_declarations,
            inputs.source_supervisor,
        )
    ):
        raise ValueError("Private receipt must be outside input directories")
    write_private_receipt(output, audit_candidate(inputs))
