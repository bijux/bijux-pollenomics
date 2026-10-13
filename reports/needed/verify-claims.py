"""Keep scientific claim accounting bound to its exact report population."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path, PurePosixPath

from bijux_pollenomics_dev.reader_reports.scientific_limits import validate_report
from bijux_pollenomics_dev.reader_reports.scientific_routes import (
    validate_reader_routes,
)

ROOT = Path(__file__).resolve().parents[2]
CATEGORIES = {
    "data",
    "assumption",
    "algorithm/numerical",
    "comparability",
    "access/rights",
    "qualified review",
    "none within stated scope",
}
FIELDS = {
    "report_path",
    "cause_categories",
    "concrete_reason",
    "retained_evidence_paths",
    "existing_consumer_paths",
    "resolver_role",
    "reopening_trigger",
    "supported_scoped_claim",
    "unsupported_claim",
    "actual_verification_performed",
    "negative_or_refused_result",
    "matched_denominator",
    "consequence",
    "precise_next_acceptance_route",
    "packet_reference",
    "source_report_sha256",
}


def expected_report_paths(root: Path) -> set[str]:
    """Include primary research accounts and explicitly owned public readers."""
    expected = {
        p.relative_to(root).as_posix() for p in (root / "reports/science").rglob("*.md")
    }
    authority = json.loads(
        (root / "reports/needed/claim-account-sources.json").read_text()
    )
    if (
        not isinstance(authority, dict)
        or set(authority) != {"schema_version", "supplemental_report_paths"}
        or authority["schema_version"] != 1
    ):
        raise ValueError("Scientific claim account authority is invalid")
    paths = authority["supplemental_report_paths"]
    if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
        raise ValueError("Scientific supplemental accounts are invalid")
    if len(paths) != len(set(paths)):
        raise ValueError("Scientific supplemental accounts are duplicated")
    for relative in paths:
        native = PurePosixPath(relative)
        local = root / relative
        if (
            native.is_absolute()
            or ".." in native.parts
            or native.parts[:2] != ("docs", "report")
            or native.suffix != ".md"
            or not local.is_file()
            or not local.resolve().is_relative_to(root.resolve())
            or relative in expected
        ):
            raise ValueError(
                "Scientific supplemental account is unavailable or duplicated"
            )
        expected.add(relative)
    return expected


def validate(root: Path, rows: list[dict[str, str]], packet_ids: set[str]) -> None:
    """Check coverage and identities; text review remains a separate judgment."""
    expected = expected_report_paths(root)
    if len(rows) != len(expected) or {r["report_path"] for r in rows} != expected:
        raise ValueError("Scientific claim inventory is missing or duplicated")
    for row in rows:
        if set(row) != FIELDS or not all(
            isinstance(value, str) and value.strip() for value in row.values()
        ):
            raise ValueError("Scientific claim fields are incomplete")
        categories = set(row["cause_categories"].split("|"))
        if not categories <= CATEGORIES or (
            "none within stated scope" in categories and len(categories) != 1
        ):
            raise ValueError("Scientific claim cause category is invalid")
        path = root / row["report_path"]
        if hashlib.sha256(path.read_bytes()).hexdigest() != row["source_report_sha256"]:
            raise ValueError(f"Scientific claim report changed: {row['report_path']}")
        validate_report(path.read_bytes(), row)
        for field in ("retained_evidence_paths", "existing_consumer_paths"):
            for relative in row[field].split(";"):
                native = PurePosixPath(relative)
                local = root / relative
                if (
                    native.is_absolute()
                    or ".." in native.parts
                    or not local.is_file()
                    or not local.resolve().is_relative_to(root.resolve())
                ):
                    raise ValueError(
                        f"Scientific claim evidence unavailable: {relative}"
                    )
        if (
            row["packet_reference"] != "none"
            and not set(row["packet_reference"].split(";")) <= packet_ids
        ):
            raise ValueError("Scientific claim references an unknown request packet")

    validate_reader_routes(root, rows)


def main() -> None:
    with (ROOT / "reports/needed/report-claims.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    with (ROOT / "reports/needed/source-requests.csv").open(newline="") as handle:
        packets = {r["packet_id"] for r in csv.DictReader(handle)}
    validate(ROOT, rows, packets)
    print(f"verified {len(rows)} scoped scientific report claims and source identities")


if __name__ == "__main__":
    main()
