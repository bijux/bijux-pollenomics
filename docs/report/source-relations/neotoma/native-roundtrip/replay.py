"""Replay the pinned Neotoma native hierarchy reconciliation."""

from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics.collection.sources.neotoma.roundtrip import (
    audit_neotoma_roundtrip,
)


def main() -> None:
    root = Path(__file__).resolve().parents[5]
    report = audit_neotoma_roundtrip(
        root / "data/neotoma/raw/neotoma_pollen_dataset_downloads",
        root / "data/neotoma/relational",
    )
    print(json.dumps(report, sort_keys=True, indent=2))
    if report["status"] != "complete":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
