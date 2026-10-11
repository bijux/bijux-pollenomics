"""Reconcile retained paper PDFs with canonical sources and model layout review."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed_digest(revision: str, relative: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("Invalid source revision")
    result = subprocess.run(
        ["git", "show", f"{revision}:{relative}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
        timeout=10,
    )
    return hashlib.sha256(result.stdout).hexdigest()


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
        if (
            digest(source) != row["source_sha256"]
            or committed_digest(source_revision, row["canonical_report"])
            != row["source_sha256"]
        ):
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
    for relative, expected in manifest["producer_sha256"].items():
        if (
            digest(ROOT / relative) != expected
            or committed_digest(manifest["producer_revision"], relative) != expected
        ):
            raise ValueError(f"Export producer changed: {relative}")
    print(
        f"verified {len(papers)} standalone paper PDFs and their source/layout identities"
    )


if __name__ == "__main__":
    main()
