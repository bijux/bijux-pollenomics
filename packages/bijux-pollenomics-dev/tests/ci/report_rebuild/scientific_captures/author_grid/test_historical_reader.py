"""Keep original author-grid footer bytes separate from current reading authority."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from bijux_pollenomics.reporting.presentation.report_portal.scientific_accounts import (
    BEGIN,
    END,
    parse_routes,
)
from bijux_pollenomics.reporting.presentation.report_portal.scientific_qualifications import (
    FIELDS,
)
from bijux_pollenomics_dev.ci.report_rebuild.scientific_captures.author_grid.historical_reader import (
    FAMILY,
    historical_reader_scope,
)


def _own_reader(
    tmp_path: Path,
) -> tuple[Path, dict[str, Any], bytes, bytes, dict[str, Any]]:
    """Construct one miniature source authority and its literal historical footer."""
    raw = b"Own scoped result.\n"
    scope = "Current source-Python; not installed-distribution execution."
    account = {"report_path": "reports/science/own.md", "source_sha256": "1" * 64}
    pins = [
        {"path": "reports/science/own/result.json", "sha256": "2" * 64},
        {"path": "reports/science/own/source.md", "sha256": "3" * 64},
    ]
    digest = hashlib.sha256(raw).hexdigest()
    fields = {key: f"Own {key} assertion." for key, _ in FIELDS}
    route = {
        "reader_path": FAMILY + "REPORT.md",
        "canonical_accounts": [account],
        "scope_reason": scope,
        "qualification": {
            "authored_reader_sha256": digest,
            "fields": fields,
            "evidence_pins": pins,
        },
    }
    document = {"schema_version": 1, "routes": [route]}
    lines = ["## Scientific verification and limits", "", scope, ""]
    for key, label in FIELDS:
        lines.extend((f"**{label}.** {fields[key]}", ""))
    lines.extend((f"Qualified authored reader SHA-256: `{digest}`.", ""))
    base = "https://github.com/bijux/bijux-pollenomics/blob/main/"
    for pin in pins:
        lines.extend(
            (
                f"- [Retained qualification evidence: {pin['path']}]({base}{pin['path']}) "
                f"(SHA-256 `{pin['sha256']}`).",
                "",
            )
        )
    lines.extend(
        (
            f"- [Canonical scientific account: {account['report_path']}]"
            f"({base}{account['report_path']}) "
            f"(source SHA-256 `{account['source_sha256']}`).",
            "",
            "JSON and CSV retain their domain source and numerical manifests; "
            "a reading route does not rerun those producers. PDF exports retain "
            "their export inventory and source pins and must be regenerated "
            "when their canonical account changes.",
        )
    )
    published = raw + (BEGIN + "\n".join(lines) + "\n" + END).encode()
    members: dict[str, Any] = {}
    _write_authority(tmp_path, document, members)
    return tmp_path, members, raw, published, document


def _write_authority(
    root: Path, document: dict[str, Any], members: dict[str, Any]
) -> None:
    """Pin only a controlled miniature authority, without copying a retained packet."""
    path = root / "publication/scientific_accounts.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(document).encode()
    path.write_bytes(body)
    members["publication/scientific_accounts.json"] = {
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def test_historical_footer_keeps_raw_and_maintained_evidence_hashes(
    tmp_path: Path,
) -> None:
    root, members, raw, published, _ = _own_reader(tmp_path)
    assert historical_reader_scope(root, members, raw, published).startswith(
        "Current source-Python"
    )
    with pytest.raises(ValueError):
        parse_routes((root / "publication/scientific_accounts.json").read_text())


@pytest.mark.parametrize(
    "damage",
    [
        "authority_unpinned",
        "authored",
        "footer",
        "account_pin",
        "maintained_evidence_pin",
        "raw_evidence_pin",
        "unknown_qualification_field",
        "duplicate_route",
        "current_schema",
        "malformed_hash",
        "changed_field",
        "extra_footer_action",
        "duplicate_JSON_field",
    ],
)
def test_original_authority_and_footer_refuse_tampering(
    tmp_path: Path, damage: str
) -> None:
    root, members, raw, published, document = _own_reader(tmp_path)
    route = document["routes"][0]
    qualification = route["qualification"]
    if damage == "authority_unpinned":
        (root / "publication/scientific_accounts.json").write_bytes(b"not JSON")
    elif damage == "authored":
        raw += b"Changed source result.\n"
    elif damage == "footer":
        published = published.replace(b"Current source-Python", b"Installed Python")
    elif damage == "extra_footer_action":
        published += b"Unowned appended claim.\n"
    else:
        if damage == "account_pin":
            route["canonical_accounts"][0]["source_sha256"] = "4" * 64
        elif damage == "maintained_evidence_pin":
            qualification["evidence_pins"][1]["sha256"] = "4" * 64
        elif damage == "raw_evidence_pin":
            qualification["evidence_pins"][0]["sha256"] = "4" * 64
        elif damage == "unknown_qualification_field":
            qualification["extra"] = "unowned"
        elif damage == "duplicate_route":
            document["routes"].append(route)
        elif damage == "current_schema":
            document["schema_version"] = 2
        elif damage == "malformed_hash":
            route["canonical_accounts"][0]["source_sha256"] = "z" * 64
        elif damage == "changed_field":
            qualification["fields"][FIELDS[0][0]] = "Changed supported claim."
        _write_authority(root, document, members)
        if damage == "duplicate_JSON_field":
            path = root / "publication/scientific_accounts.json"
            body = path.read_bytes().replace(
                b'"schema_version": 1', b'"schema_version": 1, "schema_version": 1'
            )
            path.write_bytes(body)
            members["publication/scientific_accounts.json"] = {
                "bytes": len(body),
                "sha256": hashlib.sha256(body).hexdigest(),
            }
    with pytest.raises(ValueError):
        historical_reader_scope(root, members, raw, published)
