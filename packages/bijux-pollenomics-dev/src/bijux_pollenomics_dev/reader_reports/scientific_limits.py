"""Expose source-bound scientific verification without replacing authored accounts."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import csv
import io
from pathlib import Path
import posixpath

from .source import repository_file, repository_root

BEGIN = "\n\n<!-- scientific-verification-and-limits:begin -->\n"
END = "<!-- scientific-verification-and-limits:end -->\n"
FIELDS = (
    ("Supported claim", "supported_scoped_claim"),
    ("Unsupported claim", "unsupported_claim"),
    ("Actual verification performed", "actual_verification_performed"),
    ("Remaining input or review", "concrete_reason"),
    ("Cause category", "cause_categories"),
    ("Consequence", "consequence"),
    ("Precise next acceptance route", "precise_next_acceptance_route"),
    ("Negative or refused result", "negative_or_refused_result"),
    ("Matched denominator", "matched_denominator"),
)


def authored_bytes(raw: bytes) -> bytes:
    """Remove one terminal owned block; refuse ambiguous or truncated custody."""
    text = raw.decode("utf-8")
    if "scientific-verification-and-limits:" not in text:
        return raw
    if text.count(BEGIN) != 1 or text.count(END) != 1:
        raise ValueError("Scientific limits markers are malformed or duplicated")
    original, block = text.split(BEGIN)
    if not block.endswith(END) or BEGIN in block:
        raise ValueError("Scientific limits block must be terminal")
    return original.encode("utf-8")


def _block(row: Mapping[str, str]) -> bytes:
    lines = ["## Scientific verification and limits", ""]
    for label, key in FIELDS:
        value = row[key]
        if not value.strip() or "scientific-verification-and-limits:" in value:
            raise ValueError("Scientific limits require complete unambiguous claims")
        if key == "concrete_reason":
            value += f" Resolver: {row['resolver_role']} Reopen when: {row['reopening_trigger']}"
        lines.extend((f"**{label}.** {value}", ""))
    parent = posixpath.dirname(row["report_path"])
    paths = row["retained_evidence_paths"].split(";")
    links = ", ".join(f"[{p}]({posixpath.relpath(p, parent)})" for p in paths)
    lines.extend((f"Retained evidence: {links}.", ""))
    lines.extend(
        (
            "This account preserves the verification scope and source limitations; "
            "rendering these statements does not rerun or qualify the underlying science.",
            "",
        )
    )
    return (BEGIN + "\n".join(lines) + "\n" + END).encode("utf-8")


def render_report(raw: bytes, row: Mapping[str, str]) -> bytes:
    """Retain authored prose and render the exact maintained claim fields."""
    base = authored_bytes(raw)
    return base + _block(row)


def validate_report(raw: bytes, row: Mapping[str, str]) -> None:
    """Refuse absent, stale, partial or altered on-page scientific statements."""
    base = authored_bytes(raw)
    if raw != base + _block(row):
        raise ValueError(f"Scientific verification block differs: {row['report_path']}")


def render_accounts(root: Path, output: Path) -> Path:
    """Render maintained limits without pinning ordinary document bodies."""
    root = repository_root(root)
    authority = repository_file(root, "reports/needed/report-claims.csv")
    source_csv = authority.read_bytes()
    reader = csv.DictReader(io.StringIO(source_csv.decode("utf-8")))
    if reader.fieldnames is None:
        raise ValueError("Scientific claim authority has no fields")
    rows = list(reader)
    paths = [row["report_path"] for row in rows]
    if not paths or len(paths) != len(set(paths)):
        raise ValueError("Scientific report population is empty or duplicated")
    prepared: list[tuple[str, bytes]] = []
    for row in rows:
        path = repository_file(root, row["report_path"])
        if path.suffix != ".md":
            raise ValueError("Scientific account must be Markdown")
        raw = path.read_bytes()
        rendered = render_report(raw, row)
        validate_report(rendered, row)
        prepared.append((row["report_path"], rendered))
    if ".." in output.parts:
        raise ValueError("Scientific report output contains parent traversal")
    target = output.absolute()
    artifacts = root / "artifacts"
    if not target.is_relative_to(artifacts) or target == artifacts:
        raise ValueError(
            "Scientific report proposal must belong to repository artifacts"
        )
    current = target
    while current != root:
        if current.is_symlink():
            raise ValueError("Scientific report proposal path contains a symlink")
        current = current.parent
    target = target.resolve(strict=False)
    if not target.is_relative_to(artifacts.resolve(strict=False)):
        raise ValueError("Scientific report output escapes normalized artifacts")
    target.mkdir(parents=True, exist_ok=False)
    for relative, rendered in prepared:
        destination = target / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(rendered)
    return target


def main() -> None:
    """Prepare source-bound report prose in a fresh artifact directory."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(render_accounts(args.repository, args.output))


if __name__ == "__main__":
    main()
