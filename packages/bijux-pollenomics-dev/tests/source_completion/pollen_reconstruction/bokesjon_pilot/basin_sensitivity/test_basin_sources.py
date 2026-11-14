"""Modern alternative values need explicit primary fact locators, not labels alone."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any, cast

import pytest

from bijux_pollenomics_dev.source_completion.pollen_reconstruction.bokesjon_pilot.basin_sensitivity import (
    inputs,
    protocol,
)

CARD = Path("data/neotoma/raw/bokesjon-core-sources/basin-sources.json")


def source_card() -> dict[str, Any]:
    repository = next(
        p for p in Path(__file__).resolve().parents if (p / "uv.lock").is_file()
    )
    return cast(dict[str, Any], json.loads((repository / CARD).read_text()))


def parser() -> Any:
    function = getattr(protocol, "profiles_from_sources", None)
    assert callable(function), (
        "Basin profiles must be derived from the primary fact card"
    )
    return function


def test_profiles_consume_primary_values_and_exact_oup_locator() -> None:
    function = parser()
    values = function(source_card())
    assert [value.radius_m for value in values] == pytest.approx(
        [69.0988298942671, 71.36496464611085, 80]
    )
    assert "https://academic.oup.com/view-large/80999410" in values[1].source
    assert "Table I" in values[1].source


@pytest.mark.parametrize(
    "change", ["quantity", "source_fact", "source_locator", "profile_locator"]
)
def test_source_value_drift_or_lost_primary_locator_is_refused(change: str) -> None:
    function = parser()
    card = deepcopy(source_card())
    if change == "quantity":
        card["profiles"][1]["quantity"]["value"] = 0.017
    elif change == "source_fact":
        card["sources"]["oup_table_I"]["facts"]["area_km2"] = 0.017
    elif change == "source_locator":
        card["sources"]["oup_table_I"]["locator"] = ""
    else:
        del card["profiles"][1]["source_refs"][0]["locator"]
    with pytest.raises(ValueError):
        function(card)


def test_changed_fact_card_bytes_are_refused_by_actual_input_boundary(
    tmp_path: Path,
) -> None:
    function = getattr(inputs, "load_basin_sources", None)
    assert callable(function), "The fact card must be an authenticated input"
    repository = next(
        p for p in Path(__file__).resolve().parents if (p / "uv.lock").is_file()
    )
    copy = tmp_path / CARD
    copy.parent.mkdir(parents=True)
    copy.write_bytes((repository / CARD).read_bytes())
    raw, profiles, pin = function(tmp_path)
    assert len(profiles) == 3
    assert pin["sha256"] == hashlib.sha256(raw).hexdigest()
    assert pin["path"] == str(CARD)
    copy.write_bytes(raw + b" ")
    with pytest.raises(ValueError):
        function(tmp_path)
