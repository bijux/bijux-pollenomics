"""Reviewable fieldwork JSON and CSV writer tests."""

import csv
import json
from pathlib import Path
import tempfile

from bijux_pollenomics.analysis import (
    write_lake_fieldwork_preparation_csv,
    write_lake_fieldwork_preparation_json,
)

from .support import _report


def test_lake_fieldwork_preparation_writers_emit_reviewable_files() -> None:
    report = _report()
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        json_path = root / "sweden_lake_fieldwork_preparation_v66.json"
        csv_path = root / "sweden_lake_fieldwork_preparation_v66.csv"

        write_lake_fieldwork_preparation_json(json_path, report)
        write_lake_fieldwork_preparation_csv(csv_path, report)

        payload = json.loads(json_path.read_text(encoding="utf-8"))
        assert payload["row_count"] == 2

        with csv_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))

        assert rows[0]["fieldwork_rank"] == "1"
        assert float(rows[0]["fieldwork_shortlist_score"]) > 0.0
        assert rows[0]["lake_registry_id"] == "test-lake-clear"
        assert rows[0]["preparation_posture"] == "fieldwork_review_ready"
        assert rows[0]["human_context_posture"] == "core_human_adna_context"
        assert rows[0]["scenario_consistency_posture"] == "high"
        assert (
            "confirm the exact Swedish lake registry match before field planning"
            in rows[1]["required_actions"]
        )
