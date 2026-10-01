from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.refresh_review import (
    build_neotoma_refresh_review,
)


def test_tracked_refresh_review_binds_current_baseline() -> None:
    repository = Path(__file__).resolve().parents[7]
    review_root = repository / "data/neotoma/review"
    baseline = json.loads((review_root / "relational_baseline.json").read_text())
    retained = json.loads((review_root / "relational_refresh_review.json").read_text())

    assert retained == build_neotoma_refresh_review(baseline, baseline)
