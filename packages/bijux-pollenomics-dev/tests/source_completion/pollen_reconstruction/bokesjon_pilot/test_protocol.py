"""The source audit cannot silently select another cohort or raw source."""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.workflow import (
    validate_protocol,
)


@pytest.fixture
def protocol() -> dict[str, Any]:
    repository = Path(__file__).resolve().parents[6]
    return cast(
        dict[str, Any],
        json.loads(
            (
                repository
                / "reports/science/pollen-reconstruction/bokesjon-pilot/protocol.json"
            ).read_text()
        ),
    )


def test_declared_source_panel(protocol: dict[str, Any]) -> None:
    validate_protocol(protocol)


@pytest.mark.parametrize(
    "mutation", ["window", "identity", "external_source", "private_source"]
)
def test_changed_claim_requires_a_distinct_explicit_protocol(
    protocol: dict[str, Any], mutation: str
) -> None:
    value = deepcopy(protocol)
    if mutation == "window":
        value["window_cal_bp"] = [0, 100]
    elif mutation == "identity":
        value["identities"]["KRAG"]["dataset_id"] = 54001
    elif mutation == "external_source":
        value["inputs"][0]["path"] = "/unrelated/data.json"
    else:
        value["optional_private_sources"]["workbook"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="protocol"):
        validate_protocol(value)
