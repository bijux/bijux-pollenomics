"""Semantic and byte-identity tests for request derivation."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.provenance.request import derive_release_evidence_request

from tests.unit.provenance.release_evidence_writer.support import _inputs


def _canonical_request_bytes(request: dict[str, object]) -> bytes:
    return (
        json.dumps(
            request,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )


def test_canonical_request_bytes_are_deterministic(tmp_path: Path) -> None:
    _inputs(tmp_path)

    first = _canonical_request_bytes(derive_release_evidence_request(tmp_path))
    second = _canonical_request_bytes(derive_release_evidence_request(tmp_path))

    assert len(first) == 8170
    assert first == second


def test_unavailable_country_source_never_becomes_zero(tmp_path: Path) -> None:
    _inputs(tmp_path)

    request = derive_release_evidence_request(tmp_path)
    reconciliations = cast(list[dict[str, object]], request["reconciliations"])
    source = next(
        row for row in reconciliations if row["identity"] == "neotoma.samples.source"
    )

    assert source["count_status"] == "unavailable"
    assert source["candidate_count"] is None
    assert source["accepted_count"] is None
    assert source["reason_codes"] == ["fixture_count_not_materialized"]
