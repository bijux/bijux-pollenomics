"""Require a complete immutable provider capture before citation replay."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.taxa_review.neotoma_priority import _captured_responses


def test_publication_capture_requires_exact_candidate_closure(tmp_path: Path) -> None:
    attribution = b"candidate-attribution\n"
    member = tmp_path / "responses/dataset-17-publications.json"
    member.parent.mkdir()
    content = b'{"status":"success","data":[]}\n'
    member.write_bytes(content)
    row = {
        "dataset_id": 17,
        "path": "responses/dataset-17-publications.json",
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "http_status": 200,
    }
    manifest = {
        "schema_version": "neotoma-candidate-publication-capture.v1",
        "attribution_sha256": hashlib.sha256(attribution).hexdigest(),
        "response_count": 1,
        "responses": [row],
    }
    path = tmp_path / "capture-manifest.json"
    path.write_text(json.dumps(manifest))
    responses, _ = _captured_responses(tmp_path, attribution, {17})
    assert responses == {17: content}

    with pytest.raises(ValueError, match="cover all candidate datasets"):
        _captured_responses(tmp_path, attribution, {17, 18})
    row["path"] = "../dataset-17-publications.json"
    path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identity or path"):
        _captured_responses(tmp_path, attribution, {17})
