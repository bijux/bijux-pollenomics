from __future__ import annotations

import json
from pathlib import Path

from bijux_pollenomics_dev.source_completion.intakes import (
    audit_intakes,
    find_hyde_candidates,
)


def test_observed_delivery_does_not_upgrade_historical_rights(tmp_path: Path) -> None:
    directory = tmp_path / "contracts/intake"
    directory.mkdir(parents=True)
    (tmp_path / "input.zip").write_bytes(b"received bytes")
    (directory / "receipt.json").write_text(
        json.dumps(
            {
                "intake_id": "external:1",
                "lifecycle_state": "quarantined",
                "delivery": {
                    "original_name": "input.zip",
                    "materialization_status": "unavailable",
                },
                "rights": {"status": "unknown"},
                "decision": {"public_release_allowed": False},
                "scientific_scope": {"status": "blocked"},
                "country_coverage": [],
            }
        )
    )
    result = audit_intakes(tmp_path)
    receipt = result["receipts"][0]
    assert receipt["observed_original_file"]["presence"] == "present"
    assert receipt["lifecycle_state"] == "quarantined"
    assert receipt["rights"]["status"] == "unknown"
    assert receipt["decision"]["public_release_allowed"] is False


def test_hyde_documentation_filename_is_not_release_evidence(tmp_path: Path) -> None:
    (tmp_path / "HYDE-35.md").write_text("Plan only")
    result = find_hyde_candidates([tmp_path])[0]
    assert result["filename_matches"] == ["HYDE-35.md"]
    assert result["confirmed_hyde_35_asset_count"] is None
