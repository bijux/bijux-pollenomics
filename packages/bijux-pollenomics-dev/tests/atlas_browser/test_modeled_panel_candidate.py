"""Source-bound modeled panel candidate guards."""

from __future__ import annotations

import csv
import hashlib
import io
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.atlas_browser.modeled_panel_candidate import (
    generate_modeled_panel_candidate,
    panel_rows,
)


def test_panel_inventory_requires_exact_digest_and_key_topology() -> None:
    rows = [
        {"country": "Denmark", "source_window": "0-100 BP", "metric_key": metric}
        for metric in ("ET", "ST", "OL", "AL")
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=tuple(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    raw = output.getvalue().encode()
    with pytest.raises(ValueError, match="CSV digest mismatch"):
        panel_rows(raw, {"csv_sha256": "0" * 64, "row_count": 4})
    with pytest.raises(ValueError, match="row count mismatch"):
        panel_rows(raw, {"csv_sha256": hashlib.sha256(raw).hexdigest(), "row_count": 4})


def test_candidate_stays_within_owned_artifacts_and_never_overwrites(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="repository artifacts"):
        generate_modeled_panel_candidate(tmp_path, tmp_path / "outside")
    destination = tmp_path / "artifacts/candidate"
    destination.mkdir(parents=True)
    with pytest.raises(ValueError, match="destination must be absent"):
        generate_modeled_panel_candidate(tmp_path, destination)
