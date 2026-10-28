"""Reconcile retained paper PDFs with canonical sources and model layout review."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any

from bijux_pollenomics_dev.ci.report_rebuild.retained_source import source_revision

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_bytes(revision: str, relative: str) -> bytes:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Invalid source revision")
    result = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "show",
            f"{source_revision(ROOT, revision)}:{relative}",
        ],
        cwd=ROOT,
        capture_output=True,
        check=True,
        timeout=10,
    )
    return result.stdout


def committed_digest(revision: str, relative: str) -> str:
    return hashlib.sha256(committed_bytes(revision, relative)).hexdigest()


def exported_content(source: bytes) -> bytes:
    """Remove only historical metadata lines suppressed by the paper renderer."""
    return re.sub(
        rb"^<!-- scientific-(?:claim-semantic|authored-source)-sha256: "
        rb"[0-9a-f]{64} -->\n",
        b"",
        source,
        flags=re.MULTILINE,
    )


def verify_producer(manifest: dict[str, Any], paper: dict[str, Any]) -> None:
    """Verify the historical renderer that actually made each retained export."""
    override = {"producer_revision", "producer_sha256"} & paper.keys()
    if override and override != {"producer_revision", "producer_sha256"}:
        raise ValueError("A separately produced paper needs complete producer identity")
    revision = paper.get("producer_revision", manifest["producer_revision"])
    records = paper.get("producer_sha256", manifest["producer_sha256"])
    if (
        not isinstance(revision, str)
        or not re.fullmatch(r"[0-9a-f]{40}", revision)
        or not isinstance(records, dict)
        or not records
        or set(records) != set(manifest["producer_sha256"])
    ):
        raise ValueError("A paper needs its complete exact historical producer closure")
    accepted = subprocess.run(
        [
            "git",
            "--no-replace-objects",
            "merge-base",
            "--is-ancestor",
            source_revision(ROOT, revision),
            "HEAD",
        ],
        cwd=ROOT,
        capture_output=True,
        check=False,
        timeout=10,
    )
    if accepted.returncode:
        raise ValueError(
            "Paper producer revision is absent from accepted source history"
        )
    for relative, expected in records.items():
        if (
            not isinstance(relative, str)
            or not relative.startswith(
                "packages/bijux-pollenomics-dev/src/bijux_pollenomics_dev/reader_reports/"
            )
            or ".." in Path(relative).parts
            or not isinstance(expected, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or committed_digest(revision, relative) != expected
        ):
            raise ValueError(f"Historical export producer changed: {relative}")


def main() -> None:
    manifest = json.loads((HERE / "manifest.json").read_text())
    review = json.loads((HERE / "visual-review.json").read_text())
    if manifest["schema_version"] != "canonical-paper-pdf-library.v1":
        raise ValueError("Unexpected PDF library schema")
    inventory_path = ROOT / manifest["inventory"]
    if digest(inventory_path) != manifest["inventory_sha256"]:
        raise ValueError("Canonical paper inventory changed; rebuild affected PDFs")
    if (
        committed_digest(manifest["repository_revision"], manifest["inventory"])
        != manifest["inventory_sha256"]
    ):
        raise ValueError("Inventory is not bound to the exported source revision")
    inventory = list(csv.DictReader(inventory_path.read_text().splitlines()))
    papers = {row["paper_id"]: row for row in manifest["papers"]}
    reviews = {row["paper_id"]: row for row in review["papers"]}
    ids = {row["paper_id"] for row in inventory}
    if (
        len(papers) != len(manifest["papers"])
        or set(papers) != ids
        or set(reviews) != ids
    ):
        raise ValueError("PDF, review and canonical paper populations differ")
    if review["overall_status"] != "layout_pass" or review["defects"]:
        raise ValueError("PDF layout review retains an unresolved defect")
    if review["input_receipt_sha256"] != manifest["build_receipt_sha256"]:
        raise ValueError("Visual review belongs to a different export")
    expected_pdfs = {HERE / row["pdf"] for row in papers.values()}
    if set(HERE.glob("*.pdf")) != expected_pdfs:
        raise ValueError("Retained PDF inventory differs")
    for original in inventory:
        row = papers[original["paper_id"]]
        visual = reviews[original["paper_id"]]
        if row["canonical_report"] != original["canonical_report"]:
            raise ValueError("PDF points to a different canonical account")
        source = ROOT / row["canonical_report"]
        source_revision = row.get("source_revision", manifest["repository_revision"])
        if "source_revision" in row and "build_receipt_sha256" not in row:
            raise ValueError("A separately exported paper needs its build receipt")
        receipt_sha256 = row.get(
            "build_receipt_sha256", manifest["build_receipt_sha256"]
        )
        if not re.fullmatch(r"[0-9a-f]{64}", receipt_sha256):
            raise ValueError("Invalid paper build receipt identity")
        if (
            visual.get("input_receipt_sha256", review["input_receipt_sha256"])
            != receipt_sha256
            or visual.get("source_revision", review["repository_revision"])
            != source_revision
        ):
            raise ValueError("Paper layout review belongs to another export revision")
        historical_source = committed_bytes(source_revision, row["canonical_report"])
        if hashlib.sha256(historical_source).hexdigest() != row[
            "source_sha256"
        ] or source.read_bytes() != exported_content(historical_source):
            raise ValueError(f"Canonical report changed: {source}")
        pdf = HERE / row["pdf"]
        if digest(pdf) != row["pdf_sha256"] or pdf.stat().st_size != row["pdf_bytes"]:
            raise ValueError(f"Retained PDF changed: {pdf.name}")
        if (
            visual["input_pdf_sha256"] != row["pdf_sha256"]
            or visual["source_sha256"] != row["source_sha256"]
        ):
            raise ValueError("Visual review belongs to different PDF/source bytes")
        if visual["review_status"] != "layout_pass" or not visual["all_fonts_embedded"]:
            raise ValueError("PDF visual/font acceptance missing")
        if [page["page"] for page in visual["pages"]] != list(
            range(1, visual["page_count"] + 1)
        ):
            raise ValueError("Page-by-page review is incomplete")
        if any(page["visual_status"] != "readable" for page in visual["pages"]):
            raise ValueError("A PDF page is not accepted for layout")
        verify_producer(manifest, row)
    print(
        f"verified {len(papers)} standalone paper PDFs and their source/layout identities"
    )


if __name__ == "__main__":
    main()
