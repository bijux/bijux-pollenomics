"""Behavioral checks for published-model landscape history."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pytest

from .support import means


def test_workflow_preserves_deterministic_source_bound_outputs(tmp_path: Path) -> None:
    from bijux_pollenomics.reporting.modeled_context import contracts, metric_families
    from bijux_pollenomics.reporting.modeled_context.metric_families import (
        PANGAEA_METRIC_KEYS,
    )
    from bijux_pollenomics_dev.landscape_history.landclim.inputs import (
        SOURCE,
        SOURCE_PATHS,
        WINDOWS,
    )
    from bijux_pollenomics_dev.landscape_history.landclim.workflow import run

    for name in SOURCE_PATHS:
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("synthetic-source-reference\n")
    features = []
    for younger, older in WINDOWS:
        for i in range(26):
            estimates = dict.fromkeys(PANGAEA_METRIC_KEYS, 0.0)
            estimates.update(means(Pinus=100))
            estimates["ET"] = estimates["IBE"] = 100
            x, y = 15 + i % 2, 55 + i // 2
            features.append(
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [[x, y], [x + 1, y], [x + 1, y + 1], [x, y + 1], [x, y]]
                        ],
                    },
                    "properties": {
                        "dataset_id": "937075",
                        "country": "Sweden",
                        "parent_grid_record_id": str(i),
                        "time_start_bp": younger,
                        "time_end_bp": older,
                        "time_label": f"{younger}-{older} BP",
                        "value_unit": "percentage_cover",
                        "quality_class": "high",
                        "reconstruction_values": estimates,
                        "standard_errors": dict.fromkeys(PANGAEA_METRIC_KEYS, 0.0),
                    },
                }
            )
    (tmp_path / SOURCE).write_text(
        json.dumps({"type": "FeatureCollection", "features": features})
    )
    out = tmp_path / "artifacts" / "first"
    run(tmp_path, out)
    second = tmp_path / "artifacts" / "second"
    run(tmp_path, second)
    a = json.loads((out / "trajectories.json").read_text())
    assert len(a["rows"]) == 25 * (4 + 5 + 6) * 3 * 2
    assert (out / "trajectories.json").read_bytes() == (
        second / "trajectories.json"
    ).read_bytes()
    assert (out / "cells.csv").read_bytes() == (second / "cells.csv").read_bytes()
    assert (out / "trajectories.csv").read_bytes() == (
        second / "trajectories.csv"
    ).read_bytes()
    with (out / "trajectories.csv").open(newline="") as handle:
        flat = list(csv.DictReader(handle))
    assert len(flat) == len(a["rows"])
    assert "tree_assigned_mean" in flat[0]
    assert "source_OL_mean" in flat[0]
    assert any(
        p["path"].endswith("modeled_context/contracts.py")
        for p in json.loads((out / "summary.json").read_text())[
            "calculation_source_pins"
        ]
    )
    summary = json.loads((out / "summary.json").read_text())
    pins = {item["path"]: item["sha256"] for item in summary["calculation_source_pins"]}
    for module in (contracts, metric_families):
        module_path = Path(module.__file__)
        label = f"packages/bijux-pollenomics/src/bijux_pollenomics/reporting/modeled_context/{module_path.name}"
        assert pins[label] == hashlib.sha256(module_path.read_bytes()).hexdigest()
    assert summary["cell_status_counts"] == {"eligible": 650}
    assert summary["input_pins"]
    assert summary["calculation_source_pins"]
    assert summary["protocol"]["regional_confidence_intervals"] is False
    with pytest.raises(ValueError, match="absent"):
        run(tmp_path, out)
    with pytest.raises(ValueError, match="artifacts"):
        run(tmp_path, tmp_path / "elsewhere")
