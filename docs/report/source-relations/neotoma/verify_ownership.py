"""Replay source relationship validation using the production materialization reader."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

from bijux_pollenomics.evidence.sources.neotoma.validation import (
    validate_neotoma_relational_materialization,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    arguments = parser.parse_args()
    root = arguments.source_root.resolve()
    manifest = validate_neotoma_relational_materialization(root)
    print(
        json.dumps(
            {
                "schema_version": "neotoma-relational-ownership-consumer.v1",
                "source_snapshot_id": manifest["source_snapshot_id"],
                "build_id": manifest["build_id"],
                "manifest_sha256": hashlib.sha256(
                    (root / "manifest.json").read_bytes()
                ).hexdigest(),
                "materialization_sha256": manifest["materialization_sha256"],
                "surfaces": {
                    name: surface["row_count"]
                    for name, surface in cast(
                        dict[str, dict[str, object]], manifest["surfaces"]
                    ).items()
                },
                "status": "passed",
                "validation": (
                    "Manifested parts, row counts, stable IDs, country partitions "
                    "and parent/ancestry ownership verified through the production "
                    "reader; null chronology references remain allowed, no scientific "
                    "admission upgrade."
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
