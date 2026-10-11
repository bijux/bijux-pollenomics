"""Scientific refusal and source-integrity checks for the SEAD screen."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.source_completion.sead_pollen_screen import (
    _parts,
    _refusal_reasons,
)


def test_pollen_word_cannot_promote_an_otherwise_dated_source_row() -> None:
    row = {
        "event_refusal_reason_codes": [],
        "chronology_link": {"eligible_claim_count": 1},
        "source_semantics": {"source_unit_id": 5},
    }

    assert _refusal_reasons(row) == ["dataset_name_does_not_certify_pollen_proxy"]


def test_partition_reader_rejects_changed_source_bytes(tmp_path: Path) -> None:
    source = tmp_path / "observations.json"
    original = json.dumps({"observations": [{"observation_id": "one"}]}).encode()
    digest = hashlib.sha256(original).hexdigest()
    source.write_bytes(original + b" ")
    document = {
        "partitioned_fields": {
            "observations": {
                "row_count": 1,
                "parts": [{"path": source.name, "sha256": digest, "row_count": 1}],
            }
        }
    }

    with pytest.raises(ValueError, match="source digest differs"):
        list(
            _parts(
                tmp_path, {source.name: {"sha256": digest}}, document, "observations"
            )
        )
