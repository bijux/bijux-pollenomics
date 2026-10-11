"""Check the lake-context screen's source roles and reproducibility."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from bijux_pollenomics_dev.source_completion.bjaresjo_context import produce

ROOT = Path(__file__).resolve().parents[4]
RESULT = ROOT / "reports/science/bjaresjo-context"


def test_official_lake_screen_retains_refused_core_and_sead_roles(
    tmp_path: Path,
) -> None:
    produce(ROOT, tmp_path / "replay")
    for name in ("report.json", "nearby-sead.csv", "window-overlap.csv"):
        assert (tmp_path / "replay" / name).read_bytes() == (RESULT / name).read_bytes()
    report = json.loads((RESULT / "report.json").read_text())
    assert report["lake"]["official_registry_id"] == "614958-137018"
    assert report["lake"]["core_identity_decision"] == "not_established"
    assert report["lake"]["radius_transfer"] == "refused"
    assert report["sead"]["nearby_interval_features"] == 371
    assert report["sead"]["nearby_sites"] == 13
    assert report["sead"]["ecological_or_event_join"] == "refused"
    with (RESULT / "nearby-sead.csv").open(newline="", encoding="utf-8") as stream:
        records = list(csv.DictReader(stream))
    assert len(records) == 371
    assert len({row["source_record_id"] for row in records}) == 371
    assert all(row["chronology_role"] == "display_only" for row in records)
    with (RESULT / "window-overlap.csv").open(newline="", encoding="utf-8") as stream:
        windows = list(csv.DictReader(stream))
    assert len(windows) == 25
    assert (
        next(row for row in windows if row["time_start_bp"] == "0")[
            "display_interval_features_within_20km"
        ]
        == "0"
    )
