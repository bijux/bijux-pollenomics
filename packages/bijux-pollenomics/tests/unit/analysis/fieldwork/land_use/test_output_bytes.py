from __future__ import annotations

import hashlib
from pathlib import Path

from bijux_pollenomics.analysis.fieldwork.land_use import (
    render_sweden_land_use_synthesis_markdown,
    write_sweden_land_use_synthesis_csv,
    write_sweden_land_use_synthesis_json,
)

from .representative_payload import representative_payload


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_serialized_output_bytes_match_the_monolith_contract(tmp_path: Path) -> None:
    payload = representative_payload()
    json_path = tmp_path / "representative.json"
    csv_path = tmp_path / "representative.csv"
    markdown_path = tmp_path / "representative.md"

    write_sweden_land_use_synthesis_json(json_path, payload)
    write_sweden_land_use_synthesis_csv(csv_path, payload)
    markdown_path.write_text(
        render_sweden_land_use_synthesis_markdown(payload), encoding="utf-8"
    )

    assert (_digest(json_path), len(json_path.read_bytes())) == (
        "098e02c38c20a5f015a7f1ef52288c5062c9c10e879355fceeb467bb4b835201",
        2039,
    )
    assert (_digest(csv_path), len(csv_path.read_bytes())) == (
        "997f3b27b042ff37eb91209ada9d2631efc8f88f27ad1e8c1f113fc0a01413ff",
        419,
    )
    assert (_digest(markdown_path), len(markdown_path.read_bytes())) == (
        "dc79c828c65286ad3f91c4df2992c66372220b1b6336c23fd962e45e969ee8cd",
        1908,
    )
