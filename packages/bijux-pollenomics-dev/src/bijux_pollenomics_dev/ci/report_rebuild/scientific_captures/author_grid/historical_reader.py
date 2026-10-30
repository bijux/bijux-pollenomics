"""Authenticate the original author-grid reader without admitting it as current input."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import posixpath
import re
from typing import Any
from urllib.parse import quote

from ...contracts import JsonObject
from .transport import file, object_value, require, typed

FAMILY = "docs/report/publication-replay/landclim-author-example-correspondence/"


def historical_reader_scope(
    packet: Path, members: dict[str, JsonObject], raw: bytes, published: bytes
) -> str:
    """Authenticate the sealed schema-one authority and its original hash-bearing footer."""
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
        BEGIN,
        END,
    )

    name = "publication/scientific_accounts.json"
    authority = file(packet, name).read_bytes()
    identity = members[name]
    require(
        len(authority) == identity["bytes"]
        and hashlib.sha256(authority).hexdigest() == identity["sha256"],
        "Author-grid historical reading authority identity differs",
    )
    document = object_value(json.loads(authority))
    typed(document["schema_version"], 1)
    rows = document["routes"]
    require(isinstance(rows, list), "Author-grid historical routes are absent")
    assert isinstance(rows, list)
    selected = [r for r in rows if r.get("reader_path") == FAMILY + "REPORT.md"]
    require(len(selected) == 1, "Author-grid historical REPORT route is ambiguous")
    original = selected[0]
    qualification = object_value(original["qualification"])
    require(
        set(qualification) == {"authored_reader_sha256", "fields", "evidence_pins"}
        and qualification["authored_reader_sha256"] == hashlib.sha256(raw).hexdigest(),
        "Author-grid historical authored-reader identity differs",
    )
    accounts = original["canonical_accounts"]
    require(
        isinstance(accounts, list)
        and all(
            isinstance(row, dict)
            and set(row) == {"report_path", "source_sha256"}
            and isinstance(row["source_sha256"], str)
            and re.fullmatch(r"[0-9a-f]{64}", row["source_sha256"])
            for row in accounts
        ),
        "Author-grid historical account identities differ",
    )
    # Interpret only this authenticated historical record. The maintained reader
    # remains schema two and never admits old authority documents as current input.
    route = _captured_reading_routes(authority.decode())[FAMILY + "REPORT.md"]
    assert route.qualification is not None
    lines = ["## Scientific verification and limits", "", route.scope_reason, ""]
    for label, text in route.qualification.fields:
        lines.extend((f"**{label}.** {text}", ""))
    lines.extend(
        (
            "Qualified authored reader SHA-256: "
            f"`{qualification['authored_reader_sha256']}`.",
            "",
        )
    )
    for record, original_pin in zip(
        route.qualification.evidence, qualification["evidence_pins"], strict=True
    ):
        require(record.path == original_pin["path"], "Historical evidence path differs")
        expected_digest = original_pin["sha256"]
        require(
            isinstance(expected_digest, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_digest) is not None,
            "Author-grid historical evidence is unbound",
        )
        target = (
            "https://github.com/bijux/bijux-pollenomics/blob/main/"
            + quote(record.path, safe="/")
            if record.path.startswith("reports/science/")
            else posixpath.relpath(record.path, posixpath.dirname(route.reader_path))
        )
        lines.extend(
            (
                f"- [Retained qualification evidence: {record.path}]({target}) "
                f"(SHA-256 `{expected_digest}`).",
                "",
            )
        )
    for account in accounts:
        target = (
            "https://github.com/bijux/bijux-pollenomics/blob/main/"
            + quote(account["report_path"], safe="/")
            if account["report_path"].startswith("reports/science/")
            else posixpath.relpath(
                account["report_path"], posixpath.dirname(route.reader_path)
            )
        )
        lines.extend(
            (
                f"- [Canonical scientific account: {account['report_path']}]({target}) "
                f"(source SHA-256 `{account['source_sha256']}`).",
                "",
            )
        )
    lines.append(
        "JSON and CSV retain their domain source and numerical manifests; "
        "a reading route does not rerun those producers. PDF exports retain "
        "their export inventory and source pins and must be regenerated "
        "when their canonical account changes."
    )
    require(
        published == raw + (BEGIN + "\n".join(lines) + "\n" + END).encode(),
        "Author-grid original managed REPORT footer differs",
    )
    return route.scope_reason


def _captured_reading_routes(raw: str) -> dict[str, Any]:
    """Parse sealed historical reading authority without restoring prose hash gates."""
    from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
        parse_routes,
    )

    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, value in pairs:
            require(
                key not in result, "Author-grid original authority duplicates a field"
            )
            result[key] = value
        return result

    def body_hash(value: object) -> bool:
        return (
            isinstance(value, str)
            and len(value) == 64
            and all(character in "0123456789abcdef" for character in value)
        )

    value = json.loads(raw, object_pairs_hook=unique)
    require(
        isinstance(value, dict)
        and set(value) == {"schema_version", "routes"}
        and type(value["schema_version"]) is int
        and value["schema_version"] == 1
        and isinstance(value["routes"], list),
        "Author-grid original reading authority schema differs",
    )
    for route in value["routes"]:
        require(
            isinstance(route, dict)
            and {"reader_path", "canonical_accounts", "scope_reason"} <= set(route)
            and set(route)
            <= {"reader_path", "canonical_accounts", "scope_reason", "qualification"},
            "Author-grid original route fields differ",
        )
        for account in route["canonical_accounts"]:
            require(
                isinstance(account, dict)
                and set(account) == {"report_path", "source_sha256"}
                and body_hash(account["source_sha256"]),
                "Author-grid original account fields differ",
            )
        qualification = route.get("qualification")
        if qualification is not None:
            require(
                isinstance(qualification, dict)
                and set(qualification)
                == {"authored_reader_sha256", "fields", "evidence_pins"}
                and body_hash(qualification["authored_reader_sha256"]),
                "Author-grid original qualification fields differ",
            )
            for evidence in qualification["evidence_pins"]:
                require(
                    isinstance(evidence, dict)
                    and set(evidence) == {"path", "sha256"}
                    and body_hash(evidence["sha256"]),
                    "Author-grid original evidence fields differ",
                )
    projected = copy.deepcopy(value)
    projected["schema_version"] = 2
    for route in projected["routes"]:
        for account in route["canonical_accounts"]:
            account.pop("source_sha256", None)
        qualification = route.get("qualification")
        if qualification is not None:
            qualification.pop("authored_reader_sha256", None)
            for evidence in qualification.get("evidence_pins", []):
                if Path(evidence["path"]).suffix.lower() in {".md", ".py", ".tex"}:
                    evidence.pop("sha256", None)
    return parse_routes(json.dumps(projected))
