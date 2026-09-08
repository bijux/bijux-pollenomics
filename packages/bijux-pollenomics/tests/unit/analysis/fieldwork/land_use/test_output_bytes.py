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

    markdown = markdown_path.read_text(encoding="utf-8")
    assert (
        "| Finjasjön | 0-1000 BP | no_pollen_data | N/A | N/A | N/A | N/A | N/A |"
        in markdown
    )
    assert "None" not in markdown

    assert (_digest(json_path), len(json_path.read_bytes())) == (
        "44650463a8811a4915dd57de70f0af21d61f8dd7de9383907bad8cd66004200c",
        2106,
    )
    assert (_digest(csv_path), len(csv_path.read_bytes())) == (
        "22313c20ac2263820e71fe4bd54e791f2f58ff23371623dde418fc6832282e59",
        428,
    )
    assert (_digest(markdown_path), len(markdown_path.read_bytes())) == (
        "5b7fa53969478ba2523090962343f027a999274513b8f94fc318426ff5674b3a",
        1919,
    )
