"""Execute only the frozen fixed-response two-taxon public API grid."""

from __future__ import annotations

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

import bijux_pollenomics_lra.api as api


def main() -> None:
    protocol_path, output_path, source_root = map(Path, sys.argv[1:])
    protocol: dict[str, Any] = json.loads(protocol_path.read_text())
    function = api.fixed_two_taxon_counting_interval
    module_path = Path(sys.modules[function.__module__].__file__ or "").resolve()
    if not module_path.is_relative_to(source_root.resolve()):
        raise ValueError("Numerical API imported outside frozen owned source")
    rows: list[dict[str, Any]] = []
    for scenario in protocol["fixed_responses"]:
        for total in protocol["counting_totals"]:
            for confidence in protocol["confidence_levels"]:
                for first in range(total + 1):
                    result = function(
                        [first, total - first],
                        scenario["deposition"],
                        scenario["ppe"],
                        taxon_measured=[True, True],
                        confidence_level=confidence,
                    )
                    rows.append({"scenario_id": scenario["id"], **asdict(result)})
    output_path.write_text(
        json.dumps(
            {
                "protocol_sha256": hashlib.sha256(
                    protocol_path.read_bytes()
                ).hexdigest(),
                "actual_api_path": str(module_path),
                "actual_api_sha256": hashlib.sha256(
                    module_path.read_bytes()
                ).hexdigest(),
                "rows": rows,
                "scope": protocol["scope"],
                "scientific_admission": False,
            },
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
