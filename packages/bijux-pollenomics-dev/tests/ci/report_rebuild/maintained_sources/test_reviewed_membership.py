"""Keep reviewed source admission aligned with independently owned report paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bijux_pollenomics_dev.ci.report_rebuild.contracts import canonical_json_sha256
from bijux_pollenomics_dev.ci.report_rebuild.maintained_sources import (
    MAINTAINED_ROLE_PATHS,
)

REPOSITORY = Path(__file__).resolve().parents[6]


@pytest.mark.parametrize("role", tuple(MAINTAINED_ROLE_PATHS))
def test_reviewed_membership_matches_current_ownership(role: str) -> None:
    owners = json.loads((REPOSITORY / "configs/ci/report-ownership.json").read_bytes())[
        "owners"
    ]
    paths = sorted(
        path for owner in owners if owner["role"] == role for path in owner["paths"]
    )
    count, digest = MAINTAINED_ROLE_PATHS[role]
    assert len(paths) == len(set(paths)) == count
    assert canonical_json_sha256(paths) == digest


@pytest.mark.parametrize(
    "name", ("transport-sensitivity.json", "regional-extent-sensitivity.json")
)
def test_nordic_transport_protocols_are_reviewed_configuration(name: str) -> None:
    path = (
        "docs/report/pollen-reconstruction/nordic-static-basin-scenarios/"
        "assumptions/" + name
    )
    owners = json.loads((REPOSITORY / "configs/ci/report-ownership.json").read_bytes())[
        "owners"
    ]
    matching = [owner for owner in owners if path in owner["paths"]]
    assert len(matching) == 1
    assert matching[0]["role"] == "maintained_configuration"
