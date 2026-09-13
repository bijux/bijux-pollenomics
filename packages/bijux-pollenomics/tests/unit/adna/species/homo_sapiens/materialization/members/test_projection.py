"""Physical-row evidence conservation without inferred scientific admission."""

from __future__ import annotations

from pathlib import Path

from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.projection import (
    iter_member_documents,
)
from bijux_pollenomics.adna.species.homo_sapiens.materialization.members.validation import (
    validate_member_ownership,
)
from tests.unit.collection.sources.aadr.materialization.accountability.support import (
    reconciliation,
)


def test_projection_owns_every_original_token_once(tmp_path: Path) -> None:
    source = reconciliation(tmp_path)
    documents = list(iter_member_documents(source, release_manifest_sha256="a" * 64))
    counts = validate_member_ownership(documents, release_manifest_sha256="a" * 64)
    assert counts["source_row_count"] == 12
    assert counts["member_count"] == 7
    assert counts["unkeyed_source_row_count"] == 1
    actual: dict[str, list[str]] = {}
    for name, record in documents:
        if name == "source_rows.ndjson":
            link = record["source_row"]
            assert isinstance(link, dict)
            tokens = record["raw_tokens"]
            assert isinstance(tokens, list)
            assert all(isinstance(token, str) for token in tokens)
            actual[link["key"]] = tokens
        elif name in {"members.ndjson", "unkeyed_rows.ndjson"}:
            boundary = record["admission_boundary"]
            assert isinstance(boundary, dict)
            assert boundary["scientifically_admitted"] is False
            assert boundary["country_membership_asserted"] is False
    expected = {
        f"{table.source.key}:record:{row.source_record_number}": list(row.raw_tokens)
        for table in source.source_tables
        for row in table.rows
    }
    assert actual == expected
    assert any("-25.50" in tokens for tokens in actual.values())
    assert any("0.0" in tokens for tokens in actual.values())
    assert any("" in tokens for tokens in actual.values())
