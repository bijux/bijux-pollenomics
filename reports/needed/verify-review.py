"""Check scientific review questions without conferring review authority."""

from __future__ import annotations

import csv
from datetime import date
import hashlib
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[2]
DECISIONS = {
    "not_received",
    "accepted_scoped",
    "accepted_with_conditions",
    "refused",
    "deferred_for_source",
}
FIELDS = {
    "review_id",
    "claim_report_paths",
    "claim_report_sha256",
    "claim_scope",
    "supporting_material_paths",
    "supporting_material_sha256",
    "source_request_ids",
    "required_source_role",
    "qualified_reviewer_role",
    "qualification_and_independence",
    "precise_review_question",
    "decision_scope",
    "admission_consumer_paths",
    "unresolved_consequence",
    "reopening_trigger",
    "reviewer_assignment",
    "review_decision",
    "decision_date",
    "decision_evidence_path",
    "claim_register_sha256",
    "source_request_register_sha256",
}


def _file(root: Path, relative: str) -> Path:
    native = PurePosixPath(relative)
    path = root / relative
    if (
        native.is_absolute()
        or ".." in native.parts
        or not path.is_file()
        or not path.resolve().is_relative_to(root.resolve())
    ):
        raise ValueError(f"Scientific review material unavailable: {relative}")
    return path


def validate(root: Path, rows: list[dict[str, str]], packet_ids: set[str]) -> None:
    """Validate version and record fields; qualifications require human review."""
    ids = {r["review_id"] for r in rows}
    if not rows or len(ids) != len(rows):
        raise ValueError("Scientific review IDs are empty or duplicated")
    covered = set()
    for row in rows:
        if set(row) != FIELDS or not all(
            isinstance(v, str) and v.strip() for v in row.values()
        ):
            raise ValueError("Scientific review fields are incomplete")
        for field, register in (
            ("claim_register_sha256", "reports/needed/report-claims.csv"),
            ("source_request_register_sha256", "reports/needed/source-requests.csv"),
        ):
            if (
                hashlib.sha256(_file(root, register).read_bytes()).hexdigest()
                != row[field]
            ):
                raise ValueError("Scientific review register changed")
        for paths, hashes in (
            ("claim_report_paths", "claim_report_sha256"),
            ("supporting_material_paths", "supporting_material_sha256"),
        ):
            for relative, digest in zip(
                row[paths].split(";"), row[hashes].split(";"), strict=True
            ):
                if (
                    hashlib.sha256(_file(root, relative).read_bytes()).hexdigest()
                    != digest
                ):
                    raise ValueError(f"Scientific review source changed: {relative}")
        for relative in row["admission_consumer_paths"].split(";"):
            _file(root, relative)
        if row["source_request_ids"] != "none":
            covered.update(row["source_request_ids"].split(";"))
        decision = row["review_decision"]
        if decision not in DECISIONS:
            raise ValueError("Unknown scientific review decision")
        if decision == "not_received":
            if (
                row["decision_date"] != "none"
                or row["decision_evidence_path"] != "none"
            ):
                raise ValueError("Unreceived scientific review has decision evidence")
        else:
            if row["reviewer_assignment"] in {"none", "unassigned"}:
                raise ValueError("Received scientific review has no reviewer")
            date.fromisoformat(row["decision_date"])
            _file(root, row["decision_evidence_path"])
    if covered != packet_ids:
        raise ValueError("Scientific review source-request coverage differs")


def main() -> None:
    with (ROOT / "reports/needed/scientific-review.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (ROOT / "reports/needed/source-requests.csv").open(newline="") as handle:
        packets = {r["packet_id"] for r in csv.DictReader(handle)}
    validate(ROOT, rows, packets)
    received = sum(r["review_decision"] != "not_received" for r in rows)
    print(
        f"verified {len(rows)} scientific review questions; {received} received records"
    )


if __name__ == "__main__":
    main()
